---
name: cyoa-develop
description: Use when coordinating multi-pass or multi-session CYOA work.
compatibility: Designed for long-running ICC Plus 2 projects with a persistent working-state file and the CYOA task-skill set.
---

# CYOA develop

Coordinate a long project across the reduced CYOA skill set. Keep one current working state and route each bounded pass to the skill, compiler, or ICC Plus Local function that owns it.

Apply the external Unslop skill to non-code written output.

## Working state

Keep a short state record with the current checkpoint, premise, non-goals, player contract, invariants, source boundary, completed work, unresolved issues, tests, and next bounded queue.

For compiler-driven projects, also record the artifact boundary: authoritative semantic source, readable semantic/test build, and any normalized or compact release artifact. Never let the compact release file become a second source of truth.

## Workflow

1. Load or rebuild the current working state.
2. Identify the smallest coherent pass that moves the project forward.
3. Separate design questions from implementation work.
4. Preserve the authoritative source boundary. Generated output is not a second authoring source.
5. Route design work to `cyoa-plan`; source lowering and normalization to the project compiler; native ICC Plus 2 implementation, direct editing, styling, media, validation, serialization, and local testing to `iccplus-local`; design/content audits to `cyoa-review`; legacy conversion to `cyoa-migrate`; and final delivery checks to `cyoa-ship`. Use `cyoa-compress` only for an explicit exceptional external-asset pass.
6. Calibrate a representative sample before a large batch.
7. Run the selected compiler, skill, or ICC Plus Local checks.
8. Run a small global check for project invariants the pass could have affected.
9. Update additions, edits, removals, tests, unresolved issues, and the next work queue.
10. Save a coherent artifact checkpoint that agrees with the working state.

## Large-project normalization passes

When a source-driven project has become structurally repetitive or the generated JSON is unnecessarily large, use a separate compiler normalization pass. Read `../../docs/COMPILER_BOUNDARY.md` and `../../docs/cyoa/guide/21-large-project-normalization.md` first.

Compiler-owned candidates include:

- consolidating repeated ordinary styling into project scope and reusable Design Groups;
- using Group-linked Design Group inheritance instead of repeated direct style assignments;
- moving shared visibility Requirements to the deepest sufficient owning Row when the source graph proves equivalence;
- removing redundant ancestor gates from descendants when implication is proved by the source model;
- emitting real Row selection maxima for source-level Pick 1 / Pick N semantics;
- merging safe one-card Rows without mixing independent axes;
- omitting runtime Groups that have no runtime consumer while retaining useful source metadata;
- optionally compacting runtime IDs deterministically as a release transformation with complete remapping and a reversible map.

ICC Plus Local should validate and simulate the native output of those transformations. It should not infer or perform them on arbitrary projects.

Normalize one layer at a time and measure both behavioral regressions and artifact size. Do not combine a large content rewrite with a large mechanical normalization pass unless the changes cannot be separated.

## Rules

- Prefer bounded passes over broad mixed work.
- Preserve useful prior work during cleanup.
- Keep confirmed facts, evidence-supported inference, design choices, and unknowns distinguishable.
- Audit generated sets for duplicate roles, cost drift, repeated prose, missing niches, and filler.
- Test requirement networks for reachability, not only individual gates.
- Test effective gating at Row + Choice scope rather than assuming every child must physically carry the same Requirement.
- Treat visibility, legality, and provider-loss cleanup as separate mechanics.
- Keep local and global checks separate.
- Record removals and structural remaps such as merged Rows.
- Discover current tool capabilities at run time.
- Do not carry validation status across project, compiler, or tool revisions.
- Keep reusable generators, validators, and test helpers under `/CYOA/tools/`; keep revision folders focused on project source, inputs, outputs, and reports.

## Output

After each pass, leave the updated artifact checkpoint, updated working state, checks run, unresolved items, and the next bounded work queue.

## Final checks

- [ ] Current working state was loaded or rebuilt.
- [ ] One bounded pass was defined.
- [ ] The authoritative source boundary remained clear.
- [ ] The compiler, task skill, or ICC Plus Local function that owns the work was used.
- [ ] Representative work was calibrated before scaling.
- [ ] Local checks passed or failures are recorded.
- [ ] Relevant global invariants were checked.
- [ ] Additions, edits, removals, and unresolved items are recorded.
- [ ] Normalized release artifacts remain reproducible from semantic source when used.
- [ ] ICC Plus Local validated the generated native project without being made responsible for source-level normalization decisions.
- [ ] Working state and artifact checkpoint agree.
- [ ] `references/develop-checklist.md` is complete.

## References

Use `../../docs/cyoa/guide/03-development-protocol.md` for long-project rules, `../../docs/COMPILER_BOUNDARY.md` for ownership boundaries, and `../../docs/cyoa/guide/21-large-project-normalization.md` for compiler/build normalization and release compaction. For native ICC Plus 2 implementation, editing, styling, validation, serialization, and local testing, use `iccplus-local` and the matching function guides.
