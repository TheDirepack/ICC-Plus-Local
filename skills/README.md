# CYOA skill set

Use the smallest skill set that adds distinct reasoning. ICC Plus Local is the single implementation skill for native ICC Plus 2 work.

Current bundled implementation: **ICC Plus Local 0.10.0rc13**, targeting **ICC Plus 2.10.7**.

## Active skills

- `cyoa-develop` coordinates long, multi-pass or multi-session work.
- `cyoa-plan` handles new CYOA design and major redesign.
- `cyoa-review` audits design, content quality, balance, reachability, and implementation risk.
- `cyoa-migrate` handles legacy ICC or ICC Plus 1.x migration.
- `cyoa-ship` handles final packaging, hosted/offline release checks, static editions, and release records.
- `cyoa-compress` is only for exceptional standalone compression of external or legacy asset trees.
- `iccplus-local` handles native ICC Plus 2 inspection, creation, editing, styling, media, validation, hydration, building, serialization, and player-safe testing.
- External Unslop handles non-code prose cleanup.

## Removed wrappers

Do not recreate separate `cyoa-create`, `cyoa-edit`, `cyoa-look`, or `cyoa-test` skills. ICC Plus Local now owns those jobs through its focused function guides:

- creation and editing: `generate`, `build`, `inspect`, `structure`, and `rules`
- visuals and media: `style`, `media`, and `template`
- mechanical and stateful testing: `inspect`, `play`, `reference parity`, and `project validate`

The project-wide CYOA guide remains the design and UX reference. Removing wrapper skills does not remove those rules.

## Routing

Use `cyoa-plan` while the design is unsettled. Use `cyoa-migrate` for pre-ICC-Plus-2 source. Use `iccplus-local` for native project implementation, modification, styling, and local testing. Use `cyoa-review` for design/content audits. Use `cyoa-ship` for final delivery checks. Use `cyoa-develop` only when several of these must stay coordinated across a longer effort.

Use `cyoa-compress` only when an external asset tree must be compressed outside the normal ICC Plus Local media workflow.

## ICC Plus Local

Read `iccplus-local/SKILL.md`, then only the function guide needed for the current operation under `iccplus-local/functions/`.

The canonical command tree is `reference`, `template`, `media`, `project`, `inspect`, `generate`, `build`, `structure`, `rules`, `style`, and `play`.

Normal writes fill missing official Creator defaults and run complete-project validation. Use `project validate` for final completeness checks and `project hydrate` to repair supported sparse or legacy ICC Plus 2 projects.

For styling, prefer project styling, then official Row/Choice Design Groups, then one-off private styling. Use custom CSS only when native ICC Plus styling cannot express the result.

## Documentation

Start with `../docs/cyoa/guide/00-index.md` for design and implementation guidance.

Detailed local-tool documentation and release metadata live at the repository root and under `docs/`.

`SKILL-STANDARD.md` defines the local skill rules. `ROUTING-EVALS.md` tests routing. `REVISION-NOTES.md` records historical changes.

Shared cross-project skills such as Unslop are external to this repository. Keep this `skills/` directory focused on the CYOA and ICC Plus Local skills shipped here.