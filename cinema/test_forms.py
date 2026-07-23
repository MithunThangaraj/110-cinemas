from .forms import MovieSearchForm, ReservationForm


class TestReservationForm:
    def test_valid_data(self):
        form = ReservationForm(
            {"customer_name": "Ada Lovelace", "customer_email": "ada@example.com"}
        )
        assert form.is_valid()

    def test_missing_name_is_invalid(self):
        form = ReservationForm(
            {"customer_name": "", "customer_email": "ada@example.com"}
        )
        assert not form.is_valid()
        assert "customer_name" in form.errors

    def test_invalid_email_is_invalid(self):
        form = ReservationForm(
            {"customer_name": "Ada", "customer_email": "not-an-email"}
        )
        assert not form.is_valid()
        assert "customer_email" in form.errors


class TestMovieSearchForm:
    def test_blank_query_is_valid(self):
        form = MovieSearchForm({"q": ""})
        assert form.is_valid()

    def test_query_is_optional(self):
        form = MovieSearchForm({})
        assert form.is_valid()
