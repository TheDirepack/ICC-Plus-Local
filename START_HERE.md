# ICC Plus Local 0.10.0rc12 handoff

Use the workflow-centered interface only.

```text
generate -> structure -> rules -> style -> play
```

Edits validate automatically before write. Bulk work uses the same phase operations as single-item work. Image compression is automatic.

Use `inspect` for read-only project discovery. Use `reference commands` for the complete command tree, `reference fields` for native fields, and `reference schema` for machine-readable contracts.

Template operations live under `template`, media under `media`, and project serialization/import/export under `project`. Do not introduce new one-off top-level commands when an existing phase or namespace can own the behavior.

`play` is the simulator and audit interface. Its player view exposes visible Rows, direct Choices, and Addons as separate structures with explicit parent/child links. Multi-step requests can assert visible Point balances, selections, availability, visibility, Row-to-Choice membership, and Choice-to-Row parentage after each action.

Compatibility aliases exist only for older scripts and should not be used by new automation.

For agent use, start with `skills/iccplus-local/SKILL.md`. For the rc11 player hierarchy, read `docs/PLAY_STRUCTURE.md`; `docs/GAMEPLAY_RUNNER.md` covers progressive play audits.
