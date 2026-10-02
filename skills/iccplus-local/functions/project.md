# project

Read this file for project validation, hydration, formatting, export, fragmentation, serialization, IDs, and build strings.

Use `project validate` for final Creator-complete validation of an imported or externally supplied project. Use `project hydrate` to restore missing official baseline sections and safe Creator-eager fields without inventing missing identities or downgrading newer projects.

For source-driven large projects, distinguish three artifacts when useful:

- authoritative semantic source,
- readable Creator-complete semantic/test `project.json`,
- compact runtime release `project.json`.

Do not edit the compact release artifact as a second source.

## Runtime serialization

Player-facing runtime serialization omits every native value currently proven behavior-equivalent when absent in the pinned ICC Plus 2.10.7 Viewer. This is the default runtime policy, not an optional generic cleanup pass.

Creator Save-to-Disk and Creator-compatible exports remain Creator-complete. Runtime omission happens after the native authoring artifact has been validated. The serializer uses an explicit, version-pinned whitelist and conditional rules rather than treating schema-optional fields or Creator construction defaults as automatically removable.

Read `../../../docs/SPARSE_RUNTIME_SERIALIZATION.md` for the proven omission set. For unresolved cases, generate one-omission-at-a-time browser artifacts with `python -m iccplus_tools.omission_probe -o verification/sparse-omission`. Promote a new omission only after the candidate behaves like its baseline in the pinned Viewer; load success alone is insufficient.

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

Do not remove native fields from Creator-complete authoring artifacts merely for size. Runtime release payloads may omit only values covered by the pinned Viewer behavior-equivalence rules.

Read `../../../docs/COMPILER_BOUNDARY.md`, `../../../docs/SPARSE_RUNTIME_SERIALIZATION.md`, and `../../../docs/cyoa/guide/21-large-project-normalization.md` for the serialization/compiler boundary and release-compaction rules.
