---
name: cyoa-ship
description: Use when packaging and final-QA testing ICC Plus 2 releases.
compatibility: Requires the validated project, the target official ICC Plus 2 Viewer or template, and release assets.
---

# CYOA ship

Test the exact package players will receive. Do not treat Creator preview or a development project file as release proof.

## Inputs

Load:

- the validated project revision,
- the intended official Viewer release or template,
- release assets and credits,
- current test and review status,
- the target delivery format and canonical URL when applicable.

## Workflow

1. Rebuild from authoritative source when applicable, run `iccplus-local project validate`, and confirm required runtime tests, design review, and accessibility checks are complete.
2. Choose the exact web, offline, or static release format.
3. Build from the official ICC Plus Viewer release or template that matches the project target. The current rc12 tool target is ICC Plus 2.10.7.
4. Test the generated package itself.
5. For web releases, stage through HTTP and then test the final hosted URL.
6. For offline releases, test the package exactly as delivered.
7. Test a static edition separately and expose interaction-dependent information in a readable static form.
8. Check final asset sources and credits where needed.
9. Record the project, Viewer, local tool, and engine-source versions actually used.
10. Complete the release checklist.

## Rules

- Web and offline Viewer packages are different release formats.
- Use official ICC Plus 2 templates.
- Do not hand-edit generated `project.json` to fix release content. Change the source and rebuild. Limit release-path changes to deliberate packaging operations that are tested.
- Treat the canonical URL as part of saved-player state when the Viewer does.
- Do not assume schema drift is safe.
- Prefer native project styling and Design Groups over private duplication; prefer project CSS over Viewer patches when CSS is actually needed.
- Check network errors at the final hosted origin.
- Protect public IDs.
- Treat static output as its own release target.

## Output

Produce the tested release package plus a release record containing versions, checks run, known exceptions, asset-credit status, and the canonical URL when applicable.

## Final checks

- [ ] Correct official Viewer format was built.
- [ ] Generated package was tested.
- [ ] Final hosted URL was tested for web releases.
- [ ] Build save and load was tested at the canonical URL when enabled.
- [ ] Accessibility smoke checks pass in the release package.
- [ ] Static edition was tested separately when one exists.
- [ ] Asset source or credit requirements are satisfied.
- [ ] Project, Viewer, local CLI, and engine-source versions are recorded.
- [ ] `references/ship-checklist.md` is complete.

## References

Use `../../docs/cyoa/guide/19-publishing-and-release.md`, `20-troubleshooting.md`, `02-creator-and-viewer.md`, and `10-research-ideation-and-images.md` as needed.