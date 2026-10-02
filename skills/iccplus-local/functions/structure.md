# structure

Read this file before adding, moving, merging, cloning, ordering, or removing Rows, Choices, or Addons.

Use `structure` for entity shape and placement. Put gameplay logic in `rules` and presentation in `style`.

For source-driven large projects, optimize hierarchy before adding more entities:

- A hidden Row already hides its contained Choices. Prefer the deepest Row gate that fully owns a branch instead of copying ancestor navigation conditions through every descendant.
- Merge a one-card Row into a compatible neighboring Row when it has no distinct gate, instructions, selection limit, result/group/button role, or layout reason to remain separate.
- Do not merge independent axes when they need different Row limits or different visibility.
- Keep parent/provider decisions before genuine dependents. Remove dependencies that merely encode taxonomy when the selected trait itself establishes the capability.
- Preserve semantic source identities across layout changes. If a compiler merges physical Rows, keep a source-owned merge/remap table so tests can follow the semantic owner.

Before a Row merge, compare Requirements, `allowedChoices`, info/result/button flags, result/group behavior, template/width, styling, generated detail Rows, and player-facing header text.

Read `../../../docs/cyoa/guide/21-large-project-normalization.md` for the normalization checklist.
