# ICC Plus 2 CYOA guide

This is the working reference for planning, building, testing, and shipping CYOAs with ICC Plus 2.

The files are ordered by the normal project lifecycle. Read only the phase you need; use the index instead of memorizing chapter numbers.

## Authority

For engine behavior, use this order:

1. Target ICC Plus 2 Viewer and Creator behavior/source.
2. Official release notes for the target version.
3. Current `../../../` source notes and field references.
4. This guide.
5. Community material for design practice and player expectations only.

If the local model and target Viewer disagree, keep the project native to the Viewer and fix or limit the local model.

## Reading order

### Foundation and workflow

1. `01-operating-model-and-glossary.md` — project model, terminology, and evidence labels.
2. `02-creator-and-viewer.md` — Creator versus Viewer, saves, imports, and release formats.
3. `03-development-protocol.md` — long-running LLM work, source-of-truth rules, bounded passes, and consistency.
4. `04-authoring-workflow.md` — the end-to-end build sequence.

### Design and content

5. `05-planning-a-cyoa.md` — premise, player contract, section map, completion rules, IDs, and state planning.
6. `06-planning-templates.md` — reusable planning and review templates.
7. `07-formats-and-rule-systems.md` — Pick N, point-buy, drawbacks, prerequisites, repeated choices, branches, and other rule patterns.
8. `08-structure-and-player-flow.md` — section order, discoverability, navigation, density, and mobile flow.
9. `09-writing-choices-and-content.md` — choice writing, content coverage, character briefs, scenarios, and tone.
10. `10-research-ideation-and-images.md` — research discipline, ideation, image briefs, sourcing, crops, and asset records.
11. `11-balance-and-playtesting.md` — economy, synergies, full builds, independent accounting, and balance tests.

### ICC Plus implementation

12. `12-rows-choices-addons.md` — Rows, Choices, Addons, repeatable structures, and source-side templates.
13. `13-ids-state-requirements.md` — IDs, Variables, Requirements, hiding, state, and reachability.
14. `14-points-scores-words-groups.md` — Point Types, Scores, Words, Groups, and Design Groups.
15. `15-buttons-saves-backpack-media.md` — Buttons, build saves, Choice Import, Backpack, media, audio, and project CSS.
16. `16-visual-design-and-responsive-layout.md` — design system, card geometry, accessibility, responsive behavior, and visual QA.

### Testing and release

17. `17-local-testing.md` — current local inspection, player-safe regression tests, and parity boundaries.
18. `18-continuing-playtests.md` — private continuation state and multi-call playtesting.
19. `19-publishing-and-release.md` — package construction and release QA.
20. `20-troubleshooting.md` — symptom-first diagnosis and current recovery rules.

`SOURCES.md` records the source material behind the guide. `REVISION-NOTES.md` is historical change provenance, not active workflow guidance.

## Task shortcuts

- **Start or redesign a CYOA:** 05 → 11, using 03 and 04 for process.
- **Implement approved content:** 12 → 16, then 17 for mechanical tests.
- **Edit a current project:** read the affected implementation file, then 17 and 20 as needed.
- **Visual or image pass:** 10, 15, and 16.
- **Mechanical regression work:** 13, 14, 17, and 18 as relevant.
- **Review:** 05 → 11, then the implementation file for each issue found.
- **Ship:** 17 → 20, with the official Viewer as the final authority.
- **Legacy project:** use `../legacy-icc-reference/legacy-icc-migration-reference.md` first, then return here for the target state.

## Core design questions

A player should not have to reverse-engineer:

- what they are making or deciding,
- what they may choose,
- what each choice changes,
- when the build is finished and legal.

## Core implementation rules

- Query the current schema before using an unfamiliar field.
- Keep public IDs stable after release.
- Keep structured source or the compiler authoritative when one exists.
- Treat generated `project.json` as output, not a second editable master.
- Test requirements on both sides of the gate and through state transitions.
- Test the target Viewer, not only static data or the local runner.
- Treat web and local Viewer packages as separate release formats.
- Do not preserve a legacy workaround unless the problem reproduces in the target ICC Plus 2 version.

## Writing rule

Apply `unslop` to player-facing prose and documentation. Keep code, exact quotations, and verbatim evidence unchanged.