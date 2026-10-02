# style

Read this file before changing templates, widths, images, fonts, colors, backgrounds, borders, card geometry, responsive presentation, or Design Groups in a native ICC Plus project.

Use `style` for explicit presentation changes. Keep structure in `structure` and gameplay logic in `rules`.

## Native style hierarchy

When directly authoring native ICC Plus styling, use the broadest correct native scope:

1. project-wide styling for the ordinary baseline,
2. official Row/Choice Design Groups for reusable visual exceptions,
3. private Row styling for a true one-Row exception,
4. private Choice styling for a true one-Choice exception,
5. custom CSS only when native ICC Plus styling cannot express the treatment.

When an ordinary ICC Plus Group already represents a family that should share a treatment, `Group.designGroups` can carry Design Group inheritance. Direct per-entity Design Group assignment is also valid when membership is intentionally explicit.

ICC Plus Local applies and validates the native styling operations it is given. It should not automatically decide that repeated private styles are semantically equivalent, create Design Groups from repetition, rewrite Group membership, or remove direct assignments to reduce project size.

For source-driven projects, deduplicating repeated style intent belongs in the source compiler. The compiler may choose project scope, Design Groups, Group-linked inheritance, or explicit exceptions and then emit the resulting native styling operations.

Local validation does not prove browser rendering. Use the official Viewer for final layout, responsive behavior, overlays, image composition, and CSS.

Read `../../../docs/COMPILER_BOUNDARY.md`, `../../../docs/cyoa/guide/16-visual-design-and-responsive-layout.md`, and `../../../docs/cyoa/guide/21-large-project-normalization.md` for the ownership boundary and broader design guidance.
