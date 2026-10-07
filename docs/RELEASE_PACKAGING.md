# Release packaging

ICC Plus Local has a manual GitHub Actions release workflow at `.github/workflows/manual-release.yml`.

Run **Actions → Manual release → Run workflow**, supply the Git tag matching the repository `VERSION` value with a `v` prefix (for example, `VERSION=0.10.0rc16` requires `v0.10.0rc16`), and choose whether the GitHub Release is a prerelease. The workflow runs the maintained test suite and examples, builds both release ZIPs, writes SHA-256 checksums, stores the files as a workflow artifact, and creates the GitHub Release with the same files attached.

## Full distribution

`iccplus-local-full-VERSION.zip` is the normal source/tooling distribution. It contains the ICC Plus Local source, launchers, schemas, examples, verification material, all skills, and all documentation needed for planning, authoring, editing, testing, and release work.

The generated full archive deliberately excludes development-only test and CI trees:

- `tests/`
- `cli_tests/`
- `compression_tests/`
- `online_tests/`
- `.github/`
- caches and generated `build/` / `dist/` directories

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
