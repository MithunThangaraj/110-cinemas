# Diagrams

## Database schema

![110 Cinemas database schema](schema.png)

- `schema.puml` — PlantUML source. Edit this, not the images.
- `schema.png` — for slides and documents.
- `schema.svg` — vector, stays sharp at any size.

Re-render after editing the source:

```bash
curl -X POST https://kroki.io/plantuml/png \
  -H "Content-Type: text/plain" \
  --data-binary "@docs/schema.puml" -o docs/schema.png
```
