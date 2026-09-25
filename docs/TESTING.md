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

Official Creator/Viewer browser verification remains a separate release gate. The retained exact browser round-trip evidence is from 2.10.6; rc13 does not claim a fresh 2.10.7 browser round-trip.
