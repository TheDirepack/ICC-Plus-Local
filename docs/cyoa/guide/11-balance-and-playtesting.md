# Balance and playtesting

CYOA balance is about decisions, not perfect numerical equality.

## What balance means here

A balanced CYOA usually has several viable builds, no accidental mandatory purchase, no currency that becomes meaningless, and no cheap combination that invalidates most alternatives.

Different builds can have different strengths. Exact combat parity is not required unless the project promises it.

## Price relative to the whole budget

A cost only matters relative to the total budget and the alternatives.

If the player has 30 points, a 10-point option consumes one third of the starting budget. If the player can easily earn 50 more points from painless drawbacks, the real cost is different.

Balance the complete economy, not each price in isolation.

## Start with target builds

Before final prices, decide what a normal finished build should be able to afford.

Example:

- One major power.
- Two or three support powers.
- One companion.
- A few minor perks.
- No drawback required for an ordinary build.

Then choose a budget and prices that produce that shape. Adjust through sample builds.

## Make scarcity happen near an interesting decision

The budget should usually run short while the player still wants several different things. If every reasonable build ends with a large surplus, the prices are not creating tradeoffs. If ordinary builds require severe drawbacks just to buy basic functionality, the starting budget or mandatory costs may be wrong.

Do not tune only for spending every last point. Leaving a small remainder is fine when the choices still feel costly.

## Use price bands

Instead of inventing every cost separately, define rough bands.

Example:

- 1 point for a narrow convenience.
- 2 to 3 for a useful supporting ability.
- 4 to 6 for a build-defining ability.
- 8 or more for a major capstone.

The exact numbers are project-specific. Bands make internal comparisons easier.

## Test opportunity cost

Ask what the player gives up to buy an option.

An 8-point power feels expensive when it prevents two other strong purchases. It does not feel expensive if every build has 60 unused points.

## Test synergies

Two fair choices can become unfair together.

Look for:

- Multipliers stacking with other multipliers.
- Cost discounts stacking with repeated purchase.
- Free selections satisfying expensive prerequisites.
- Defense combinations that remove all meaningful risk.
- Resource generators that pay for themselves.
- Forced selections that trigger extra Scores or actions.

Test the combination, not only each part.

## Avoid cancellation traps

Be careful with a later drawback whose only effect is to remove a benefit the player already paid for. That can feel like paying twice for the same axis.

If the project wants a reversible tradeoff, present it clearly as an upgrade, downgrade, replacement, or paired choice. If a drawback really does negate an earlier benefit, explain that interaction where the player can see it and price the pair as a combined decision.

## Test drawbacks as an economy

A drawback should have a price based on the burden it creates in this project.

Check whether players can take a drawback with little effect on the build they already wanted. If so, it may be free money for that archetype.

Also check the opposite problem. A drawback that destroys the premise may technically grant enough points and still be a bad option because almost no reasonable player would use it.

## Avoid fake budgets

If every legal build must spend 10 points on mandatory basics, a nominal 30-point budget gives only 20 points of real choice.

Either account for the mandatory cost in the starting budget, give the mandatory choice for free, or explain the structure clearly.

## Avoid dead currencies

A currency is dead when the player cannot spend it meaningfully or when every build ends with the same large surplus.

Separate currencies should represent separate constraints. If two currencies always rise and fall together, one may be unnecessary.

## Avoid mandatory best-in-slot choices

If nearly every sample build takes the same option, ask why.

It may be a core feature that should be free or part of the premise. It may be underpriced. It may cover a basic need that no alternative covers.

## Sample-build matrix

For any medium or large point-buy project, create a table like this before final implementation.

| Build | Main spend | Drawbacks | Points left | What it does well | What it gives up |
| --- | --- | --- | ---: | --- | --- |
| Generalist | mixed | none | 0 | broad coverage | no capstone |
| Specialist | one expensive path | none | 1 | peak power | weak support |
| Social | allies and influence | one | 0 | relationships | combat |
| High-risk | capstones | several | 0 | raw power | severe complications |

The names and columns should match the project.

Three builds are a useful minimum. For a large point-buy CYOA, do a wider tuning sweep once the first prices exist. A dozen or more deliberately different builds can reveal universal picks, dead options, and drawback combinations that three examples miss.

Record the builds in a table or spreadsheet so changes in budget and prices can be compared without replaying every build from memory.

## Sensitivity pass

After the economy works at the intended budget, make small changes to the starting budget or to one price band and repeat representative builds.

Look for choices that become mandatory after a tiny discount, choices that disappear after a tiny increase, and currencies that become irrelevant with a small surplus. These are signs that the design is sitting on a fragile threshold.


## Use an independent accounting check

For a point-heavy project, verify representative full builds with a simple accounting path that is independent of the runtime effect evaluator being tested.

Record the starting balances, each selected cost or gain, repeated-purchase increments, discounts, forced selections that change points, and the expected ending balances. Compare that ledger with the runtime result.

This catches cases where the project generator and the simulator share the same mistaken assumption. It is especially useful after changing repeat logic, discounts, forced activation, point transforms, or build compilation.

## Mechanical tests

For each major gate, test at least one passing and one failing state.

For complex rules, also test boundaries.

- Zero points.
- Exact cost.
- One point short.
- Minimum and maximum selection counts.
- Selection then deselection.
- Save then load.
- Requirement gained after a choice is already active.
- Requirement lost after a choice is active.
- Multi-select increase and decrease.
- Discounts entering and leaving effect.
- Forced activation chains.

## Player tests

Mechanical tests cannot answer whether the CYOA is fun or clear.

Ask testers to build without coaching. Note where they stop to ask a rules question, where they scroll backward, and which sections they ignore.

Useful questions include:

- What did you think the goal was?
- Which choice was hardest in a good way?
- Which choice was confusing?
- Did you ever feel forced to take an option?
- Did you understand your remaining budget?
- Did you discover an interaction that felt unintended?
- Which section felt too long for what it offered?

## Stop tuning when decisions work

Do not chase numerical precision that players cannot perceive. If several distinct builds are attractive, the economy is understandable, and no obvious exploit dominates the project, further changes should have a specific reason.