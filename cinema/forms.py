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


# Booking currently asks for nothing but the seats: `Reservation.customer_name`
# and `customer_email` are still on the model, so a details step can be added
# back later without a migration.
