# project

Read this file for project validation, hydration, formatting, export, fragmentation, serialization, IDs, and build strings.

Use `project validate` for final Creator-complete validation of an imported or externally supplied project. Use `project hydrate` to restore missing official baseline sections and safe Creator-eager fields without inventing missing identities or downgrading newer projects.

For source-driven large projects, distinguish three artifacts when useful:

- authoritative semantic source,
- readable semantic/test `project.json`,
- optional compact runtime release `project.json`.

Do not edit the compact release artifact as a second source.

## Runtime ID compaction

Compact runtime IDs can materially reduce repeated-reference payload in large projects, but only as a deterministic release transformation.

A safe compact-ID pipeline must:

- keep source/test IDs semantic and readable;
- generate stable deterministic runtime IDs rather than fresh random IDs;
- use explicit collision detection and stable collision handling;
- rewrite every identity and every reference-bearing field;
- emit a reversible semantic-to-runtime ID map for release/debug records;
- validate the compact artifact;
- reverse-map a comparison copy and compare it field-for-field with the semantic build;
- treat any later mapping/algorithm change as a public-ID migration when old saves or imports matter.

A short type prefix such as `r`, `c`, `a`, or `g` is useful for diagnosis but does not replace the reversible map.

Do not strip official Creator-complete eager/default fields only to reduce file size. Remaining schema overhead is preferable to a smaller project that the target Creator cannot round-trip safely.

Read `../../../docs/cyoa/guide/21-large-project-normalization.md` for the full release-compaction rules.
