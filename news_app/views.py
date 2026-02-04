from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render

from .forms import (LoginForm, RegisterForm, ArticleForm, NewsletterForm,
                    SubscriptionForm)
from .models import Article, Newsletter, Publisher

User = get_user_model()

READERS = "Readers"
EDITORS = "Editors"
JOURNALISTS = "Journalists"


def home(request):
    """
    View to display the public home page.
    """
    return render(request, "news_app/home.html")


def ensure_groups_and_permissions():
    """
    Ensure that the Readers, Editors, and Journalists groups exist and have
    the correct permissions assigned.

    Permissions:
    - Reader: view Article/Newsletter/Publisher
    - Editor: view/change/delete Article & Newsletter + view Publisher
    - Journalist: add/view/change/delete Article & Newsletter + view Publisher
    """
    readers, _ = Group.objects.get_or_create(name=READERS)
    editors, _ = Group.objects.get_or_create(name=EDITORS)
    journalists, _ = Group.objects.get_or_create(name=JOURNALISTS)

    article_ct = ContentType.objects.get_for_model(Article)
    newsletter_ct = ContentType.objects.get_for_model(Newsletter)
    publisher_ct = ContentType.objects.get_for_model(Publisher)

    reader_perms = Permission.objects.filter(
        content_type__in=[article_ct, newsletter_ct, publisher_ct],
        codename__in=["view_article", "view_newsletter", "view_publisher"],
    )

    editor_perms = Permission.objects.filter(
        content_type__in=[article_ct, newsletter_ct, publisher_ct],
        codename__in=[
            "view_article", "change_article", "delete_article",
            "view_newsletter", "change_newsletter", "delete_newsletter",
            "view_publisher",
        ],
    )

    journalist_perms = Permission.objects.filter(
        content_type__in=[article_ct, newsletter_ct, publisher_ct],
        codename__in=[
            "add_article", "view_article", "change_article", "delete_article",
            "add_newsletter", "view_newsletter", "change_newsletter",
            "delete_newsletter", "view_publisher",
        ],
    )

    readers.permissions.set(reader_perms)
    editors.permissions.set(editor_perms)
    journalists.permissions.set(journalist_perms)

    return readers, editors, journalists


def is_reader(user):
    """
    Helper function to check if the user is in Readers group.
    """
    return user.is_authenticated and user.groups.filter(name=READERS).exists()


def is_editor(user):
    """
    Helper function to check if the user is in Editors group.
    """
    return user.is_authenticated and user.groups.filter(name=EDITORS).exists()


def is_journalist(user):
    """
    Helper function to check if the user is in Journalists group.
    """
    return user.is_authenticated and user.groups.filter(
        name=JOURNALISTS).exists()


def register_user(request):
    """
    Register a new user and assign them to a group
    based on their selected role.
    """
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data["username"]
            email = form.cleaned_data["email"]
            password = form.cleaned_data["password"]
            role = form.cleaned_data["role"]

            if User.objects.filter(username=username).exists():
                return render(request, "news_app/register.html",
                              {"form": form,
                               "error": "Username already exists."})

            user = User.objects.create_user(username=username,
                                            password=password, email=email)
            user.role = role
            user.save()

            readers, editors, journalists = ensure_groups_and_permissions()
            if role == "reader":
                user.groups.add(readers)
            elif role == "editor":
                user.groups.add(editors)
            else:
                user.groups.add(journalists)

            login(request, user)
            messages.success(request, "Registered and logged in successfully.")
            return redirect("article_list")
    else:
        form = RegisterForm()

    return render(request, "news_app/register.html", {"form": form})


def login_user(request):
    """
    Authenticate and log the user in.
    """
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            user = authenticate(request,
                                username=form.cleaned_data["username"],
                                password=form.cleaned_data["password"])
            if user is not None:
                login(request, user)
                messages.success(request, "Logged in successfully.")
                return redirect("article_list")
            return render(request, "news_app/login.html",
                          {"form": form, "error": "Invalid credentials."})
    else:
        form = LoginForm()

    return render(request, "news_app/login.html", {"form": form})


def logout_user(request):
    """
    Log out the current user.
    """
    logout(request)
    messages.info(request, "Logged out.")
    return redirect("login")


@login_required
def article_list(request):
    """
    List articles.
    - Readers see only approved articles.
    - Editors and journalists can see all.
    """

    qs = Article.objects.select_related(
        "author", "publisher").order_by("-created_at")
    if is_reader(request.user):
        qs = qs.filter(approved=True)

    featured = qs.first()
    articles = qs[1:13] if featured else qs[:12]

    return render(request, "news_app/article_list.html",
                  {"featured": featured, "articles": articles})


@login_required
def article_detail(request, article_id):
    """
    Article detail view.
    Readers can only access approved articles.
    """
    article = get_object_or_404(Article.objects.select_related
                                ("author", "publisher"), id=article_id)
    if is_reader(request.user) and not article.approved:
        return HttpResponseForbidden("Readers can only view "
                                     "approved articles.")
    return render(request, "news_app/article_detail.html",
                  {"article": article})


@login_required
def article_create(request):
    """
    Journalists can create new articles.
    New submissions start as approved=False and await editor review.
    """
    if not is_journalist(request.user):
        return HttpResponseForbidden("Journalists only.")

    if request.method == "POST":
        form = ArticleForm(request.POST)
        if form.is_valid():
            article = form.save(commit=False)
            article.author = request.user
            article.approved = False
            article.save()
            messages.success(request, "Article submitted for review.")
            return redirect("article_detail", article_id=article.id)
    else:
        form = ArticleForm()

    return render(request, "news_app/article_form.html",
                  {"form": form, "title": "Create Article"})


