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
