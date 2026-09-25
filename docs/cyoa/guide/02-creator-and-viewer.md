# ICC Plus 2 Creator and Viewer

## Creator and Viewer have different jobs

Use the Creator to edit project data and project-level settings. Use the Viewer to test the player experience.

A valid save in the Creator does not prove the Viewer behaves correctly. Requirements, force-active actions, multi-select behavior, score order, build saves, and responsive layout all need runtime tests when the project depends on them.

## ICC Plus 2 target

ICC Plus 2 is the target for this guide. Use the current v2 schema, source, release notes, and target Viewer for engine behavior.

For a pre-v2 project, use the separate migration reference before normal v2 editing.

## What each verification proves

- Creator acceptance proves the project can be opened and saved by the authoring tool.
- Local inspection proves only the checks implemented by the current local tool.
- Local `play` proves only the gameplay semantics covered by that runner.
- Official Viewer testing proves the behavior of the target player runtime for the path tested.

Do not promote one of these into proof of the others. A clean local result cannot settle a browser-only layout issue, and a project that opens in the Creator can still have broken runtime transitions.

## Creator saves

ICC Plus 2 supports author-side project saving through IndexedDB, including manual save slots and autosave. File-based project workflows remain useful for versioning, scripted command-line generation, backup, and release packaging.

Do not confuse Creator save slots with player build saves.

## Player build saves

ICC Plus 2 has a dedicated Viewer build-save system. Current v2 behavior stores builds per CYOA link and supports autosave.

If a project depends on build saves, test the canonical release URL. A URL change can create what looks like a missing save because the save belongs to another link.

## Choice Import

Choice Import is separate from build save and separate from the Backpack. Use it when the project benefits from transferable build data or ID-based imports.

Do not enable Choice Import merely because the project has a Backpack.

## Web and local viewers

Treat these as separate release formats.

- The web viewer is built for hosted use.
- The local viewer is an offline-oriented package.

A helper that previews the web viewer through HTTP does not imply that the official local viewer must be served over HTTP.

## Global project behavior worth planning early

Some global settings affect later design work.

- Build save and autosave.
- Project custom CSS.
- External CSS imports.
- Image rendering during edit mode.
- Responsive Choices Per Row behavior.
- Point bar presentation.
- BGM and sound use.

Decide these when they affect the experience, not at the last minute.

## Version discipline

Record the project version, target ICC Plus 2 Viewer version, and local CLI version together for a release. If the local CLI source snapshot is older than the target Viewer, verify changed fields against the target source before scripting them.