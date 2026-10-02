# build

Read this file for reproducible multi-phase builds.

`build` consumes an ordered manifest and produces a Creator-complete project. Use it when a project has an authoritative source tree or compiler pipeline. Generated project JSON remains output, not a second authoring source.

For large projects, keep two concerns separate:

- the readable semantic build used for authoring, review, and most tests;
- optional release normalization/compaction performed deterministically after the semantic build.

A normalization phase may centralize style, promote shared Requirements to Rows, prune runtime-only Groups with no consumers, merge safe Rows, or compact runtime IDs. Do not make those transformations by hand against the generated release file.

If runtime IDs are compacted, generate them deterministically, rewrite every reference-bearing field, emit a reversible mapping, validate the compact result, and prove that reverse mapping reproduces the semantic project. A different compact-ID mapping is a public-ID migration after release.

Do not strip Creator-complete eager/default fields merely to reduce bytes.

Read `../../../docs/cyoa/guide/21-large-project-normalization.md` before adding a large-project normalization phase.

See `../../../docs/BUILD_SYSTEM.md` and the current build manifest schema for exact command and phase shapes.
