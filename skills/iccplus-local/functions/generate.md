# generate

Read this file when creating a new ICC Plus project from scratch.

`generate` creates the exact blank ICC Plus 2.10.7 Creator project used as the clean starting point and verifies it with complete-project validation.

```bash
iccplus-local generate -o project.json
```

After generation, use the phase commands in this order as needed:

```text
structure -> rules -> style -> play
```

Do not hand-build a blank project JSON when `generate` can create the canonical base. A generated project always includes the official top-level sections and defaults expected by the Creator. For repeatable multi-phase builds from manifests, use `build` instead and read `build.md`.

See `../../../docs/BUILD_SYSTEM.md` and `PHASED_AUTHORING.md`.
