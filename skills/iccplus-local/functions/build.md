# build

Read this file for reproducible multi-phase native ICC Plus builds.

`build` consumes an ordered manifest, produces and complete-validates a Creator-complete project in memory, then writes the normal sparse project form. Use it when a project has an authoritative source tree or compiler pipeline. Generated project JSON remains output, not a second authoring source.

ICC Plus Local executes the explicit native phases it is given. It does not decide how a higher-level semantic source should be normalized.

For source-driven projects, perform semantic normalization in the compiler before or while emitting the native build phases. Examples of compiler-owned decisions include Requirement hoisting, style deduplication, source-taxonomy Group pruning, Row merging, Pick N inference, and runtime-ID compaction.

If the compiler emits a compact release artifact, ICC Plus Local can validate that native result and run local regressions against it. The compiler remains responsible for deterministic ID generation, complete reference remapping, reversible mappings, and migration policy for published IDs.

Do not invent omission rules merely to reduce bytes. The normal save path may strip only fields covered by the pinned sparse serializer.

Read `../../../docs/COMPILER_BOUNDARY.md` and `../../../docs/cyoa/guide/21-large-project-normalization.md` when the surrounding compiler performs normalization or release compaction.

See `../../../docs/BUILD_SYSTEM.md` and the current build manifest schema for exact command and phase shapes.
