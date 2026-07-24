#!/usr/bin/env bash
# render.com build step: install dependencies, collect static files, migrate.
set -o errexit

# Install uv, then sync the exact locked dependencies.
pip install uv
uv sync --frozen

# Collect static files for WhiteNoise to serve.
uv run python manage.py collectstatic --no-input

# Apply database migrations.
uv run python manage.py migrate

# Seed demo movies/screenings so the deployed site isn't empty.
# render's free tier has an ephemeral disk, so the SQLite database starts empty
# on every deploy. This is a no-op once movies exist.
uv run python manage.py seed_demo_data

# Optionally create an admin user, but only if credentials were supplied as
# environment variables in the render dashboard. Never hard-code these.
if [[ -n "${DJANGO_SUPERUSER_USERNAME:-}" && -n "${DJANGO_SUPERUSER_PASSWORD:-}" ]]; then
  uv run python manage.py createsuperuser --noinput || true
fi
