# ICC Plus Local 0.10.0rc13 handoff

The engine target remains ICC Plus 2.10.7, pinned to upstream commit `1ea9db888cde2286d18d0d5de50933cb8773b739`.

Use the workflow-centered ICC Plus Local interface:

```text
generate -> structure -> rules -> style -> play
```

Use `inspect` for read-only project discovery. Use `reference commands` for the complete command tree, `reference fields` for native fields, and `reference schema` for machine-readable contracts. Template operations live under `template`, media under `media`, and project validation, hydration, serialization, import, and export under `project`.

Normal `structure`, `rules`, and `style` writes fill missing official Creator defaults and require complete-project validation before replacement. Use `project validate` for a final Creator-complete check and `project hydrate` to repair supported sparse or legacy ICC Plus 2 input without inventing missing IDs.

For styling, use project styling first, then official Row/Choice Design Groups. Use private Row or Choice styling only for genuine one-off exceptions. Use custom CSS only when native ICC Plus styling cannot express the result.

`play` is the player-safe simulator and audit interface. It exposes visible Rows, direct Choices, and Addons as separate structures with explicit parent/child links. Keep continuation state private with `--state FILE`.

## CYOA skill routing

Use `skills/iccplus-local/SKILL.md` for native ICC Plus 2 creation, editing, styling, media work, validation, building, serialization, and mechanical playtesting.

Use the retained high-level skills only when the task adds work outside the CLI:

- `cyoa-plan` for design and major redesign.
- `cyoa-review` for design, balance, content, and implementation audits.
- `cyoa-migrate` for legacy ICC or ICC Plus 1.x conversion.
- `cyoa-develop` for long multi-pass or multi-session coordination.
- `cyoa-ship` for final packaging and release QA.
- `cyoa-compress` only for an exceptional external or legacy asset tree outside the normal media workflow.

The retired wrappers `cyoa-create`, `cyoa-edit`, `cyoa-look`, and `cyoa-test` must not be reintroduced.

Start CYOA documentation at `docs/cyoa/guide/00-index.md`. For the current player hierarchy, read `docs/PLAY_STRUCTURE.md`; `docs/GAMEPLAY_RUNNER.md` covers progressive play audits.
