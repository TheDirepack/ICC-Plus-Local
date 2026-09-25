# Local workflow checklist

- [ ] Record the project revision or fingerprint under test.
- [ ] Discover the installed `iccplus-local` command tree when the release may have changed.
- [ ] Confirm the authoritative source before writing; do not patch generated `project.json` when a compiler or structured source exists.
- [ ] Use `inspect` before mutation when target IDs, selectors, or current values are uncertain.
- [ ] Use `structure`, `rules`, and `style` for normal writes and read their validation receipts.
- [ ] Bound bulk selectors with an expected match count and re-resolve them after membership-changing edits.
- [ ] Use `play` for player-visible actions and observations.
- [ ] Keep continuation data in a private `--state` file and out of player reasoning.
- [ ] Treat rejected actions as test results and confirm they leave no partial mutation.
- [ ] Start a new run after project edits unless cross-revision behavior is the test.
- [ ] Reduce important failures to the shortest reproducing action sequence.
- [ ] Check current coverage before making Viewer-parity claims.
- [ ] Use the official target Viewer for browser behavior and anything outside verified local coverage.
- [ ] Record the release identity and artifact hash only when parity-sensitive provenance requires it.