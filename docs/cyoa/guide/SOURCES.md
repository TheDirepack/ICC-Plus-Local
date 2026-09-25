# Sources

This guide separates engine facts from design references.

## ICC Plus 2 engine sources

Use these for ICC Plus 2 behavior.

- Official deployment repository: https://github.com/wahaha303/ICCPlus
- Official ICC Plus 2 source repository: https://github.com/wahaha303/ICC-Plus-Svelte
- Official ICC Plus 2 web Creator: https://hikawasisters.neocities.org/ICCPlus2/
- Official ICC Plus 2.0.0 release post: https://www.reddit.com/r/InteractiveCYOA/comments/1luqv2k/
- Official ICC Plus 2.10.6 update post: https://www.reddit.com/r/InteractiveCYOA/comments/1vp0avg/
- Current pinned ICC Plus 2.10.7 source commit: `1ea9db888cde2286d18d0d5de50933cb8773b739`.
- Local `../../../SOURCE_NOTES.md` and field reference for the pinned command-line snapshot.

The official deployment repository records the ICC Plus 2 save system, custom CSS, responsive controls, Point Type changes, Requirement changes, Backpack changes, and Viewer changes.

Do not assume any recorded release remains the newest v2 release. Check the target version and pinned source before relying on a feature or bug fix. The 2.10.6 release post remains useful historical evidence, while the current local tool targets 2.10.7 from the official source repository.

## CYOA design and player-experience references

These are community discussions. They are evidence of recurring author and player concerns, not engine documentation or universal rules.

- CYOA balance discussion: https://www.reddit.com/r/makeyourchoice/comments/llsktv/how_to_balance_a_cyoa/
- Point-buy balance discussion: https://www.reddit.com/r/makeyourchoice/comments/1l5hvk4/pointbuy_system_balance_help/
- Drawback placement discussion: https://www.reddit.com/r/makeyourchoice/comments/ywibiq/
- Earlier drawback format discussion: https://www.reddit.com/r/makeyourchoice/comments/dzejpi/
- CYOA layout and image advice: https://www.reddit.com/r/makeyourchoice/comments/1d5p3kn/
- CYOA player pet peeves, including mechanical and structural complaints: https://www.reddit.com/r/makeyourchoice/comments/ky787d/
- Interactive CYOA tips and pitfalls: https://www.reddit.com/r/InteractiveCYOA/comments/wrf0hl/
- Discussion of common interactive CYOA needs such as sections, points, scores, and build review: https://www.reddit.com/r/makeyourchoice/comments/19byc70/
- Recent player preferences and dislikes: https://www.reddit.com/r/makeyourchoice/comments/1vpd4sh/what_do_you_really_appreciate_in_a_cyoa/
- Discussion of images in long CYOAs: https://www.reddit.com/r/makeyourchoice/comments/106hdat/

Recurring useful observations include testing full builds instead of isolated prices, making point accounting visible, minimizing forced backtracking, matching image shape to card layout, and using drawbacks that change the fiction rather than only paying points.



## Supplied CYOA guide

The user supplied `CYOA 101 by Dragon's Whore` as an eight-image archive. It is preserved in the CYOA source folder and summarized in the project references.

Useful material carried into the current guide includes premise focus, structure-first drafting, relative pricing, broad build testing, related-choice placement, unlock hints, image cropping, consistent card geometry, mobile-aware density, restrained palettes, and character briefs.

Old ICC editor steps, manual `project.json` hacks, specific hosting workarounds, and other version-bound instructions were not treated as ICC Plus 2 facts.

The public Interactive CYOA Creator Tutorial also lists CYOA 101 as one of its major tutorial sources:
- https://icctutorial.pages.dev/appendix/resources/

## Additional interactive CYOA references

- Interactive CYOA Creator Tutorial, IDs and requirements: https://icctutorial.pages.dev/mechanics/ids-and-requirements/
- Interactive CYOA Creator Tutorial, Rows and nesting pitfalls: https://icctutorial.pages.dev/mechanics/rows/
- Interactive CYOA Creator Tutorial, resources and tooling: https://icctutorial.pages.dev/appendix/resources/
- Recent community layout discussion: https://www.reddit.com/r/makeyourchoice/comments/1d5p3kn/
- On Building CYOAs resource thread: https://www.reddit.com/r/makeyourchoice/comments/o5ycdd/

## Interactive fiction design references

These sources are not ICC Plus 2 documentation. They are useful for choice and branch design.

- Choice of Games, "5 Rules for Writing Interesting Choices in Multiple-Choice Games": https://www.choiceofgames.com/2010/03/5-rules-for-writing-interesting-choices-in-multiple-choice-games/
- Choice of Games, "By the Numbers: How to Write a Long Interactive Novel That Doesn't Suck": https://www.choiceofgames.com/2011/07/by-the-numbers-how-to-write-a-long-interactive-novel-that-doesnt-suck/
- Choice of Games, "End Game and Victory Design": https://www.choiceofgames.com/2016/11/end-game-and-victory-design/
- ink web tutorial and branching basics: https://www.inklestudios.com/ink/web-tutorial/
- Bruno Dias, "Making Interactive Fiction: The Branch and the Merge": https://sub-q.com/making-interactive-fiction-the-branch-and-the-merge/

Recurring lessons used here are that choices need consequences and a basis for decision, full permanent branching grows too quickly, delayed consequences can preserve meaning after branches merge, and major ending paths can carry more divergence than every small choice.

## Accessibility references

For web releases, the guide uses WCAG 2.2 as a practical baseline.

- Contrast minimum: https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html
- Use of color: https://www.w3.org/WAI/WCAG22/Understanding/use-of-color
- Target size minimum: https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html
- Images and text alternatives: https://www.w3.org/WAI/tutorials/images/