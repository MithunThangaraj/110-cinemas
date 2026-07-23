## Why

Exercise 9 asks for a pass on interface quality: clean HTML structure, CSS
separated from markup, a responsive layout, and basic accessibility. Right
now every template has zero styling, no viewport meta tag, and inconsistent
label/form markup — it works, but only as "plain HTML pages, hyperlinks, and
input forms" (the baseline the earlier exercises explicitly allowed).

## What Changes

- Add `cinema/static/cinema/css/styles.css` and link it from `base.html`;
  no inline styles or `<style>` blocks in any template.
- Add a proper `<head>` (viewport meta tag, charset already present) and a
  consistent page skeleton: header/nav landmark, `<main>`, `<footer>`.
- Rework each template's markup to be semantic: use `<label for>` linked to
  every input, `<fieldset>`/`<legend>` where a group of controls belongs
  together (the seat grid), and heading levels that nest correctly
  (`h1` site title → `h2` page heading → no skipped levels).
- Responsive layout: a fluid, mobile-first CSS layout using flexbox/grid and
  a small number of media query breakpoints, so the seat grid and movie list
  reflow instead of overflowing on narrow viewports.
- Accessibility pass: visible `:focus` states, sufficient color contrast,
  a skip-to-content link, `aria-live` on the messages list (Django's
  messages/flash banners appear after a redirect, so screen readers should
  announce them), and `alt` text wherever an image is shown.
- No behavior changes: no new URLs, no new fields, no changed validation.
  This is presentation-only.

## Capabilities

### New Capabilities
- None.

### Modified Capabilities
- None — this changes presentation, not the requirements captured in
  `openspec/specs/web-views` or any other capability. No spec-level behavior
  changes.

## Impact

- New file: `cinema/static/cinema/css/styles.css`.
- Modified files: all templates under `cinema/templates/cinema/`.
- No new dependencies, no migrations, no URL/view/model changes.
