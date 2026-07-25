from .forms import MovieSearchForm


class TestMovieSearchForm:
    def test_blank_query_is_valid(self):
        form = MovieSearchForm({"q": ""})
        assert form.is_valid()

    def test_query_is_optional(self):
        form = MovieSearchForm({})
        assert form.is_valid()

    def test_labels_have_no_colon_suffix(self):
        form = MovieSearchForm()
        assert form["q"].label_tag().endswith("Search</label>")
