from django import forms


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
    """POST form collecting the details needed to book a seat."""

    customer_name = forms.CharField(
        max_length=255,
        label="Your name",
        widget=forms.TextInput(attrs={"placeholder": "Ada Lovelace"}),
    )
    customer_email = forms.EmailField(
        label="Your email",
        widget=forms.EmailInput(attrs={"placeholder": "ada@example.com"}),
    )
