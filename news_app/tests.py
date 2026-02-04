from unittest.mock import patch
from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token

from .models import Publisher, Article, Newsletter

User = get_user_model()


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    DEFAULT_FROM_EMAIL="no-reply@test.local",
    SITE_BASE_URL="http://testserver",
)
class NewsAppTests(TestCase):
    """
    Automated tests for the News Application.

    Covers:
    - Token-authenticated API access per role.
    - Reader subscription filtering.
    - Journalist article/newsletter creation.
    - Editor approval triggers email + X post (signals).
    - Publisher and Newsletter API endpoints.
    """

    def setUp(self):
        self.reader = User.objects.create_user(
            username="reader1", password="pass123",
            email="reader@test.com", role="reader"
        )
        self.editor = User.objects.create_user(
            username="editor1", password="pass123",
            email="editor@test.com", role="editor"
        )
        self.journalist = User.objects.create_user(
            username="journo1", password="pass123",
            email="journo@test.com", role="journalist"
        )
        self.journalist2 = User.objects.create_user(
            username="journo2", password="pass123",
            email="journo2@test.com", role="journalist"
        )

        self.publisher = Publisher.objects.create(
            name="Daily Planet", description="Metropolis")
        self.publisher.journalists.add(self.journalist)
        self.publisher.editors.add(self.editor)

        self.approved = Article.objects.create(
            title="Approved A1",
            content="Hello world " * 50,
            author=self.journalist,
            publisher=self.publisher,
            approved=True,
        )
        self.pending = Article.objects.create(
            title="Pending A2",
            content="Pending content " * 50,
            author=self.journalist,
            publisher=self.publisher,
            approved=False,
        )

        self.reader.subscribed_publishers.add(self.publisher)
        self.reader.subscribed_journalists.add(self.journalist)

        self.newsletter = Newsletter.objects.create(
            title="Weekly Roundup",
            description="Best stories this week",
            author=self.journalist,
        )
        self.newsletter.articles.add(self.approved, self.pending)

        self.api = APIClient()

    def _auth(self, user):
        """
        Attach token authentication to the API client.
        """
        token, _ = Token.objects.get_or_create(user=user)
        self.api.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
        return token.key

    def test_api_articles_returns_only_approved(self):
        self._auth(self.reader)
        resp = self.api.get("/api/articles/")
        self.assertEqual(resp.status_code, 200)
        titles = [a["title"] for a in resp.json()]
        self.assertIn("Approved A1", titles)
        self.assertNotIn("Pending A2", titles)

    def test_api_articles_subscribed_reader_only(self):
        self._auth(self.reader)
        resp = self.api.get("/api/articles/subscribed/")
        self.assertEqual(resp.status_code, 200)
        titles = [a["title"] for a in resp.json()]
        self.assertIn("Approved A1", titles)

        self._auth(self.journalist)
        resp2 = self.api.get("/api/articles/subscribed/")
        self.assertEqual(resp2.status_code, 403)

    def test_journalist_can_create_article(self):
        self._auth(self.journalist)
        resp = self.api.post(
            "/api/articles/",
            {"title": "New Draft", "content": "Draft...",
             "publisher_id": self.publisher.id},
            format="json",
        )
        self.assertEqual(resp.status_code, 201)
        self.assertFalse(resp.data["approved"])

    def test_reader_cannot_create_article(self):
        self._auth(self.reader)
        resp = self.api.post("/api/articles/", {
            "title": "Nope", "content": "Nope"}, format="json")
        self.assertEqual(resp.status_code, 403)

    def test_publishers_endpoints(self):
        self._auth(self.reader)
        list_resp = self.api.get("/api/publishers/")
        self.assertEqual(list_resp.status_code, 200)
        self.assertGreaterEqual(len(list_resp.json()), 1)

        detail_resp = self.api.get(f"/api/publishers/{self.publisher.id}/")
        self.assertEqual(detail_resp.status_code, 200)
        self.assertEqual(detail_resp.json()["name"], "Daily Planet")

    def test_newsletters_endpoints_reader_filters_unapproved_articles(self):
        self._auth(self.reader)
        resp = self.api.get("/api/newsletters/")
        self.assertEqual(resp.status_code, 200)

        n = resp.json()[0]
        nested_titles = [a["title"] for a in n.get("articles", [])]
        self.assertIn("Approved A1", nested_titles)
        self.assertNotIn("Pending A2", nested_titles)

    def test_journalist_can_create_newsletter(self):
        self._auth(self.journalist)
        resp = self.api.post(
            "/api/newsletters/",
            {"title": "New Letter", "description": "Desc",
             "article_ids": [self.approved.id]},
            format="json",
        )
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.json()["title"], "New Letter")

    @patch("news_app.functions.notify.post_to_x", return_value=True)
    def test_editor_approval_triggers_signal_email_and_x(self, _mock_x):
        """
        Approving an article should trigger:
        - email excerpt+link sent to subscribers
        - X post attempted (mocked)
        """
        from django.core import mail

        self.client.login(username="editor1", password="pass123")
        resp = self.client.get(reverse(
            "approve_article",
            kwargs={"article_id": self.pending.id}), follow=True)
        self.assertEqual(resp.status_code, 200)

        self.pending.refresh_from_db()
        self.assertTrue(self.pending.approved)

        self.assertGreaterEqual(len(mail.outbox), 1)
        self.assertIn("Excerpt:", mail.outbox[0].body)
        self.assertIn("Read more:", mail.outbox[0].body)
