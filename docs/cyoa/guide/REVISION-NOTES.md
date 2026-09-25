# Revision notes

## 2026-09-25 rc12 validation and styling alignment

- Updated the active ICC Plus Local guidance for 0.10.0rc12 and the pinned ICC Plus 2.10.7 source.
- Documented complete-project validation and official-default hydration for canonical write/build paths.
- Added `project validate` as the final completeness check and `project hydrate` as the legacy repair path.
- Clarified that official Row/Choice Design Groups are the reusable native styling system.
- Set the styling order to project defaults first, Design Groups for reusable families, private Row/Choice styling only for one-off exceptions, and custom CSS only when native styling cannot express the result.
- Kept revision 6.6.21 recorded as a 2.10.6 project until an actual migration and rebuild is performed.

## 2026-09-20 lifecycle reorganization

- Reordered the active guide around the project lifecycle instead of historical addition order.
- Replaced fragile chapter-number shorthand with explicit filenames.
- Grouped the guide into foundation/workflow, design/content, ICC Plus implementation, and testing/release.
- Kept installable skills flat for discovery while ordering the skills README by lifecycle.
- Replaced the stale local-session checklist with `local-workflow-checklist.md` using the current `inspect`/phase/`play` workflow.


## 2026-09-20 memory-driven clarification pass

- Added an explicit rule for local-runner disagreements: keep native Viewer behavior and fix or limit the local model instead of encoding simulator mismatches into project data.
- Documented what Creator, local inspection, local play, and official Viewer tests each prove.
- Added source-side baseline-and-delta guidance for repeated content families without exposing authoring inheritance to players.
- Clarified opening and goal text, hidden versus unavailable content, independent point accounting, reusable tool placement, generated-output discipline, and release filtering of authoring metadata.
- Replaced stale requirement-debugging commands with the current `inspect`, `play`, and `reference commands` workflow.
- Expanded performance troubleshooting to separate Creator, Viewer, and scripted-authoring bottlenecks.

## 2026-09-20 rc10 workflow alignment

- Updated the active guide to the current workflow-centered `iccplus-local` interface.
- `inspect` is now the read-only project surface and `play` is the normal player-safe testing surface.
- Normal `structure`, `rules`, and `style` writes are documented as self-validating.
- Visual guidance now uses `inspect`, `style`, and `media`; normal image assignment handles compression automatically.
- Continuous-play guidance no longer teaches `session`, `view`, or `state-check` as current commands.
- The guide now says to discover any advanced analysis route with `reference commands` instead of relying on hidden compatibility aliases.
- Historical notes below keep old command names only to describe the releases in which they existed.

## 2026-09-18 damaged-session recovery pass

This pass updates the guide for `iccplus-local` 0.9.5.

- `state-check` treats malformed and truncated JSON as an invalid state instead of a generic CLI failure.
- `play` uses a sanitized invalid-state result and leaves the damaged file unchanged.
- `play --reset` can replace a damaged continuation file without loading it first.
- Failed state imports are transactional, including seed and RNG validation.

## 2026-09-18 local play and continuation pass

This pass updates the guide for `iccplus-local` 0.9.4.

- `play PROJECT --state FILE` is now the default continuing LM player loop.
- `state-check` validates a continuation file without changing it.
- Player continuation files stay outside the LM context and are written atomically with owner-only permissions where supported.
- `session --player-safe` remains the ordered multi-action interface.
- The guide keeps `view` as the one-shot player observation command and raw `session` state for internal regression tooling only.

## 2026-09-17 research and LLM authoring pass

This pass kept the existing ICC Plus 2 structure and added missing design and LLM workflow guidance.

Main changes:

- Reviewed the supplied eight-part "CYOA 101 by Dragon's Whore" archive and preserved it as a source.
- Added premise focus, non-goals, skeleton-first drafting, content coverage, related-choice placement, hidden-content discoverability, and better choice-consequence checks.
- Expanded balance guidance with wider build sweeps, relative pricing, cancellation-trap checks, and sensitivity testing.
- Expanded visual guidance with image focal-point cropping, consistent card geometry, measured contrast, target-size checks, and image text-alternative guidance.
- Added static-edition release guidance without carrying forward old ICC or host-specific hacks.
- Added `03-development-protocol.md` for long-project state, source labels, bounded passes, consistency audits, and requirement-graph review.
- Added `10-research-ideation-and-images.md` for idea capture, reference use, asset records, image search, cropping, palettes, and character briefs.
- Added new planning templates for choice briefs, coverage matrices, and LLM work passes.
- Updated the recorded ICC Plus release reference to 2.10.6 after checking the August 2026 release post.

Legacy ICC instructions remain outside the main guide.