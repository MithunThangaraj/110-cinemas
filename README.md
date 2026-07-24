# 110 Cinemas

A simple web application for browsing movies and reserving cinema seats.

## Tech stack
- **Backend**: Python / Django + HTMX
- **Database**: SQLite
- **App server (production)**: waitress
- **Static files (production)**: WhiteNoise

## Setup
```bash
uv venv
source .venv/bin/activate
uv sync
```

## Run (development)
```bash
uv run python manage.py migrate
uv run python manage.py runserver
```
Then open http://localhost:8000/movies/. Create some data via the admin:
```bash
uv run python manage.py createsuperuser
```
and add a Movie and a Screening at http://localhost:8000/admin/ (seats are
generated automatically when a screening is saved).

## Run Linter
```bash
uv run pylint cinema
```

## Run Tests
```bash
uv run pytest --cov
```

## Configuration (environment variables)

Settings are read from the environment, with development-friendly defaults so
`runserver` works out of the box:

| Variable | Default | Purpose |
| --- | --- | --- |
| `DJANGO_DEBUG` | `True` | Set to `False` in production. |
| `DJANGO_SECRET_KEY` | insecure dev key | Set a long random value in production. |
| `DJANGO_ALLOWED_HOSTS` | `localhost,127.0.0.1` | Comma-separated allowed hosts. |
| `RENDER_EXTERNAL_HOSTNAME` | (set by render.com) | Auto-added to allowed hosts and CSRF trusted origins. |

## Deployment

**How the pieces fit:** `waitress` runs the Django WSGI app; `WhiteNoise`
serves the collected static files (CSS/JS) directly from the app server, so no
separate Nginx/Apache is needed. There are **no media/upload files** to serve —
movie posters are external URLs (`Movie.poster_image` is a `URLField`).

### Local production run

Run the app the way production does (no `runserver`, `DEBUG=False`):

```bash
# 1. Collect static files into staticfiles/ for WhiteNoise to serve.
DJANGO_DEBUG=False uv run python manage.py collectstatic --no-input

# 2. Apply migrations.
uv run python manage.py migrate

# 3. Serve with waitress in production mode.
DJANGO_DEBUG=False \
DJANGO_SECRET_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(50))')" \
DJANGO_ALLOWED_HOSTS="localhost,127.0.0.1" \
uv run waitress-serve --host=127.0.0.1 --port=8000 cinema.wsgi:application
```
Open http://127.0.0.1:8000/movies/.

### Deploy to render.com

The repo includes `render.yaml` (service blueprint) and `build.sh` (build step).

1. Push the repository to GitHub.
2. On https://render.com, create a new **Blueprint** and point it at this repo;
   render reads `render.yaml`.
3. render runs `build.sh` (installs dependencies, runs `collectstatic`,
   `migrate`, and seeds demo data) and then starts the app with waitress.
4. `DJANGO_DEBUG=False` and a generated `DJANGO_SECRET_KEY` are set by
   `render.yaml`; `RENDER_EXTERNAL_HOSTNAME` is provided by render and is
   automatically trusted for hosts and CSRF, and enables HTTPS hardening.

**Why the start command passes `--trusted-proxy`:** waitress defaults to
`clear_untrusted_proxy_headers=True`, which strips render's `X-Forwarded-Proto`
header. Django would then treat HTTPS requests as insecure and
`SECURE_SSL_REDIRECT` would redirect `https -> https` forever. Trusting the
proxy for that one header fixes it:

```
uv run waitress-serve --port=$PORT --trusted-proxy='*' \
  --trusted-proxy-headers=x-forwarded-proto cinema.wsgi:application
```

### Demo data and the admin user on render

Because render's free tier starts with an empty database on every deploy,
`build.sh` runs `manage.py seed_demo_data`, which creates a few movies and
future screenings (with their seats) only if no movies exist yet. Run it
locally the same way:

```bash
uv run python manage.py seed_demo_data
```

To also get an admin login on the deployed site, add these as environment
variables in the render dashboard (choose your own password; it is never stored
in the repo). `build.sh` creates the superuser only when they are present:

- `DJANGO_SUPERUSER_USERNAME`
- `DJANGO_SUPERUSER_EMAIL`
- `DJANGO_SUPERUSER_PASSWORD`

> **Note on the database:** render's free tier has an ephemeral filesystem, so
> the SQLite database resets on each deploy/restart. That is fine for a demo.
> For durable data, attach a persistent disk (and point the SQLite file at it)
> or switch `DATABASES` to a managed Postgres instance.
