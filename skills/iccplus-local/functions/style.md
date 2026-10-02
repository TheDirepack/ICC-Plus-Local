# style

Read this file before changing templates, widths, images, fonts, colors, backgrounds, borders, card geometry, responsive presentation, or Design Groups.

Use `style` for presentation. Keep structure in `structure` and gameplay logic in `rules`.

## Native style hierarchy

Use the broadest native scope that fits:

1. project-wide styling for the ordinary baseline,
2. official Row/Choice Design Groups for reusable visual exceptions,
3. private Row styling for a true one-Row exception,
4. private Choice styling for a true one-Choice exception,
5. custom CSS only when native ICC Plus styling cannot express the treatment.

Do not copy the project style into every Row or Choice. Do not copy a complete project style object into every Design Group; store only the properties that group overrides.

When an ordinary ICC Plus Group already represents the semantic family that should share a treatment, link the Design Group through `Group.designGroups` instead of repeating the Design Group ID on every member. The target Viewer can inherit styling through ordinary Group membership, which keeps source intent and runtime JSON smaller.

Direct per-entity Design Group assignment is still appropriate when membership is genuinely explicit and no semantic Group represents the family. It should not be the default for thousands of entities.

Use project styling for normal cards and Rows even when a compiler could cheaply stamp equivalent private styles. Repeated private styles make the project larger and harder to audit.

## Large-project visual normalization

Before a large style migration:

- inventory project styling, Row/Choice Design Groups, ordinary Groups, direct design assignments, private styles, and custom CSS;
- identify the baseline treatment that can move to project styling;
- identify true exception families and give each one a reusable Design Group;
- prefer Group-linked inheritance for semantic families;
- keep private styling only where the visual treatment is intentionally unique;
- rebuild and compare player-visible states, including selected and unmet states.

Local validation does not prove browser rendering. Use the official Viewer for final layout, responsive behavior, overlays, image composition, and CSS.

Read `../../../docs/cyoa/guide/16-visual-design-and-responsive-layout.md` and `../../../docs/cyoa/guide/21-large-project-normalization.md` for the broader design and normalization rules.
