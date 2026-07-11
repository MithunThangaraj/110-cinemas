from django import forms


class MovieSearchForm(forms.Form):
    """GET form for filtering the movie list by title."""

    q = forms.CharField(
        required=False,
        label="Search",
        widget=forms.TextInput(attrs={"placeholder": "Search movies..."}),
    )


class ReservationForm(forms.Form):
    """POST form collecting the details needed to book a seat."""

    customer_name = forms.CharField(max_length=255, label="Your name")
    customer_email = forms.EmailField(label="Your email")
