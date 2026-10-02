## 0.10.0rc15

- Made sparse `project.json` the normal authoring representation across generation, phased edits, low-level apply, hydration, formatting, exports, and Viewer packaging. Use `--not-sparse` / `--not_sparse` only when a materialized full-project artifact is specifically required.
- Fixed sparse authoring round trips by retaining Score `idx` as stable authoring identity. The Viewer can generate an internal substitute, but ICC Plus Local hydration deliberately does not invent missing entity identities.
- Retained Sound Effect `name` because it is a non-derivable authoring label even though the pinned Viewer does not use it for playback.
- Tightened sparse-serialization documentation and tests so future Viewer-safe omissions must also preserve the state needed by later ICC Plus Local commands.
- Refreshed the README, CYOA guide, ICC Plus Local skill, project function guide, package manifest, and release metadata for rc15.
- Kept the ICC Plus target at 2.10.7 and pinned upstream source commit `1ea9db888cde2286d18d0d5de50933cb8773b739`.
- GitHub Actions remains the authoritative release gate for core runtime/validation, CLI contract, and checked-in examples.

## 0.10.0rc14

- Introduced sparse normal project saves after complete in-memory hydration and validation.
- Unified `generate`, `build`, `structure`, `rules`, `style`, `apply`, formatting, export, and Viewer packaging around the pinned sparse serializer.
- Split normal sparse compatibility validation from explicit Creator-complete validation.
- Added the standalone `iccplus-sparse` serializer and `iccplus-omission-probe` verification generator.
- Made compiler/native ownership boundaries explicit and added Row-semantic regressions.
- Split CI into core, CLI-contract, and checked-in-example jobs.

## 0.10.0rc13

- Added the compressed high-level CYOA skill set and retained `iccplus-local` as the single native ICC Plus 2 implementation skill.
- Added the complete current CYOA guide and legacy migration reference under `docs/cyoa/`.
- Refreshed current documentation for the ICC Plus 2.10.7 command model.

## Earlier releases

Detailed historical implementation and browser-audit evidence for rc12 and earlier is retained in repository history and the versioned/historical audit documents under `docs/`. Current operating instructions live in the unversioned documentation and skills.
