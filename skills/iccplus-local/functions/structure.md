# structure

Read this file before explicitly adding, moving, merging, cloning, ordering, or removing Rows, Choices, or Addons in a native ICC Plus project.

Use `structure` for requested entity shape and placement. Put gameplay logic in `rules` and presentation in `style`.

ICC Plus Local should not inspect an arbitrary project and decide that Rows ought to be merged, ancestor gates ought to disappear, taxonomy dependencies ought to be removed, or semantic identities ought to be remapped. Those are source/compiler decisions because they require knowledge of author intent beyond the native JSON shape.

For source-driven projects:

- perform hierarchy normalization in the source compiler;
- preserve semantic ownership/remap data in source when physical Rows change;
- emit the intended native Row/Choice/Addon structure;
- then use ICC Plus Local `structure` only for explicit native edits or compiler-emitted operations.

When an explicit Row merge is requested, compare Requirements, `allowedChoices`, info/result/button flags, result/group behavior, template/width, styling, generated detail Rows, and player-facing header text before applying it. Do not infer the merge merely because a Row contains one card.

Read `../../../docs/COMPILER_BOUNDARY.md` for the ownership boundary and `../../../docs/cyoa/guide/21-large-project-normalization.md` for compiler-side normalization rules.
