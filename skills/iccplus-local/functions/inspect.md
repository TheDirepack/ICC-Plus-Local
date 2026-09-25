# inspect

Read this file when the task needs to understand an existing project without changing it.

Use `inspect` for batched read-only project queries such as summaries, identities, search, show, selector previews, statistics, validation reports, and visual work queues.

```bash
iccplus-local inspect project.json @inspect.json
```

Inspect before editing an unfamiliar project. Prefer one batched request over many small reads when the required information is known in advance.

Use selector preview before a broad edit when a selector could match more or fewer entities than intended. If command or schema details are unclear, read `reference.md` and query `reference` instead of guessing.

Use `play` rather than `inspect` when the question is what a player can currently see, select, or deselect.

See `../../../docs/LLM_USAGE.md`, `FIELD_CATALOG.md`, and `BULK_SELECTORS.md` for more detail.
