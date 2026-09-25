# Legacy ICC project migration reference

This document exists only to recognize and port projects made for old Interactive CYOA Creator variants, including ICC Plus 1.x and MeanDelay-era project conventions.

Do not use this file as a design guide for new work. The target for new and migrated work is ICC Plus 2.

## Why this is separate

The official ICC Plus repository labels ICC Plus 1.x as legacy and no longer maintained. ICC Plus 2 is a Svelte 5 rewrite. Keeping old behavior in the main guide makes it too easy for an LLM to apply a historical workaround to a current project.

Read this file only when the input project is old, the source is uncertain, or the user explicitly asks for migration help.

## Historical sources

Use these to identify old concepts, not to override ICC Plus 2.

- Official ICC Plus repository: https://github.com/wahaha303/ICCPlus
- Historical MeanDelay-era tutorial: https://github.com/upasadena/interactive-cyoa-tutorial

The official repository is the authority for the relationship between the legacy and v2 lines. The historical tutorial is useful for recognizing old editor terminology and old project practices.

## Identification checklist

Before migration, record what you actually have.

- Original project JSON if available.
- Original hosted Viewer files if available.
- The URL where the old CYOA was known to work.
- Any custom JavaScript or CSS shipped beside it.
- Whether the project was made in MeanDelay ICC, ICC Plus 1.x, or an unknown fork.
- Whether the project depends on behavior that is not represented in project JSON.

Do not infer the exact old editor from visual appearance alone.

## Migration goal

The goal is not to reproduce the old editor. The goal is to preserve the player's intended choices and rules in a clean ICC Plus 2 project.

Preserve these first.

1. Choice meaning and visible text.
2. IDs when players or external build codes depend on them.
3. Point totals and costs.
4. Requirements and exclusions.
5. Selection limits and repeated-selection behavior.
6. Groups, result behavior, and build summaries.
7. Custom styling that affects readability or meaning.
8. Player save or import compatibility when it is a requirement.

Historical editor UI details are low priority unless they affect runtime behavior.

## Known v2 changes that matter during porting

The official ICC Plus 2 migration notes describe a full move from Vue 2.6.11 to Svelte 5 and several behavior or UI changes.

Examples include:

- The Alternate Menu option was removed.
- Creator saves gained IndexedDB slots and autosave.
- Point Types gained integer or floating-point configuration.
- The point bar scrolls when crowded instead of continuing to compress.
- Build save controls moved into Global Settings.
- Builds are saved per CYOA link and can autosave.
- Backpack image download behavior changed and old preload workarounds are not current v2 requirements.
- Design management moved into its own dialog.
- Project custom CSS and external CSS import are supported.
- Global Requirements can reference other Global Requirements.
- Requirement hide behavior changed to apply per requirement.
- Choices gained newer layout, multi-select, Addon, and transition controls.
- Responsive Choices Per Row controls expanded in later v2 releases.

Use the target v2 schema and release notes for exact current behavior.

## Do not port old workarounds blindly

Old projects may contain workarounds for editor or Viewer bugs that no longer exist.

Common warning signs include:

- Hidden helper state with no clear design purpose.
- Duplicate Scores that appear to compensate for update order.
- CSS selectors tied to old DOM structure.
- Manual image-preload logic.
- Viewer file patches.
- Instructions telling players to scroll before using a feature.
- Odd row structures that exist only to simulate an old UI limitation.

For each workaround, write down the behavior it was trying to preserve. Reproduce the original behavior in the target ICC Plus 2 Viewer. If v2 already behaves correctly, remove the workaround.

## Migration procedure

### 1. Freeze the old artifact

Keep an untouched copy of the original project and viewer files.

Do not migrate in place.

### 2. Inventory the old project

List:

- Rows.
- Choices.
- Point systems.
- Requirements.
- Groups.
- Buttons or custom actions.
- Addons or subchoices.
- Result or summary behavior.
- IDs used by external builds.
- Custom CSS and JavaScript.

### 3. Write behavioral tests

Before changing anything, describe a few old builds that must continue to work.

For each build, record selected Choices, point totals, visible Rows, important disabled Choices, and the expected summary.

### 4. Open or import into the current toolchain

Use the ICC Plus 2-compatible import path available in the working environment. If the project loads, do not assume the migration is complete. Loading is only the first test.

If the project does not load, inspect its JSON structure and historical tool source before hand-editing it.

### 5. Validate against ICC Plus 2

Run the current validator and query the current schema for every feature that reports drift.

Do not preserve an obsolete field merely because it exists in the old JSON.

### 6. Rebuild unsupported or unclear mechanics

Translate the intended behavior into current ICC Plus 2 constructs such as Requirements, Global Requirements, Variables, Groups, Design Groups, selectable Addons, current multi-select behavior, and project custom CSS.

Prefer a clean v2 implementation over a literal old-data translation when both produce the same player-facing result.

### 7. Preserve IDs deliberately

Keep old public Choice IDs when shared builds, imports, or external references depend on them.

Internal helper IDs can be cleaned up if every reference is migrated and compatibility is not needed.

### 8. Test the target Viewer

Run the behavioral tests made before migration. Add transition tests for any mechanic that changed implementation.

### 9. Remove dead compatibility code

Delete legacy workarounds that no longer serve a tested behavior.

### 10. Save as a new v2 project version

Record the original source, migration date, target ICC Plus 2 version, and known compatibility limits.

## Migration review questions

- Does the migrated project behave the same for representative old builds?
- Are public IDs preserved where needed?
- Did any old workaround survive without a reproduced need?
- Did old custom CSS rely on DOM selectors that changed in v2?
- Did build save or Choice Import assumptions change?
- Are point totals and multi-select refunds identical where they should be?
- Are hidden Rows and Requirements revealed at the same times?
- Did the migration preserve only intended behavior, or did it also preserve old bugs?

## After migration

Once the project is cleanly on ICC Plus 2, stop consulting this document for normal edits. Use `../guide/` as the current reference.