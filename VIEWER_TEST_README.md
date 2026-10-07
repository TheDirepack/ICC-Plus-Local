# ICC Plus Viewer Test

This is the minimal Viewer/runtime-testing distribution of ICC Plus Local. It is intended for testing an existing ICC Plus project from the player's side. It deliberately does not include CYOA generation, editing, styling, media, build-manifest, packaging, or Creator-authoring tooling.

## Included runtime abilities

- Load an existing ICC Plus project JSON.
- Evaluate Row and Choice requirements.
- Produce the player-visible Row / Choice / Addon hierarchy.
- Simulate selections, deselections, points, variables, forced activation/deactivation, cleanup, Row limits, Addons, and the other runtime behavior documented in `COVERAGE.md`.
- Run deterministic scenario tests.
- Check Row visibility directly for fast gating tests.

The official ICC Plus Viewer remains the authority for browser-only rendering, CSS, animation, media playback, dialogs, and other behavior outside the documented headless runtime boundary.

## Command

Install the included source as a Python package, or run it directly from the extracted ZIP:

```bash
python -m iccplus_tools.viewer_cli view project.json
python -m iccplus_tools.viewer_cli status project.json choice_id
python -m iccplus_tools.viewer_cli row-visible project.json row_id
python -m iccplus_tools.viewer_cli scenario project.json scenario.json
```

If installed through the included `pyproject.toml`, the same interface is available as `iccplus-viewer-test`.

## Skills and documentation

Start with `skills/iccplus-viewer-test/SKILL.md`. The package also includes the player-view, gameplay-runner, testing, visibility, continuation/playtest, and upstream-parity documentation relevant to Viewer testing.
