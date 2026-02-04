from django.urls import path
from rest_framework.authtoken.views import obtain_auth_token
from . import api_views

urlpatterns = [
    # Token auth endpoint
    path("login/", obtain_auth_token, name="api_login"),

    # Articles
    path("articles/", api_views.api_articles, name="api_articles"),
    path("articles/subscribed/", api_views.api_articles_subscribed,
         name="api_articles_subscribed"),
    path("articles/<int:article_id>/", api_views.api_article_detail,
         name="api_article_detail"),

    # Publishers
    path("publishers/", api_views.api_publishers, name="api_publishers"),
    path("publishers/<int:publisher_id>/", api_views.api_publisher_detail,
         name="api_publisher_detail"),

    # Newsletters
    path("newsletters/", api_views.api_newsletters, name="api_newsletters"),
    path("newsletters/<int:newsletter_id>/", api_views.api_newsletter_detail,
         name="api_newsletter_detail"),
]
