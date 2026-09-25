# ICC Plus 2 Rows, Choices, and Addons

## Rows

Use a Row for a coherent section of content. A Row can be a choice section, information section, result section, button section, or another supported presentation depending on its configuration.

A Row should usually answer one player-facing question. If the Row contains unrelated decisions only because they fit the same visual grid, split it.

Useful Row-level decisions include:

- Whether the Row is always visible or gated.
- Allowed selections.
- Choices Per Row.
- Image template.
- Result or group behavior.
- Button behavior.
- Design and Design Group membership.

Query the current schema for exact fields.

## Choices

A Choice is the main selectable unit.

Plan these before creation:

- ID.
- Name and text.
- Cost or Scores.
- Selection behavior.
- Multi-select behavior when used.
- Requirements.
- Groups.
- Addons.
- Functions and actions.
- Design overrides only when needed.

Keep the core meaning of the Choice in one place. Do not make the player combine a title, hidden tooltip, and distant rule note to learn what selecting it does.

## Addons

Use Addons for content that belongs to a parent Choice.

Good uses include upgrades, sub-options, attached details, alternate images, or small related selections.

Do not use Addons to hide an entire second CYOA inside every Choice. If the sub-options become large enough to need their own navigation and economy, a separate Row may be clearer.

Current ICC Plus 2 supports selectable Addons and newer Addon layout and CSS behavior. Query the target schema before choosing the implementation.

A non-selectable Addon is a structural child and the Creator normally leaves its `id` blank. A selectable Addon has a real identity. Selecting an Addon can internally activate an `isNotSelectable` parent even though the player cannot click that parent directly. Parent cleanup can occur through `deselectParent` or `deselectWhenNoAddon`.

## Multi-select Choices

Use multiple selection when quantity is the decision.

In ICC Plus 2.10.7, `isSelectableMultiple` alone does not define a working quantity mechanic. Use one of the real repeat modes. `isMultipleUseVariable` gives a signed variable count. `multipleScoreId` gives a Point Type-backed count. If neither is present, the Viewer counter action is a no-op.

Plan:

- Minimum and maximum count.
- Whether the first selection can happen by clicking.
- Slider or counter behavior when supported.
- Score multiplication.
- Discount interaction.
- Requirement behavior as the count changes.
- Save and load behavior.

Test increasing and decreasing the count. A mechanic that works only while adding selections is not complete.

When `multiplyByTimes` is used, verify the marginal repeat cost or score at each step, including the expected 1x, 2x, 3x progression and refunds on decrement.

Test crossing zero when negative counts are allowed. Test Row-cap displacement of a positive repeat count. If the Choice changes `allowedChoices`, verify that the change runs on every increment and decrement. Do not assume ordinary point multiply/divide/set effects run on repeat steps; the Viewer does not execute them there.

## Result and selected-choice Rows

Use result-style Rows when the player benefits from seeing selected content in a new context. This can work for summaries, loadouts, teams, or final builds.

Do not duplicate the entire page just to create a summary. Show the information needed to review the build.

## Groups

Rows and Choices can participate in Groups for supported group-aware behavior. Use a Group when the engine operation genuinely acts on a set. Do not use Groups only as author-side folders unless the feature needs them.

## Layout overrides

ICC Plus 2 can change image template and Choices Per Row at multiple scopes. Prefer a small number of clear layout rules.

A project where every Choice overrides its Row becomes harder to maintain and harder for an LLM to reason about.