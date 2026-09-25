# build

Read this file when rebuilding a project from a repeatable ordered build manifest.

`build` starts from the exact blank project and applies the declared phases in order. The final output validates before write.

```bash
iccplus-local build iccplus.build.json -o project.json
```

Use `build` when the project should be reproducible from source manifests or when several authoring phases must run in a controlled order. Do not use it as a substitute for a simple one-off edit to an existing project.

Keep build inputs under source control or in the authoritative project source. Treat the built `project.json` as an output when the project is manifest-driven.

See `../../../docs/BUILD_SYSTEM.md`, `PHASED_AUTHORING.md`, and `AUTHORING_SCRIPTS.md`.
