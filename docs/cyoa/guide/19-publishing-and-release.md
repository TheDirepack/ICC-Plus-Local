# Publishing and release

## Choose the release format

ICC Plus 2 has official web and local viewer formats. Select the format the player will actually receive.

Do not package a web preview and call it a local build.

## Build from an official template

Use the ICC Plus 2 viewer template that matches the target release. Do not hand-copy an old viewer folder from memory.

Build from the official Viewer template or release package for the target version. Keep project generation and edits in reproducible CLI scripts instead of hand-editing generated Viewer output.

## Test the generated package

A release test starts after packaging.

Check:

- Project loads.
- First choices work.
- Point totals work.
- Requirements work.
- Multi-select and Addons work if used.
- Build save works if enabled.
- Choice Import works if enabled.
- Backpack works if enabled.
- Custom CSS and external CSS load.
- Images and audio load.
- Phone layout works.

## Web release

Serve the package through HTTP during testing. Then test the final public URL in a clean browser session.

Check the browser console and network requests for missing assets, blocked fonts, or failed external CSS.

If build save is enabled, test it at the canonical public URL because ICC Plus 2 associates builds with the CYOA link.

## Local release

Test the official local viewer package as it will be delivered. Do not apply a web viewer loading requirement to it without evidence from the local package.

## Optional static edition

Treat a static edition as its own release format.

Before export, make sure the static reader can see the information that an interactive player would reveal through clicks, requirements, tabs, or hidden Rows. Do not leave core instructions behind an interaction that no longer exists.

Render only after all intended images have loaded. Check the rasterized result for changed colors, clipped text, missing fonts, and inconsistent card heights.

If the final image is too long or too large for the target host, split it into readable pages. Put the CYOA title, version, page number, and total page count on each page when practical. Host limits change, so record the current platform limit instead of hard-coding an old number into the design guide.

If both formats exist, link the interactive edition from the static release when the platform allows it.

## Release metadata

Record:

- CYOA version.
- Target ICC Plus 2 viewer version.
- Date.
- Local `iccplus-local` version and source snapshot used for scripted checks.
- Known compatibility notes.

## Public ID stability

After release, changing visible text is much safer than changing IDs.

If a release must rename public IDs, treat it as a migration and decide whether old shared builds will remain supported.

## Release checklist

A release is not ready only because local phase validation and read-only inspection are clean.

The final standard is that the packaged project behaves correctly in the target viewer and the player can understand how to finish a legal build.