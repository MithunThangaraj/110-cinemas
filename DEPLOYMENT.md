# Deployment

The live app: **https://one10-cinemas.onrender.com**

You do not need anything in this file to run 110 Cinemas locally — see the
[README](README.md) for that. This covers how the deployed copy is put
together.

## How the pieces fit

- **waitress** runs the Django WSGI app. No Gunicorn, so it works the same way
  on Windows.
- **WhiteNoise** serves the collected static files (CSS) straight from the app
  server, so there is no separate Nginx or Apache.
- There are **no media/upload files** to serve: movie posters are external URLs
  (`Movie.poster_image` is a `URLField`).

## Configuration

Settings are read from the environment, with development-friendly defaults so
`runserver` works with no setup at all:

| Variable | Default | Purpose |
| --- | --- | --- |
| `DJANGO_DEBUG` | `True` | Set to `False` in production. |
| `DJANGO_SECRET_KEY` | insecure dev key | Set a long random value in production. |
| `DJANGO_ALLOWED_HOSTS` | `localhost,127.0.0.1` | Comma-separated allowed hosts. |
| `RENDER_EXTERNAL_HOSTNAME` | set by render | Auto-added to allowed hosts and CSRF trusted origins, and switches on the HTTPS hardening. |

## Deploy to render.com

The repo includes `render.yaml` (the service blueprint) and `build.sh` (the
build step), so the whole service is described in the repository.

1. Push the repository to GitHub.
2. On https://render.com create a new **Blueprint** and point it at the repo.
   render reads `render.yaml`.
3. render runs `build.sh`: install dependencies, `collectstatic`, `migrate`,
   `seed_demo_data`, then `fetch_posters`.
4. `DJANGO_DEBUG=False` and a generated `DJANGO_SECRET_KEY` come from
   `render.yaml`. `RENDER_EXTERNAL_HOSTNAME` is provided by render.

Merging to `main` triggers a redeploy.

## Why the start command passes `--trusted-proxy`

This one cost a live outage, so it is worth writing down.

waitress defaults to `clear_untrusted_proxy_headers=True`, which **strips**
render's `X-Forwarded-Proto` header. Django then sees an HTTPS request as
insecure, `SECURE_SSL_REDIRECT` redirects it to HTTPS, and the site loops
`https -> https` forever. Trusting the proxy for that one header fixes it:

```
uv run waitress-serve --port=$PORT --trusted-proxy='*' \
  --trusted-proxy-headers=x-forwarded-proto cinema.wsgi:application
```

The `'*'` is safe **only** because render terminates TLS in front of the
container and nothing else can reach the port. Anywhere the port were directly
reachable, a client could forge the header and switch HTTPS enforcement off.

## Run the production stack locally

Useful for reproducing a deployment problem without deploying:

```bash
# 1. Collect static files for WhiteNoise to serve.
DJANGO_DEBUG=False uv run python manage.py collectstatic --no-input

# 2. Apply migrations.
uv run python manage.py migrate

# 3. Serve the way production does.
DJANGO_DEBUG=False \
DJANGO_SECRET_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(50))')" \
DJANGO_ALLOWED_HOSTS="localhost,127.0.0.1" \
uv run waitress-serve --host=127.0.0.1 --port=8000 cinema.wsgi:application
```

Then open http://127.0.0.1:8000/.

## Demo data and the admin user

render's free tier starts from an empty database on every deploy, so `build.sh`
runs `seed_demo_data` (which does nothing once movies exist) followed by
`fetch_posters`. A failed poster lookup never fails the build.

To get an admin login on the deployed site, set these in the render dashboard —
choose your own password; nothing is stored in the repo. `build.sh` creates the
superuser only when they are present:

- `DJANGO_SUPERUSER_USERNAME`
- `DJANGO_SUPERUSER_EMAIL`
- `DJANGO_SUPERUSER_PASSWORD`

## Known limitation: the database is ephemeral

render's free tier has an ephemeral filesystem, so the SQLite database is reset
on every deploy and restart. Bookings made on the live site do not survive a
redeploy. That is fine for a demo.

For durable data, attach a persistent disk and point the SQLite file at it, or
switch `DATABASES` to a managed Postgres instance.
