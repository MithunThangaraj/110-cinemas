from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


class NoSuffixForm(forms.Form):
    """Base form that drops Django's trailing ":" from rendered labels.

    The redesigned interface styles labels as small uppercase captions, where
    a colon reads as a typo.
    """

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("label_suffix", "")
        super().__init__(*args, **kwargs)


class MovieSearchForm(NoSuffixForm):
    """GET form for filtering the movie list by title."""

    q = forms.CharField(
        required=False,
        label="Search",
        widget=forms.TextInput(attrs={"placeholder": "Search movies..."}),
    )


class ReservationForm(NoSuffixForm):
    """Who the booking is for, collected after the seats are chosen."""

    customer_name = forms.CharField(
        max_length=255,
        label="Your name",
        widget=forms.TextInput(
            attrs={"placeholder": "Ada Lovelace", "autocomplete": "name"}
        ),
    )
    customer_email = forms.EmailField(
        label="Your email",
        help_text="Your booking reference is shown on the next screen.",
        widget=forms.EmailInput(
            attrs={"placeholder": "ada@example.com", "autocomplete": "email"}
        ),
    )


class SignUpForm(UserCreationForm):
    """Free membership. Email is asked for so a booking can be confirmed."""

    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={"placeholder": "ada@example.com"}),
    )

    class Meta:
        model = User
        fields = ["username", "email"]

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("label_suffix", "")
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs["placeholder"] = "ada"

    def clean_email(self):
        email = self.cleaned_data["email"]
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with that email already exists.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user
