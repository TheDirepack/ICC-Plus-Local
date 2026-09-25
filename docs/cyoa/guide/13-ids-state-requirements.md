# ICC Plus 2 IDs, state, and Requirements

## IDs

IDs are references. Treat them as part of the project's data contract.

Not every field named `id` is a project identity. In the ICC Plus 2.10.7 Creator, ordinary Requirements and non-selectable Addons use structural `id: ""` values. Scores use `idx` as identity while Score `id` points to a Point Type. Do not manufacture global IDs for structural blank records.

Generated IDs are valid. Semantic IDs are easier to audit in large projects and easier to use in migration or debugging.

Good IDs are short, unique, stable, and tied to meaning rather than order.

Examples:

- `row_powers`
- `power_blink`
- `point_energy`
- `var_gate_open`
- `req_archive_access`

Do not rename public IDs casually after release. Saved builds, Choice Import data, Requirements, Groups, and external tools may refer to them.

## Requirements

Write the intended rule in plain language before encoding it.

Example:

> Show the archive Row when the player has Scholar or has at least 5 Reputation.

Then translate that rule using requirement types from the current ICC Plus 2 schema.

This reduces mistakes caused by building the condition backward from field names.

## Requirement placement

A Row Requirement, Choice Requirement, Addon Requirement, and Score Requirement affect different behavior. Put the gate on the thing it is meant to control.

Do not gate an entire Row because one Choice inside it has a prerequisite.

## Global Requirements

Use a Global Requirement when the same rule appears in several places or when giving the rule a name makes the project easier to audit.

Current ICC Plus 2 allows Global Requirements to reference other Global Requirements.

Keep dependency chains short. A reusable rule should simplify understanding, not turn one condition into five layers of indirection.

## Hidden is not the same as unavailable

Decide whether unmet content should be absent from the player view or visible but unavailable. These are different player experiences and must be tested separately.

For content that must be hidden, test that it is absent from the player-visible surface before the requirement passes and appears at the intended transition. For content that should stay visible, test that the card remains visible and that selection is rejected or disabled as intended.

Do not infer hiding from unselectability or unselectability from hiding. ICC Plus 2 can apply hide behavior per requirement, and several requirements do not become one block unless their configured logic makes them one.

A hidden selected or forced state can still matter internally. Test the transition that created it and the transition that removes its provider. Do not use authoring-side visibility of hidden IDs as evidence of what the player can see.

## Variables

Use Variables for state that supported actions change and supported Requirements read.

Good examples include a mode toggled by a Button, a story flag, a state that is not naturally represented by a selected Choice, or a persistent switch used by several later conditions.

Do not create a Variable merely to mirror every Choice selection. The Choice already represents that state.

## Words

Use Words when text must be reused or changed dynamically. Keep the Word ID semantic and document what action can change it.

## State transition tests

Source-compatible Requirement evaluation has a few non-obvious cases. `selFromGroups` counts the same active Choice once for each requested Group it belongs to. `/ON#` count suffixes use JavaScript numeric-prefix parsing. Point-comparison priority 0 is valid. Preserve these rules in local tests and migrations.

A condition may work in a static evaluator and still fail during transitions.

Test these when relevant:

- Select the prerequisite, then select the dependent Choice.
- Deselect the prerequisite while the dependent Choice is active.
- Gain the prerequisite through a Button or forced action.
- Lose it through a Button or forced action.
- Save in one state and load the build.
- Change a multi-select count across the requirement boundary.
- Reset after changing points and selections, then confirm `initValue`, `isAutoActive`, and simple `notDeselectedByClean` replay.

## ID renames

Treat an ID rename as a migration.

Use tool support that rewrites references when its scope matches the project. For manual work, update all references in one coherent revision, validate, and test an imported or saved build if that ID is part of a public build format.