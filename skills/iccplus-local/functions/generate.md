# generate

Read this file when creating a new ICC Plus project from scratch.

`generate` creates the exact blank ICC Plus Creator project used as the clean starting point.

```bash
iccplus-local generate -o project.json
```

After generation, use the phase commands in this order as needed:

```text
structure -> rules -> style -> play
```

Do not hand-build a blank project JSON when `generate` can create the canonical base. For repeatable multi-phase builds from manifests, use `build` instead and read `build.md`.

See `../../../docs/BUILD_SYSTEM.md` and `PHASED_AUTHORING.md`.
