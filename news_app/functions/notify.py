from django.conf import settings
from django.core.mail import EmailMessage
from django.urls import reverse

from ..models import CustomUser, Article
from .x_post import post_to_x


def build_excerpt(text: str, limit: int = 240) -> str:
    """
    Build an excerpt for article notifications.

    Default length is 240 characters.
    """
    cleaned = (text or "").strip()
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[:limit].rsplit(" ", 1)[0] + "..."


def _subscriber_emails(article: Article) -> set[str]:
    """
    Collect subscriber emails for a newly approved article.

    Subscribers include:
    - readers subscribed to the journalist
    - readers subscribed to the publisher (if publisher article)
    """
    emails = set()

    for reader in CustomUser.objects.filter(subscribed_journalists=article.author).distinct():
        if reader.email:
            emails.add(reader.email)

    if article.publisher_id:
        for reader in CustomUser.objects.filter(subscribed_publishers=article.publisher).distinct():
            if reader.email:
                emails.add(reader.email)

    return emails


def article_absolute_url(article: Article) -> str:
    """
    Build absolute article detail link for emails/social posts.
    Signals do not have access to request.build_absolute_uri,
    so we use settings.SITE_BASE_URL.
    """
    path = reverse("article_detail", kwargs={"article_id": article.id})
    return f"{settings.SITE_BASE_URL}{path}"


def notify_on_approval(article: Article) -> None:
    """
    Notify subscribers when an article is approved:
    - send email with excerpt + link
    - post update to X (optional)
    """
    link = article_absolute_url(article)
    excerpt = build_excerpt(article.content, limit=240)
    scope = article.publisher.name if article.publisher else "Independent"

    subject = f"New Article: {article.title}"
    body = (
        f"Title: {article.title}\n"
        f"Author: {article.author.username}\n"
        f"Publisher: {scope}\n\n"
        f"Excerpt:\n{excerpt}\n\n"
        f"Read more: {link}\n"
    )

    recipients = _subscriber_emails(article)
    if recipients:
        EmailMessage(
            subject=subject,
            body=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=list(recipients),
        ).send(fail_silently=False)

    x_text = f"NEW: {article.title} — {article.author.username} ({scope}) {link}"
    try:
        post_to_x(x_text)
    except Exception:
        # External failures should never block publishing.
        pass
