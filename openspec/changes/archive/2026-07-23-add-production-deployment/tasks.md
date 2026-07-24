## 1. Dependencies

- [x] 1.1 Add `whitenoise` and `waitress` to project dependencies

## 2. Production settings

- [x] 2.1 Read `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS` from env with dev defaults
- [x] 2.2 Add `STATIC_ROOT` and WhiteNoise `CompressedStaticFilesStorage`
- [x] 2.3 Insert WhiteNoise middleware right after `SecurityMiddleware`
- [x] 2.4 Auto-detect `RENDER_EXTERNAL_HOSTNAME` for `ALLOWED_HOSTS` and
      `CSRF_TRUSTED_ORIGINS`
- [x] 2.5 Ignore `staticfiles/` in `.gitignore`

## 3. render.com deploy files

- [x] 3.1 Add `build.sh` (install deps, collectstatic, migrate)
- [x] 3.2 Add `render.yaml` (web service: build + waitress start command, env vars)

## 4. Documentation

- [x] 4.1 Update README with deployment section (local production + render.com)

## 5. Verification

- [x] 5.1 `uv run pytest --cov` still passes
- [x] 5.2 `uv run black .` and `uv run pylint cinema`
- [x] 5.3 Local production run: `collectstatic`, then `DJANGO_DEBUG=False`
      waitress serving; confirm pages render and WhiteNoise serves the CSS
