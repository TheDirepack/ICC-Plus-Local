---
name: cyoa-compress
description: Use when an external CYOA asset tree needs standalone compression.
compatibility: Exceptional or legacy asset workflow. Normal ICC Plus 2 authoring should use iccplus-local media and style commands instead.
---

# CYOA compress

Treat standalone compression as an exception, not a normal authoring phase.

## Normal ICC Plus workflow

For images being assigned through the current local authoring tool, use `iccplus-local` with its `media` and `style` function guides. Assigned local or embedded images are compressed automatically when appropriate.

Do not add a second compression pass merely because images are final.

## Exceptional workflow

Use a separate compressor only when all of these are true:

- the assets sit outside the normal `iccplus-local` media path,
- the user wants a separate compression operation,
- the available compressor is appropriate for that file tree,
- the original assets remain recoverable.

For a legacy or external tree:

1. Probe the asset layout and references.
2. Prefer a separate output directory.
3. Dry-run broad rewrites when the tool supports it.
4. Keep the original when conversion is not smaller or visibly worse.
5. Verify rewritten references.
6. Compare representative images at their rendered size.
7. Test the resulting release package.
8. Record before and after size.

## Rules

- Compression must not become a second source of project structure.
- Do not rewrite the authoritative structured source merely to fit a compressor.
- Do not recompress files that are already suitable without a measurable benefit.
- Do not assume a smaller file is visually acceptable.
- Do not use a retired compatibility command simply because an old guide mentions it.

## Output

Report why a standalone pass was needed, the tool used, output location, size change, rewritten-reference count if applicable, errors, and visual/package verification.

## Final checks

- [ ] The normal automatic media path was ruled out first.
- [ ] Originals remain recoverable.
- [ ] References resolve.
- [ ] Representative images remain acceptable.
- [ ] The package loads as delivered.