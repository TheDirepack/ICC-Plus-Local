# project

Read this file for project validation, hydration, formatting, export, fragmentation, serialization, IDs, and build strings.

Use `project validate` for final Creator-complete validation of an imported or externally supplied project. Use `project hydrate` to restore missing official baseline sections and safe Creator-eager fields without inventing missing identities or downgrading newer projects.

For source-driven large projects, distinguish three artifacts when useful:

- authoritative semantic source,
- readable semantic/test `project.json`,
- optional compact runtime release `project.json`.

Do not edit the compact release artifact as a second source.

## Runtime ID compaction boundary

ICC Plus Local owns native serialization and reference validation. It does not choose a compact ID scheme or infer which public identities are safe to replace.

If a source compiler or release pipeline compacts runtime IDs, that layer must:

- keep source/test IDs semantic and readable;
- generate stable deterministic runtime IDs rather than fresh random IDs;
- use explicit collision detection and stable collision handling;
- rewrite every identity and every reference-bearing field;
- emit a reversible semantic-to-runtime ID map for release/debug records;
- treat later mapping or algorithm changes as public-ID migrations when old saves or imports matter.

After that transformation, use ICC Plus Local to validate the compact native artifact, exercise relevant runtime/save-load paths, and inspect references. Reverse-mapped semantic equivalence is a compiler/release-pipeline proof, not a hidden `project` rewrite.

Do not strip official Creator-complete eager/default fields only to reduce file size. Remaining schema overhead is preferable to a smaller project that the target Creator cannot round-trip safely.

Read `../../../docs/COMPILER_BOUNDARY.md` and `../../../docs/cyoa/guide/21-large-project-normalization.md` for the source-compiler boundary and release-compaction rules.
