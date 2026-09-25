# Command surface audit

Version 0.10.0rc10 reorganizes the CLI around workflows rather than implementation helpers.

The canonical top level is now 11 commands:

`reference`, `template`, `media`, `project`, `inspect`, `generate`, `build`, `structure`, `rules`, `style`, `play`.

## What was removed from the advertised surface

`creator` was dissolved. Its useful pieces moved to coherent owners:

- style presets and design files -> `template`
- fonts, sound, images, crops -> `media`
- ID/export/format/fragment helpers -> `project`
- command discovery, schemas, parity, symbols -> `reference`
- Row sort/copy/move -> existing `structure` operations

`test` was removed as a separate public concept. Progressive testing and audit now use `play`; deep internal analysis helpers remain compatibility/internal tooling.

`check` was removed from the normal workflow because normal edits already validate before writing. The read-only `inspect` interface can still request validation information when an audit needs it.

`build-viewer` was removed from the canonical authoring surface. The local simulator is `play`; packaging a browser viewer is a separate compatibility/release utility rather than something an authoring LLM should plan around.

`apply`, `session`, `state-check`, and the old one-off edit/read commands are compatibility/internal paths, not canonical authoring commands.

## Design rule

A new capability should first be added to an existing phase or focused namespace. New top-level commands require a genuinely separate workflow, not merely a new implementation helper.
