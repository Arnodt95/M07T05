from django.db import models
from django.utils import timezone
from django.contrib.auth.models import AbstractUser


class CustomUser(AbstractUser):
    """
    Custom user with role-based behavior and subscription fields.

    Roles (required):
    - Reader: can view articles/newsletters and subscribe to
              publishers/journalists.
    - Editor: can review/approve and manage content.
    - Journalist: can create and manage articles/newsletters.

    Reader subscriptions:
    - subscribed_publishers: Many to many of Publisher subscriptions.
    - subscribed_journalists: Many to many to journalists (users).
    """
    ROLE_READER = "reader"
    ROLE_EDITOR = "editor"
    ROLE_JOURNALIST = "journalist"

    ROLE_CHOICES = (
        (ROLE_READER, "Reader"),
        (ROLE_EDITOR, "Editor"),
        (ROLE_JOURNALIST, "Journalist"),
    )

    role = models.CharField(max_length=20, choices=ROLE_CHOICES,
                            default=ROLE_READER)

    subscribed_publishers = models.ManyToManyField(
        "Publisher",
        blank=True,
        related_name="subscribers",
    )

    subscribed_journalists = models.ManyToManyField(
        "self",
        blank=True,
        symmetrical=False,
        related_name="subscribed_by_readers",
    )

    def __str__(self):
        return f"{self.username} ({self.role})"


class Publisher(models.Model):
    """
    Publisher model.

    A publisher can have multiple editors and journalists.
    """
    name = models.CharField(max_length=150, unique=True)
    description = models.TextField(blank=True)

    editors = models.ManyToManyField(
        CustomUser,
        blank=True,
        related_name="publisher_editor_roles",
        limit_choices_to={"role": CustomUser.ROLE_EDITOR},
    )

    journalists = models.ManyToManyField(
        CustomUser,
        blank=True,
        related_name="publisher_journalist_roles",
        limit_choices_to={"role": CustomUser.ROLE_JOURNALIST},
    )

    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.name


class Article(models.Model):
    """
    Article model representing a news article submission.

    Required fields:
    - title, content, author, created_at, approved, publisher.

    Association rule:
    - Every article is authored by a journalist.
    - publisher is optional:
      * publisher is null => independent article
      * publisher set => publisher content
    """
    title = models.CharField(max_length=200)
    content = models.TextField()

    author = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="articles",
        limit_choices_to={"role": CustomUser.ROLE_JOURNALIST},
    )

    publisher = models.ForeignKey(
        Publisher,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="articles",
    )

    image = models.ImageField(upload_to="article_images/",
                              blank=True, null=True)

    created_at = models.DateTimeField(default=timezone.now)
    approved = models.BooleanField(default=False)

    @property
    def is_independent(self) -> bool:
        return self.publisher_id is None

    def __str__(self):
        scope = self.publisher.name if self.publisher else "Independent"
        return f"{self.title} ({scope})"


class Newsletter(models.Model):
    """
    Newsletter model: curated collection of articles, created by journalists.

    Required fields:
    - title, description, created_at, author
    - many-to-many to Article
    """
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    author = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="newsletters",
        limit_choices_to={"role": CustomUser.ROLE_JOURNALIST},
    )

    articles = models.ManyToManyField(Article, blank=True,
                                      related_name="newsletters")

    def __str__(self):
        return f"{self.title} by {self.author.username}"
