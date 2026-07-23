## Context

Every template currently renders unstyled HTML: no CSS, no viewport meta tag,
inconsistent labeling on form controls, and a seat grid that's just a flat
`<ul>` regardless of screen width. Exercise 9's four review questions (clean
HTML structure, CSS/structure separation, responsive design, accessibility)
map directly onto four concrete changes.

## Goals / Non-Goals

**Goals:**
- One stylesheet, zero inline styles, zero `<style>` tags in templates.
- A layout that's usable on a phone-width viewport without horizontal
  scrolling or overlapping controls.
- Forms and the seat grid usable with a screen reader and keyboard-only
  navigation.

**Non-Goals:**
- A visual redesign / branding — plain, clean, and legible is the bar here,
  not a polished consumer product.
- Any new URLs, fields, or behavior (Exercise 8 territory, already done).
- HTMX/dynamic updates (Exercise 10).

## Decisions

- **Plain CSS, no framework.** Adding Bootstrap/Tailwind would be a new
  dependency for a "basic principles" exercise; a single hand-written
  stylesheet is enough to demonstrate structure/presentation separation and
  keeps `AGENTS.md`'s "don't install packages without confirming" constraint
  moot.
- **Mobile-first with a single breakpoint.** The seat grid and movie list are
  the only layouts complex enough to need reflow; one `@media (min-width: ...)`
  breakpoint switching from a single column to a wider grid covers both. This
  avoids an over-engineered set of breakpoints for a four-page app.
- **CSS Grid for the seat grid**, since seats are naturally a 2D layout (row ×
  number) — closer to the physical seat map than a `<ul>`, and easy to reflow
  by changing `grid-template-columns` at the breakpoint.
- **`<fieldset>`/`<legend>` for the seat grid**, since it's conceptually one
  control ("pick a seat") made of many individual seat buttons/links —
  fieldset gives screen reader users that grouping for free.
- **`aria-live="polite"` on the messages list** in `base.html`: flash messages
  appear after a redirect (e.g. "seat reserved" / "already reserved"), so a
  screen reader user landing on the new page should have them announced
  without needing to hunt for them.
- **A skip-to-content link** as the very first focusable element, hidden
  visually until focused — cheap to add, meaningfully helps keyboard users
  skip the header/nav on every page load.

## Risks / Trade-offs

- [Hand-rolled CSS won't match a framework's polish] → Acceptable; the
  exercise asks for structure/presentation separation and responsiveness, not
  visual design maturity.
- [No automated accessibility test] → Verified manually (resize to mobile
  width, keyboard-only tab-through, check computed contrast) rather than
  adding a new tool/dependency for one exercise.
