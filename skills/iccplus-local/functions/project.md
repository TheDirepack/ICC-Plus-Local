# project

Read this file for project validation, hydration, formatting, export, fragmentation, serialization, IDs, and build strings.

Use `project validate` for the normal sparse saved-project check. Add `--complete` for explicit Creator-complete validation. Use `project hydrate` to materialize missing official baseline sections and safe Creator-eager fields in memory without inventing missing identities or downgrading newer projects. Its saved JSON is still sparse unless `--not-sparse` is supplied.

For source-driven large projects, distinguish three artifacts when useful:

- authoritative semantic source,
- readable sparse semantic/test `project.json`,
- compact runtime release `project.json`.

Do not edit the compact release artifact as a second source.

## Runtime serialization

Player-facing runtime serialization omits native values proven behavior-equivalent when absent in the pinned ICC Plus 2.10.7 Viewer. This is the default runtime policy. Normal saved project JSON uses the same sparse serializer, but it also has to remain safe for later authoring commands and hydration.

All saved full-project JSON and Viewer payloads use sparse serialization after the native project has been hydrated and complete-validated in memory. Formatting, `project hydrate`, separate-image exports, and Viewer packages do not bypass this rule; only `--not-sparse` does. The serializer uses an explicit, version-pinned whitelist and conditional rules rather than treating schema-optional fields or Creator construction defaults as automatically removable.

Canonical sparse project saves must round-trip back to a Creator-complete authoring form without inventing stable identities or non-derivable authoring values. Keep Score `idx` and Sound Effect `name` in sparse project JSON even though the pinned Viewer does not need their serialized values for player behavior. Score `idx` is the stable authoring identity used across commands, and Sound Effect `name` is an authoring label that hydration cannot reconstruct.

Read `../../../docs/SPARSE_RUNTIME_SERIALIZATION.md` for the proven omission set. For unresolved cases, generate one-omission-at-a-time browser artifacts with `python -m iccplus_tools.omission_probe -o verification/sparse-omission`. Promote a new omission only after the candidate behaves like its baseline in the pinned Viewer and remains compatible with the authoring-round-trip contract. Load success alone is insufficient.

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

Do not add new omissions merely for size. Normal saved and runtime payloads may omit only values covered by the pinned Viewer behavior-equivalence rules and, for editable project JSON, the authoring-round-trip invariant. Materialized fields are retained only when the producing command explicitly uses `--not-sparse`.

Read `../../../docs/COMPILER_BOUNDARY.md`, `../../../docs/SPARSE_RUNTIME_SERIALIZATION.md`, and `../../../docs/cyoa/guide/21-large-project-normalization.md` for the serialization/compiler boundary and release-compaction rules.
