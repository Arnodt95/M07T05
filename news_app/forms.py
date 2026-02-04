from django import forms
from django.contrib.auth import get_user_model
from .models import Article, Newsletter, Publisher

User = get_user_model()


class RegisterForm(forms.Form):
    """
    Registration form for new users.

    Includes:
    - basic identity fields
    - password confirmation validation
    - role selection
    """
    ROLE_CHOICES = (
        ("reader", "Reader"),
        ("editor", "Editor"),
        ("journalist", "Journalist"),
    )

    username = forms.CharField(max_length=150)
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput, label="Password")
    password_confirm = forms.CharField(widget=forms.PasswordInput,
                                       label="Confirm password")
    role = forms.ChoiceField(choices=ROLE_CHOICES)

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get("password")
        p2 = cleaned.get("password_confirm")
        if p1 and p2 and p1 != p2:
            self.add_error("password_confirm", "Passwords do not match.")
        return cleaned


class LoginForm(forms.Form):
    """
    Basic login form.
    """
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)


class ArticleForm(forms.ModelForm):
    """
    Form to create/edit articles.

    - publisher is optional (independent article)
    - article image is optional (photo upload)
    """
    class Meta:
        model = Article
        fields = ["title", "content", "publisher", "image"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["publisher"].required = False
        self.fields["publisher"].empty_label = "Independent (No publisher)"

        self.fields["image"].required = False


class NewsletterForm(forms.ModelForm):
    """
    Form to create/edit newsletters.
    """
    class Meta:
        model = Newsletter
        fields = ["title", "description", "articles"]


class SubscriptionForm(forms.Form):
    """
    Reader subscription form: choose publishers and journalists.
    """
    publishers = forms.ModelMultipleChoiceField(
        queryset=Publisher.objects.all().order_by("name"),
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )
    journalists = forms.ModelMultipleChoiceField(
        queryset=User.objects.filter(role="journalist").order_by("username"),
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )
