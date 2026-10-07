# Release packaging

ICC Plus Local has a manual GitHub Actions release workflow at `.github/workflows/manual-release.yml`.

Run **Actions → Manual release → Run workflow**, enter the version/tag text you want to release, and choose whether the GitHub Release is a prerelease. The entered value is authoritative: the workflow writes it into `VERSION`, synchronizes the package/current-document version markers, verifies the release ZIPs, commits that version update to the selected branch, rebuilds the final archives from that commit, and creates the GitHub Release using the same entered text as the tag.

## Full distribution

`iccplus-local-full-VERSION.zip` is the normal source/tooling distribution. It contains the ICC Plus Local source, launchers, schemas, examples, verification material, all skills, and all documentation needed for planning, authoring, editing, testing, and release work.

The generated full archive deliberately excludes development-only test and CI trees:

- `tests/`
- `cli_tests/`
- `compression_tests/`
- `online_tests/`
- `.github/`
- caches and generated `build/` / `dist/` directories
- root `run-tests`, `run-compression-tests`, and `run-upstream-parity-tests` launchers, because their test trees are not shipped

The full archive explicitly marks `iccplus-local`, `cyoa-compress`, and `install.sh` executable so the release does not depend on Git file-mode metadata surviving the packaging path.

Tests remain in the Git repository and run before a manual release is created; they are simply not shipped in the end-user release ZIP.

## Viewer/test distribution

`iccplus-viewer-test-VERSION.zip` is a deliberately smaller player/runtime-testing environment. It contains only the runtime dependency closure required to evaluate an existing ICC Plus project plus the documentation and skill needed for Viewer-side testing.

The package includes:

- the simulator, project runtime index, Requirement engine, scenario runner, native Build Form parser, expression/JavaScript compatibility helpers, Viewer text helper, version module, and a minimal Viewer-test CLI;
- `skills/iccplus-viewer-test/SKILL.md`;
- Viewer/runtime coverage, play structure, gameplay runner, session/testing, visibility, parity, and blind-playtest documentation;
- a minimal `pyproject.toml` that installs only the `iccplus-viewer-test` command.

It deliberately excludes CYOA generation, editing, structure/rules/style operations, build manifests, Creator helpers, media/image tooling, packaging/export tooling, authoring skills, and other build-side source.

The release packager verifies this boundary before writing the ZIP. Repository tests also inspect the generated archives so an authoring module cannot silently leak into the Viewer/test distribution.

## Building locally

From the repository root:

```bash
python scripts/build_release_archives.py --output-dir release-dist --source-ref LOCAL
```

This creates:

```text
release-dist/iccplus-local-full-VERSION.zip
release-dist/iccplus-viewer-test-VERSION.zip
release-dist/SHA256SUMS.txt
```

The archives contain `RELEASE_MANIFEST.json` with the package kind, source version, source ref, and packaged file list.

## Version handling

Manual releases do not require the repository to be pre-bumped. The workflow input is the source of truth for that run.

`scripts/set_version.py VERSION` updates the canonical package metadata plus the small set of current docs that display the live tool version. Historical release-note headings and historical source notes are not rewritten.

Normal CI does not try to infer or police documentation placement. Its version-consistency test checks only the canonical runtime/package metadata. The main-branch release-artifact job uses the same full/viewer ZIP builder as the manual release workflow, so CI and GitHub Releases test the same package shapes.
