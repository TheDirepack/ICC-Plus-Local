---
name: cyoa-develop
description: Use when coordinating multi-pass or multi-session CYOA work.
compatibility: Designed for long-running ICC Plus 2 projects with a persistent working-state file and the CYOA task-skill set.
---

# CYOA develop

Coordinate a long project across the reduced CYOA skill set. Keep one current working state and route each bounded pass to the skill or ICC Plus Local function that owns it.

Apply the external Unslop skill to non-code written output.

## Working state

Keep a short state record with the current checkpoint, premise, non-goals, player contract, invariants, source boundary, completed work, unresolved issues, tests, and next bounded queue.

## Workflow

1. Load or rebuild the current working state.
2. Identify the smallest coherent pass that moves the project forward.
3. Separate design questions from implementation work.
4. Preserve the authoritative source boundary. Generated output is not a second authoring source.
5. Route design work to `cyoa-plan`, native ICC Plus 2 implementation, editing, styling, media, validation, and local testing to `iccplus-local`, design/content audits to `cyoa-review`, legacy conversion to `cyoa-migrate`, and final delivery checks to `cyoa-ship`. Use `cyoa-compress` only for an explicit exceptional external-asset pass.
6. Calibrate a representative sample before a large batch.
7. Run the selected skill or ICC Plus Local function checks.
8. Run a small global check for project invariants the pass could have affected.
9. Update additions, edits, removals, tests, unresolved issues, and the next work queue.
10. Save a coherent artifact checkpoint that agrees with the working state.

## Rules

- Prefer bounded passes over broad mixed work.
- Preserve useful prior work during cleanup.
- Keep confirmed facts, evidence-supported inference, design choices, and unknowns distinguishable.
- Audit generated sets for duplicate roles, cost drift, repeated prose, missing niches, and filler.
- Test requirement networks for reachability, not only individual gates.
- Keep local and global checks separate.
- Record removals.
- Discover current tool capabilities at run time.
- Do not carry validation status across project or tool revisions.
- Keep reusable generators, validators, and test helpers under `/CYOA/tools/`; keep revision folders focused on project source, inputs, outputs, and reports.

## Output

After each pass, leave the updated artifact checkpoint, updated working state, checks run, unresolved items, and the next bounded work queue.

## Final checks

- [ ] Current working state was loaded or rebuilt.
- [ ] One bounded pass was defined.
- [ ] The authoritative source boundary remained clear.
- [ ] The appropriate task skill owned the work.
- [ ] Representative work was calibrated before scaling.
- [ ] Local checks passed or failures are recorded.
- [ ] Relevant global invariants were checked.
- [ ] Additions, edits, removals, and unresolved items are recorded.
- [ ] Working state and artifact checkpoint agree.
- [ ] `references/develop-checklist.md` is complete.

## References

Use `../../docs/cyoa/guide/03-development-protocol.md` for long-project rules. For native ICC Plus 2 implementation, editing, styling, validation, and local testing, use `iccplus-local` and the matching function guides.