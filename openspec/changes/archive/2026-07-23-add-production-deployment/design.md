## Context

The four Exercise-11 questions map onto concrete choices for this app
(Django + HTMX + SQLite, no user uploads):

- **Hosting?** render.com (free web service) as the primary target, with a
  documented local production run for the "full production environment locally"
  option.
- **Application server?** waitress — pure-Python WSGI, runs on the developer's
  macOS as well as render's Linux, and is exactly what the lecture uses. Django
  already exposes a WSGI app at `cinema.wsgi:application`.
- **Static files (CSS/JS)?** WhiteNoise, so the app server itself serves
  compressed static assets — no separate Nginx/Apache needed for a project this
  size.
- **Uploaded files/media?** None. `Movie.poster_image` is a `URLField`
  (external URL), so there are no uploads to store or serve.

## Goals / Non-Goals

**Goals:**
- One command runs the app in production mode locally.
- A render.com deploy works without hand-editing hosts.
- The existing `runserver` dev loop keeps working unchanged.

**Non-Goals:**
- Nginx / reverse proxy / SSL termination (WhiteNoise + render's built-in TLS
  cover this project; the lecture's Nginx pipeline is overkill here).
- Postgres — SQLite is retained (see Risks for the render caveat).

## Decisions

- **Env-driven settings with dev defaults.** `SECRET_KEY`, `DEBUG`, and
  `ALLOWED_HOSTS` come from `DJANGO_SECRET_KEY` / `DJANGO_DEBUG` /
  `DJANGO_ALLOWED_HOSTS`. Defaults keep local `runserver` behaving exactly as
  before (`DEBUG=True`, localhost hosts); production sets `DJANGO_DEBUG=False`
  and a generated secret key. Keeping the dev default at `True` avoids breaking
  the everyday workflow (static served automatically by `runserver`); the
  render config and the documented local-production command both set it to
  `False` explicitly.
- **WhiteNoise `CompressedStaticFilesStorage` (not the Manifest variant).**
  The manifest storage raises "missing manifest entry" whenever a template
  renders `{% static %}` without a prior `collectstatic` — which would break
  the test suite and the dev loop. The compressed (non-manifest) storage gives
  gzip/brotli compression without that failure mode.
- **Auto-detect render's host.** render sets `RENDER_EXTERNAL_HOSTNAME`; when
  present it is appended to `ALLOWED_HOSTS` and used to build
  `CSRF_TRUSTED_ORIGINS = ["https://<host>"]`. This means a fresh render deploy
  needs no manual host/CSRF configuration for reservation POSTs to work.
- **build.sh does install + collectstatic + migrate.** render runs it on every
  deploy, so static files are collected and migrations applied automatically.

## Risks / Trade-offs

- [render's free tier has an ephemeral filesystem → the SQLite DB resets on
  each deploy/restart] → Acceptable for a course demo; documented in the README
  with the persistent-disk / Postgres upgrade path noted.
- [Defaulting `DEBUG=True` for dev means a deploy that forgets
  `DJANGO_DEBUG=False` runs insecurely] → Mitigated by baking
  `DJANGO_DEBUG=False` into `render.yaml` and the documented local-production
  command, so every production path sets it explicitly.
