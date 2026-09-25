---
name: cyoa-migrate
description: Use when migrating legacy ICC projects to ICC Plus 2.
compatibility: Requires the legacy migration reference, a preserved source artifact, and access to the target ICC Plus 2 toolchain.
---

# CYOA migrate

Port player-visible behavior into current ICC Plus 2 without treating the old editor or its workarounds as the target design.

Apply the external Unslop prose skill only to text that is intentionally rewritten. Preserve legacy player text during a mechanical port unless rewriting is part of the request.

## Inputs

Load:

- an untouched copy of the old project and Viewer files,
- the legacy migration reference,
- representative old builds or expected behavior,
- the current ICC Plus 2 guide and toolchain.

## Workflow

1. Freeze the original artifact.
2. Identify the likely source editor or fork only as far as evidence allows.
3. Inventory rows, choices, points, requirements, groups, addons, buttons, custom code, CSS, IDs, and build formats.
4. Record representative old builds and expected behavior before migration.
5. Import or reconstruct the project through an ICC Plus 2-compatible path. Use `iccplus-local project hydrate` when supported sparse input is missing official Creator baseline fields.
6. Run `iccplus-local project validate` against the current target before treating the migrated project as complete.
7. Rebuild unsupported, ambiguous, or workaround-heavy mechanics through the current `iccplus-local` structure, rules, style, media, and build paths.
8. Preserve public IDs when compatibility requires it.
9. Re-run recorded builds and state-transition tests in the target Viewer.
10. Remove dead compatibility code and save a new ICC Plus 2 version.

## Rules

- Preserve player-visible behavior, not historical editor internals.
- Never migrate in place.
- Do not port a workaround without reproducing the old problem in the target Viewer.
- Treat custom JavaScript as a separate risk and determine what it does before replacing it.
- Old field presence is not evidence of current support.
- A project loading successfully does not prove behavioral compatibility.
- Stop using legacy guidance after migration.

## Output

Leave the untouched source, a new ICC Plus 2 project, the behavior inventory, the compatibility decisions, and the old-build regression results.

## Final checks

- [ ] Original artifact is preserved.
- [ ] Legacy behavior inventory exists.
- [ ] Representative old builds are recorded.
- [ ] Current ICC Plus 2 validation is clean or exceptions are documented.
- [ ] Workarounds were reproduced or removed.
- [ ] Public-ID compatibility was decided explicitly.
- [ ] Target Viewer tests match the intended old behavior.
- [ ] `references/migration-checklist.md` is complete.

## References

Read `../../docs/cyoa/legacy/legacy-icc-migration-reference.md` first. Use current `../../docs/cyoa/guide/` files for the target implementation.