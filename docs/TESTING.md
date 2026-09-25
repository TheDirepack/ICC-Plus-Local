# Testing

## Source regression

```bash
python -m pytest -q
./run-compression-tests
```

The normal suite covers phase authoring, bulk editing, style manifests, automatic image compression, player-safe simulation, command discovery, schema packaging, import/export helpers, and pinned upstream semantics.

## LLM-facing gameplay audit

Use `play` rather than a separate test namespace.

```bash
iccplus-local play project.json @audit.json --state run.json
```

A good audit checks Point balances, selected IDs, availability, unlocks, Row limits, visible Requirements/Scores, Addons, and hidden-content non-leakage after each action.

## Release checks

A release candidate should verify:

- the canonical top-level command list,
- `reference commands` recursive discovery,
- all three phase schemas,
- blank generation,
- structure/rules/style writes with automatic validation,
- automatic image compression,
- progressive and multi-step player-safe `play`,
- build output validation,
- clean installed-wheel smoke tests.

Official Creator/Viewer browser verification remains a separate release gate.
