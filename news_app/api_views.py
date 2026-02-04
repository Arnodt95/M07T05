from django.db.models import Q
from django.shortcuts import get_object_or_404

from rest_framework.decorators import (api_view, permission_classes,
                                       authentication_classes)
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.decorators import parser_classes
from .models import Article, Publisher, Newsletter
from .serializers import (ArticleSerializer, PublisherSerializer,
                          NewsletterSerializer)


def _is_reader(user):
    """
    Role check helper function for API endpoints.
    """
    return getattr(user, "role", "") == "reader"


def _is_editor(user):
    """
    Role check helper function for API endpoints.
    """
    return getattr(user, "role", "") == "editor"


def _is_journalist(user):
    """
    Role check helper function for API endpoints.
    """
    return getattr(user, "role", "") == "journalist"


# Articles


@api_view(["GET", "POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def api_articles(request):
    """
    GET /api/articles/
      - Returns all approved articles.

    POST /api/articles/
      - Creates an article (journalists only).
      - Supports image upload (multipart/form-data).
    """
    if request.method == "GET":
        qs = Article.objects.filter(
            approved=True).select_related(
                "author", "publisher").order_by("-created_at")

        return Response(
            ArticleSerializer(qs, many=True,
                              context={"request": request}).data)

    if not _is_journalist(request.user):
        return Response({"error": "Journalists only."},
                        status=status.HTTP_403_FORBIDDEN)

    serializer = ArticleSerializer(data=request.data,
                                   context={"request": request})
    if serializer.is_valid():
        article = serializer.save(author=request.user, approved=False)
        return Response(ArticleSerializer(article,
                                          context={"request": request}).data,
                        status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def api_articles_subscribed(request):
    """
    GET /api/articles/subscribed/
      - Returns approved articles from the reader's subscriptions.
      - Readers only.
    """
    if not _is_reader(request.user):
        return Response({"error": "Readers only."},
                        status=status.HTTP_403_FORBIDDEN)

    pubs = request.user.subscribed_publishers.all()
    journos = request.user.subscribed_journalists.all()

    qs = Article.objects.filter(approved=True).select_related(
        "author", "publisher").filter(
        Q(publisher__in=pubs) | Q(author__in=journos)
    ).order_by("-created_at")

    return Response(ArticleSerializer(qs, many=True).data)


@api_view(["GET", "PUT", "DELETE"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def api_article_detail(request, article_id: int):
    """
    GET /api/articles/<id>/
      - Retrieve a single article.
      - Readers can only retrieve approved articles.

    PUT /api/articles/<id>/
      - Update article (editors/journalists).
      - Journalists can only edit their own articles.
      - Only editors can set approved=True (signals will notify).

    DELETE /api/articles/<id>/
      - Delete article (editors/journalists).
      - Journalists can only delete their own articles.
    """

    article = get_object_or_404(Article.objects.select_related(
        "author", "publisher"), id=article_id)

    if request.method == "GET":
        if _is_reader(request.user) and not article.approved:
            return Response({"error": "Not allowed."},
                            status=status.HTTP_403_FORBIDDEN)
        return Response(ArticleSerializer(
            article, context={"request": request}).data)

    if request.method == "PUT":
        if not (_is_editor(request.user) or _is_journalist(request.user)):
            return Response({"error": "Editors/journalists only."},
                            status=status.HTTP_403_FORBIDDEN)

        if _is_journalist(
             request.user) and article.author_id != request.user.id:
            return Response({"error": "Not allowed."},
                            status=status.HTTP_403_FORBIDDEN)

        wants_approve = str(request.data.get(
            "approved", "")).lower() in ("true", "1", "yes")

        serializer = ArticleSerializer(article, data=request.data,
                                       partial=True, context={
                                           "request": request})
        if serializer.is_valid():
            updated = serializer.save()

            if "approved" in request.data and wants_approve:
                if not _is_editor(request.user):
                    updated.approved = False
                    updated.save()
                    return Response({"error": "Only editors can approve."},
                                    status=status.HTTP_403_FORBIDDEN)
                updated.approved = True
                updated.save()

            if _is_journalist(request.user) and not _is_editor(request.user):
                updated.approved = False
                updated.save()

            return Response(ArticleSerializer(updated,
                                              context={
                                                  "request": request}).data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    article.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


# Publishers

@api_view(["GET"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def api_publishers(request):
    """
    GET /api/publishers/
      - Return a list of publishers.
      - Any authenticated role can view.
    """
    qs = Publisher.objects.all().order_by("name")
    return Response(PublisherSerializer(qs, many=True).data)


@api_view(["GET"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def api_publisher_detail(request, publisher_id: int):
    """
    GET /api/publishers/<id>/
      - Retrieve a single publisher.
      - Any authenticated role can view.
    """
    publisher = get_object_or_404(Publisher, id=publisher_id)
    return Response(PublisherSerializer(publisher).data)


# Newsletters

def _newsletter_payload(newsletter: Newsletter, is_reader_role: bool):
    """
    Helper to serialize a newsletter.

    Readers should only see approved articles in newsletters.
    Editors/journalists can see all linked articles.
    """
    data = NewsletterSerializer(newsletter).data
    if is_reader_role:
        data["articles"] = [a for a in data.get(
            "articles", []) if a.get("approved") is True]
    return data


@api_view(["GET", "POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def api_newsletters(request):
    """
    GET /api/newsletters/
      - Return newsletters.
      - Readers see newsletters with only approved nested articles.

    POST /api/newsletters/
      - Create newsletter (journalists only).
    """
    if request.method == "GET":
        qs = Newsletter.objects.select_related(
            "author").prefetch_related("articles").order_by("-created_at")
        if _is_reader(request.user):

            qs = qs.filter(articles__approved=True).distinct()
        return Response([_newsletter_payload(
            n, _is_reader(request.user)) for n in qs])

    if not _is_journalist(request.user):
        return Response({"error": "Journalists only."},
                        status=status.HTTP_403_FORBIDDEN)

    serializer = NewsletterSerializer(data=request.data)
    if serializer.is_valid():
        newsletter = serializer.save(author=request.user)

        serializer.save()
        return Response(_newsletter_payload(newsletter, False),
                        status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET", "PUT", "DELETE"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def api_newsletter_detail(request, newsletter_id: int):
    """
    GET /api/newsletters/<id>/
      - Retrieve a newsletter.
      - Readers see only approved articles nested.

    PUT /api/newsletters/<id>/
      - Update newsletter (editors/journalists).
      - Journalists can only update their own newsletters.

    DELETE /api/newsletters/<id>/
      - Delete newsletter (editors/journalists).
      - Journalists can only delete their own newsletters.
    """
    newsletter = get_object_or_404(
        Newsletter.objects.select_related(
            "author").prefetch_related("articles"),
        id=newsletter_id,
    )

    if request.method == "GET":
        if _is_reader(
            request.user) and not newsletter.articles.filter(
                approved=True).exists():
            return Response(
                {"error": "No approved articles in this newsletter."},
                status=status.HTTP_404_NOT_FOUND)
        return Response(_newsletter_payload(
            newsletter, _is_reader(request.user)))

    if request.method == "PUT":
        if not (_is_editor(request.user) or _is_journalist(request.user)):
            return Response({"error": "Editors/journalists only."},
                            status=status.HTTP_403_FORBIDDEN)

        if _is_journalist(
             request.user) and newsletter.author_id != request.user.id:
            return Response({"error": "Not allowed."},
                            status=status.HTTP_403_FORBIDDEN)

        serializer = NewsletterSerializer(
            newsletter, data=request.data, partial=True)
        if serializer.is_valid():
            updated = serializer.save()
            return Response(_newsletter_payload(
                updated, _is_reader(request.user)))
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    if not (_is_editor(request.user) or _is_journalist(request.user)):
        return Response({"error": "Editors/journalists only."},
                        status=status.HTTP_403_FORBIDDEN)

    if _is_journalist(
         request.user) and newsletter.author_id != request.user.id:
        return Response({"error": "Not allowed."},
                        status=status.HTTP_403_FORBIDDEN)

    newsletter.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)
