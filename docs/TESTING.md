# Testing

## CI regression gate

Run the same source and example checks used by GitHub Actions:

```bash
python -m pytest -q tests cli_tests
./examples/test_examples.sh
```

The suite covers phase authoring, bulk editing, style manifests and Design Groups, automatic image compression behavior, player-safe simulation, project completeness and hydration, command discovery, schema packaging, import/export helpers, skill/documentation consistency, and pinned upstream semantics.

The standalone compression diagnostics remain available when asset-compression behavior itself is under investigation. They are not a required extra authoring step for normal media assignment.

## LLM-facing gameplay audit

Use `play` rather than a separate test namespace:

```bash
iccplus-local play project.json @audit.json --state run.json
```

A useful audit checks Point balances, selections, availability, unlocks, Row limits, visible Requirements or Scores, Addons, and hidden-content non-leakage after each action.

## Release checks

A release candidate should verify the canonical command list, recursive `reference commands` discovery, phase schemas, blank generation, normal write validation, project hydration/completeness, Design Group styling, automatic image compression, progressive `play`, repeatable builds, checked-in examples, and installed-wheel smoke tests.

The pinned **Viewer** Chromium differential is separately tested by `.github/workflows/upstream-parity.yml` and passed on the merged rc17 head (99 gameplay cases, 62 action traces, 13 full/sparse comparisons). This is not a Creator GUI import/export or visual/hosting test. The strongest retained exact Creator GUI round-trip evidence is the historical 2.10.6 C01 fixture; future Creator changes still require their own browser validation.