@login_required
def article_edit(request, article_id):
    """
    Edit an article.
    - Editors can edit any article.
    - Journalists can edit only their own articles.
    - Journalist edits reset approval to False.
    """
    article = get_object_or_404(Article, id=article_id)

    if is_journalist(request.user) and article.author_id != request.user.id:
        return HttpResponseForbidden("Not allowed.")
    if not (is_journalist(request.user) or is_editor(request.user)):
        return HttpResponseForbidden("Not allowed.")

    if request.method == "POST":
        form = ArticleForm(request.POST, instance=article)
        if form.is_valid():
            updated = form.save(commit=False)
            if is_journalist(request.user) and not is_editor(request.user):
                updated.approved = False
            updated.save()
            messages.success(request, "Article updated.")
            return redirect("article_detail", article_id=article.id)
    else:
        form = ArticleForm(instance=article)

    return render(request, "news_app/article_form.html",
                  {"form": form, "title": "Edit Article"})


@login_required
def article_delete(request, article_id):
    """
    Delete an article.
    - Editors can delete any article.
    - Journalists can delete their own articles.
    """
    article = get_object_or_404(Article, id=article_id)

    if not (is_editor(request.user) or
            (is_journalist(request.user)
             and article.author_id == request.user.id)):
        return HttpResponseForbidden("Not allowed.")

    if request.method == "POST":
        article.delete()
        messages.info(request, "Article deleted.")
        return redirect("article_list")

    return render(request, "news_app/article_form.html",
                  {"form": None, "title":
                   f"Delete {article.title}", "delete": True})


@login_required
def editor_queue(request):
    """
    Queue of pending articles for editors to review.
    """
    if not is_editor(request.user):
        return HttpResponseForbidden("Editors only.")

    pending = Article.objects.filter(approved=False).select_related(
        "author", "publisher").order_by("-created_at")
    return render(request, "news_app/editor_queue.html", {"articles": pending})


@login_required
def approve_article(request, article_id):
    """
    Approve an article.
    Signals will notify subscribers and post to X upon approval.
    """
    if not is_editor(request.user):
        return HttpResponseForbidden("Editors only.")

    article = get_object_or_404(Article, id=article_id)
    if not article.approved:
        article.approved = True
        article.save()

    messages.success(request, "Article approved and published.")
    return redirect("editor_queue")


@login_required
def newsletter_list(request):
    """
    List all newsletters.
    """
    qs = Newsletter.objects.select_related("author").order_by("-created_at")
    return render(request, "news_app/newsletter_list.html",
                  {"newsletters": qs})


@login_required
def newsletter_detail(request, newsletter_id):
    """
    Newsletter detail view.
    """
    newsletter = get_object_or_404(
        Newsletter.objects.select_related("author").prefetch_related(
            "articles"),
        id=newsletter_id,
    )
    return render(request, "news_app/newsletter_detail.html",
                  {"newsletter": newsletter})


@login_required
def newsletter_create(request):
    """
    Journalists can create newsletters.
    """
    if not is_journalist(request.user):
        return HttpResponseForbidden("Journalists only.")

    if request.method == "POST":
        form = NewsletterForm(request.POST)
        if form.is_valid():
            newsletter = form.save(commit=False)
            newsletter.author = request.user
            newsletter.save()
            form.save_m2m()
            messages.success(request, "Newsletter created.")
            return redirect("newsletter_detail", newsletter_id=newsletter.id)
    else:
        form = NewsletterForm()

    return render(request, "news_app/newsletter_form.html",
                  {"form": form, "title": "Create Newsletter"})


@login_required
def newsletter_edit(request, newsletter_id):
    """
    Edit a newsletter.
    - Editors can edit any newsletter.
    - Journalists can edit only their own newsletters.
    """
    newsletter = get_object_or_404(Newsletter, id=newsletter_id)

    if is_journalist(request.user) and newsletter.author_id != request.user.id:
        return HttpResponseForbidden("Not allowed.")
    if not (is_journalist(request.user) or is_editor(request.user)):
        return HttpResponseForbidden("Not allowed.")

    if request.method == "POST":
        form = NewsletterForm(request.POST, instance=newsletter)
        if form.is_valid():
            form.save()
            messages.success(request, "Newsletter updated.")
            return redirect("newsletter_detail", newsletter_id=newsletter.id)
    else:
        form = NewsletterForm(instance=newsletter)

    return render(request, "news_app/newsletter_form.html",
                  {"form": form, "title": "Edit Newsletter"})


@login_required
def subscriptions(request):
    """
    Reader subscription management view.
    """
    if not is_reader(request.user):
        return HttpResponseForbidden("Readers only.")

    if request.method == "POST":
        form = SubscriptionForm(request.POST)
        if form.is_valid():
            request.user.subscribed_publishers.set(form.cleaned_data[
                "publishers"])
            request.user.subscribed_journalists.set(form.cleaned_data[
                "journalists"])
            messages.success(request, "Subscriptions updated.")
            return redirect("subscriptions")
    else:
        form = SubscriptionForm(initial={
            "publishers": request.user.subscribed_publishers.all(),
            "journalists": request.user.subscribed_journalists.all(),
        })

    return render(request, "news_app/subscriptions.html", {"form": form})
