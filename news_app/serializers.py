from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Publisher, Article, Newsletter

User = get_user_model()


class UserPublicSerializer(serializers.ModelSerializer):
    """
    Public serializer for user info in API responses.
    """
    class Meta:
        model = User
        fields = ["id", "username", "role"]


class PublisherSerializer(serializers.ModelSerializer):
    """
    Publisher serializer.
    """
    class Meta:
        model = Publisher
        fields = ["id", "name", "description", "created_at"]


class ArticleSerializer(serializers.ModelSerializer):
    """
    Article serializer.
    """
    author = UserPublicSerializer(read_only=True)
    publisher = PublisherSerializer(read_only=True)

    publisher_id = serializers.PrimaryKeyRelatedField(
        source="publisher",
        queryset=Publisher.objects.all(),
        allow_null=True,
        required=False,
        write_only=True,
    )

    image = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = Article
        fields = [
            "id", "title", "content",
            "author", "publisher", "publisher_id",
            "image",
            "created_at", "approved",
        ]


class NewsletterSerializer(serializers.ModelSerializer):
    """
    Newsletter serializer.

    Note: articles are nested for readability.
    """
    author = UserPublicSerializer(read_only=True)
    articles = ArticleSerializer(many=True, read_only=True)

    article_ids = serializers.PrimaryKeyRelatedField(
        source="articles",
        queryset=Article.objects.all(),
        many=True,
        required=False,
        write_only=True,
    )

    class Meta:
        model = Newsletter
        fields = ["id", "title", "description", "created_at", "author",
                  "articles", "article_ids"]
