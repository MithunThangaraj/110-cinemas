## Why

The project only runs under Django's development server (`runserver`) with
`DEBUG = True`, a hard-coded `SECRET_KEY`, and empty `ALLOWED_HOSTS`. Exercise 11
requires a production-ready build that can be deployed to a real environment
(locally in production mode, and to an external host such as render.com).

## What Changes

- Add `whitenoise` (serve static files from the app server, no separate web
  server needed) and `waitress` (a production WSGI server) as dependencies.
- Make `settings.py` environment-driven and production-safe:
  - `SECRET_KEY`, `DEBUG`, and `ALLOWED_HOSTS` read from environment variables,
    with dev-friendly defaults so the existing `runserver` workflow is
    unchanged.
  - `STATIC_ROOT` for `collectstatic`, WhiteNoise static-files storage, and the
    WhiteNoise middleware directly after `SecurityMiddleware`.
  - `CSRF_TRUSTED_ORIGINS` for the deployed HTTPS host so form POSTs (seat
    reservation) work behind TLS.
  - Auto-detect render.com's host (`RENDER_EXTERNAL_HOSTNAME`) so a render
    deploy needs no manual host configuration.
- Add render.com deploy files: `render.yaml` (service definition) and
  `build.sh` (install deps, collectstatic, migrate).
- Document both a local production run (waitress + `DEBUG=False`) and a
  render.com deploy in the README.

**Media files:** none needed — movie posters are external URLs (`URLField`),
so there are no user uploads to serve. This is called out explicitly rather
than configuring an unused media pipeline.

## Capabilities

### New Capabilities
- None (deployment/infrastructure only — no user-facing behavior changes).

### Modified Capabilities
- None.

## Impact

- Modified: `pyproject.toml`, `uv.lock`, `cinema/settings.py`, `.gitignore`,
  `README.md`.
- New: `render.yaml`, `build.sh`.
- No migrations, no view/model/URL changes.
