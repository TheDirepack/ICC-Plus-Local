# Authoring workflow for an LLM

Build in passes. Each pass should leave a project that can be checked.

## Pass 0. Establish working state

Read `03-development-protocol.md`.

Record the current project version, player contract, section map, mechanical invariants, source boundaries, open decisions, and current test matrix. For a source-based CYOA, also keep a source ledger.

Do not begin a large generation pass from chat memory alone.

## Source and tool boundary

When a project has structured source or a compiler, that source is authoritative. Generated `project.json` is a build product. Do not hand-edit it and then try to remember the change later. Fix the source or compiler and rebuild.

Keep reusable generation, validation, conversion, and test helpers under `/CYOA/tools/`. Revision folders should contain project source, inputs, outputs, checkpoints, and reports, not private copies of reusable tooling.

At the compile and release boundary, keep an explicit separation between authoring metadata and player content. Do not export debug controls, source-only template fields, placeholder labels, or schema defaults as visible prose merely because they exist in the source model.

## Pass 1. Plan

Use the design sequence in:

- `05-planning-a-cyoa.md`,
- `06-planning-templates.md`,
- `07-formats-and-rule-systems.md`,
- `08-structure-and-player-flow.md`,
- `09-writing-choices-and-content.md`,
- `10-research-ideation-and-images.md`,
- `11-balance-and-playtesting.md`.

Produce:

- Player contract.
- Premise focus and non-goals.
- Chosen format and rules.
- Section map.
- Economy.
- State model.
- ID policy.
- Content coverage notes.
- Sample builds.
- Major test cases.

Do not create hundreds of Choices before this pass is coherent.

## Pass 2. Create the mechanical skeleton

Create dependencies before objects that reference them.

A safe general order is:

1. Point Types.
2. Variables and Words.
3. Groups and Design Groups.
4. Global Requirements.
5. Rows.
6. Choices.
7. Scores and Addons.
8. Requirements and actions.

Use the current ICC Plus 2 schema for exact field shapes. The exact order can change when the project has no dependency between two categories.

Match Creator identity semantics while building the skeleton. Ordinary Requirements and non-selectable Addons keep structural blank IDs. Scores use `idx`; selectable Addons and normal top-level entities use real identities.

Use short placeholders where content is not ready. A complete skeleton is more useful than one polished section followed by missing structure.

## Pass 3. Prove one vertical slice

Before cloning the structure across the whole project, finish one representative section.

Test its:

- Selection.
- Deselection.
- Points.
- Requirements.
- Addons.
- Multi-select behavior if used.
- The actual repeat mode, including malformed no-mode rejection, zero crossing, and Row-cap displacement.
- Save and load if relevant.
- Reset behavior when `initValue`, `isAutoActive`, or `notDeselectedByClean` is used.
- Phone layout.
- Longest likely card.

Fix the pattern now. A bad template multiplied by eighty Choices is expensive to repair.

## Pass 4. Fill the project in coherent sections

Create one section or mechanic family at a time.

Use the section plan and content inventory rather than inventing the section again from scratch. Calibrate a few representative choices before generating the whole set.

After each coherent batch:

- Read the phase validation receipt or run the current read-only inspection needed for the batch.
- Evaluate new gates with passing and failing states.
- Open the project in the target Viewer when runtime behavior changed.
- Compare new choices against their closest existing competitors.
- Check names, costs, units, IDs, and terminology against the project glossary.
- Save a versioned checkpoint.
- Update the working-state notes.

Do not wait until the whole project is complete for the first runtime test.

## Pass 5. Finalize text

Replace placeholder text after the rules stop moving quickly.

Apply `unslop` to player-facing prose. Check mechanical wording separately from flavor text.

Run a set-level prose audit. Look for repeated openings, duplicated benefits, inconsistent terms, accidental power inflation, and descriptions that promise more than the mechanics provide.

## Pass 6. Add final media and styling

Use `10-research-ideation-and-images.md` and `16-visual-design-and-responsive-layout.md`.

Add final art, fonts, Row design, card design, and custom CSS. Current local or embedded image assignment handles compression automatically when appropriate. Test with the real longest cards, not only short examples.

Keep source and credit information for assets when it matters to the release.

## Pass 7. Run full builds

Play several full archetypes from the top of the CYOA to the end.

This finds issues that isolated section tests miss, such as point shortages, forgotten prerequisites, late backtracking, dead sections, hidden unlocks, and summary problems.

For large point-buy projects, run a wider build sweep after the first balance pass.

## Pass 8. Run a global consistency audit

After local sections work, inspect the project globally.

Check:

- every planned section exists,
- every required player goal has at least one route,
- no stale placeholder remains,
- public IDs are unique and stable,
- currencies and units use one naming scheme,
- repeated concepts use the same rule wording,
- hidden content has the intended discoverability,
- major early choices pay off later when promised,
- sources and original additions are distinguishable where relevant.

## Pass 9. Review

Use the `cyoa-review` skill.

Review rule clarity, section order, choice quality, economy, exploits, discoverability, mobile layout, accessibility, save behavior, and release readiness.

## Pass 10. Package and ship

Use `19-publishing-and-release.md` and the `cyoa-ship` skill.

Test the generated release package, then test the final hosted URL for web releases. If a static edition is part of the release, test it separately.