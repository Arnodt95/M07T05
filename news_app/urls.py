from django.urls import path
from . import views

urlpatterns = [
    path("register/", views.register_user, name="register"),
    path("login/", views.login_user, name="login"),
    path("logout/", views.logout_user, name="logout"),

    path("articles/", views.article_list, name="article_list"),
    path("articles/<int:article_id>/", views.article_detail,
         name="article_detail"),
    path("journalist/articles/new/", views.article_create,
         name="article_create"),
    path("articles/<int:article_id>/edit/", views.article_edit,
         name="article_edit"),
    path("articles/<int:article_id>/delete/", views.article_delete,
         name="article_delete"),

    path("editor/queue/", views.editor_queue, name="editor_queue"),
    path("editor/approve/<int:article_id>/", views.approve_article,
         name="approve_article"),

    path("newsletters/", views.newsletter_list, name="newsletter_list"),
    path("newsletters/<int:newsletter_id>/", views.newsletter_detail,
         name="newsletter_detail"),
    path("journalist/newsletters/new/", views.newsletter_create,
         name="newsletter_create"),
    path("newsletters/<int:newsletter_id>/edit/", views.newsletter_edit,
         name="newsletter_edit"),

    path("subscriptions/", views.subscriptions, name="subscriptions"),
]
