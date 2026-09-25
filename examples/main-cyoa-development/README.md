# Main CYOA development excerpt

This is a standalone excerpt derived from the in-development 6.6.11 main CYOA. It uses real current row and choice IDs and player-facing text from the species-builder portion of that project.

The full development project is much larger and has extensive cross-section requirements, scores, groups, optional modules, and generated relationships. Those cross-section mechanics are intentionally omitted here so this example can build and play independently. The excerpt preserves the selected rows, their direct Choices, and their original row selection limits.

Included topics:

- organism basis
- individual organization
- embodiment persistence
- physical substrate
- native embodiment environment
- species variation model
- head organization

Build and smoke-test it with:

```bash
./build.sh
```

or:

```bash
python build.py
```

The checked-in `build/project.json` is generated from `project-src/` and should not be treated as a second authoring source.
