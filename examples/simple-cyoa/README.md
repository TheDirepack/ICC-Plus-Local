# Simple CYOA example

This example is deliberately small. It demonstrates the maintained ICC Plus Local build pattern without carrying assumptions from a larger project.

The source lives in `project-src/`:

- `10-structure.json` creates rows and choices.
- `20-rules.json` adds the point budget, selection limits, costs, and one requirement.
- `90-style.json` is an empty style phase that shows where presentation changes belong.
- `iccplus.build.json` defines the repeatable build order.

`build.sh` and `build.py` both rebuild the project from scratch and run `tests/playtest.json` through the player-safe `play` command.

`generate_phase_files.py` shows a second builder pattern. It starts from ordinary Python data and emits phased ICC Plus source files. A larger project can replace the in-script data with YAML, spreadsheets, a database export, or another canonical source model.

Run:

```bash
./build.sh
```

The generated output is `build/project.json`.
