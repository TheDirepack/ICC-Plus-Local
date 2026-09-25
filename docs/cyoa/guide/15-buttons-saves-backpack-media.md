# ICC Plus 2 Buttons, Backpack, saves, media, and CSS

## Buttons

A Button should have a clear player-facing purpose.

Examples include confirming a mode, running a random selection, changing a Variable, navigating a Row flow, or applying a deliberate state change.

Avoid Buttons that silently rewrite many unrelated parts of the build unless the player is told what will happen.

Test Buttons from a clean state and from states where affected Choices are already active.

## Build save and load

Use ICC Plus 2 build save when players are likely to return to a long project or compare several builds.

Test:

- A new save.
- Loading the save.
- Editing and resaving.
- Autosave if enabled.
- The final deployed URL.
- A save that includes multi-select, Variables, forced state, or other complex mechanics used by the project.

## Choice Import

Use Choice Import when players benefit from copyable or transferable build data.

Treat imported IDs as a compatibility promise. Stable IDs matter more once players share builds.

## Backpack

The Backpack summarizes selected content through configured Backpack Rows.

Use it when a final build is hard to review in the main page.

Current ICC Plus 2 preloads images for Backpack downloads and can allow deselection from the Backpack. If deselection is enabled, test what happens when the removed Choice is a prerequisite for something else.

## Images

Add final images after the structure and rules are stable enough that large sections will not be deleted or rebuilt.

Crop for the intended card shape before compression. Keep a consistent visual ratio within a section unless the layout is designed around mixed shapes.

Do not set one universal pixel size for all assets. A large background, a wide feature image, and a small Choice thumbnail have different needs.

Measure the packaged release rather than only the raw project file. Packaging can change how images are stored or deduplicated.

## Image rendering during authoring

ICC Plus 2 can disable image rendering in Edit Mode. Use that on large projects when editor responsiveness is a problem.

## Sound effects

ICC Plus 2 has a Sound Effects manager. The Creator recommends keeping each effect under 100 KB to avoid performance problems.

Sound should reinforce feedback, not replace visible feedback. A player with audio muted should still know that an action occurred.

## BGM

ICC Plus 2 supports background music behavior, including later support for external audio in addition to YouTube-based use.

Use BGM only when it serves the project. Test mute, load, and saved-build behavior for the target version when the project depends on audio state.

## Custom CSS

Use native ICC Plus styling before custom CSS. Put whole-project defaults in project styling. Use official Row/Choice Design Groups for reusable visual families. Reserve private Row or Choice styling for genuine one-off exceptions.

ICC Plus 2 can store custom CSS in the project. Use it only when the native styling controls and Design Groups cannot express the required result. Prefer project CSS before patching viewer files, and keep selectors narrow and based on supported classes where possible.

Current ICC Plus 2 exposes useful classes for newer Addon conditions. Query the target source or schema before relying on a specific class.

## External CSS

External CSS imports can provide fonts or other shared styles. The host must permit the required cross-origin access.

Test the final hosted URL. A font that works in one authoring environment can fail after deployment because of host CORS rules.

## Scripted image assignment

Use `inspect` to build a bounded visual work queue, `style` to apply one or many presentation changes, and `media` for image import, crop operations, fonts, sound, and asset probing.

Keep source, permission, credit, and crop notes beside the asset assignment or style manifest. Use explicit refs or bounded selectors with an expected match count for repeated styling.

Current local or embedded image assignment performs compression automatically when appropriate. Do not add a routine standalone compression pass after media assignment. Probe local assets and test the official Viewer before release.