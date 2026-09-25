# Operating model and glossary

## What the LLM is doing

When working on a CYOA, separate four jobs that are easy to mix together.

1. Design the experience and rules.
2. Write the content.
3. Encode the design in ICC Plus 2.
4. Test the result as a player would use it.

A technically valid project can still be a poor CYOA. A well-written plan can still fail if it uses the engine incorrectly. Keep both checks.

## Before changing a project

For a new project, establish the premise, format, completion condition, economy, section map, and major state rules before creating large amounts of content.

For an existing project, first determine whether the user wants a content change, a rule change, a visual change, a bug fix, a migration, or a review. These tasks use different evidence.

If a project came from old ICC or ICC Plus 1.x, use the separate legacy migration reference before editing it. The target state should still follow ICC Plus 2 rules in this guide.

## Terms

- **CYOA**: A choice-driven character builder, scenario builder, world builder, gift picker, decision game, or related experience where the player makes a build from presented options.
- **Player contract**: The short statement of what the player is choosing, what limits apply, and what counts as a finished build.
- **Build**: The player's final set of choices and resulting state.
- **Row**: An ICC Plus 2 section that contains Choices and row-level settings.
- **Choice**: A selectable item inside a Row.
- **Addon**: Content attached to a Choice. Depending on configuration, an Addon can be informational or selectable.
- **ID**: The machine-readable identifier used by Requirements, Groups, imports, and other references.
- **Requirement**: A condition that controls supported behavior such as visibility, selection, scores, or Addons.
- **Global Requirement**: A reusable requirement definition.
- **Point Type**: A numeric value or currency tracked by the project.
- **Score**: A change to a Point Type associated with a supported object or condition.
- **Word**: Reusable or changeable text referenced by ID.
- **Variable**: Runtime state changed by supported actions and read by supported conditions.
- **Group**: A collection of Rows or Choices used by supported group-aware features.
- **Design Group**: The native reusable styling system for Rows or Choices. A Design Group can be assigned directly or linked through a normal ICC Plus Group.
- **Button**: A viewer control that runs configured actions.
- **Backpack**: A selected-choice summary built from configured Backpack Rows.
- **Choice Import**: A separate build-transfer feature that imports selected choice IDs or supported build data.
- **Build save**: The ICC Plus 2 viewer system for saving a player's build. Current ICC Plus 2 saves are associated with the CYOA link and can autosave.
- **Creator save**: Author-side project saving. ICC Plus 2 supports IndexedDB save slots and autosave in addition to file workflows.
- **Web viewer**: A hosted ICC Plus 2 viewer build.
- **Local viewer**: The offline-oriented ICC Plus 2 viewer package.
- **Gate**: A design term for any condition that blocks, hides, reveals, enables, or changes content.
- **Archetype**: A representative type of player build used for balance testing.

## Keep engine truth separate from design advice

A source saying that players prefer early drawbacks does not mean drawbacks belong early in every project. It means section order affects backtracking and should be chosen on purpose.

A source saying ICC Plus 2 supports a feature is different. Engine support is a factual question. Verify it against the schema, source, or target viewer.

## Minimum output for a planning task

A useful CYOA plan should normally identify these items.

- Premise and player contract.
- Main format and rule system.
- Section map and section order.
- Currencies, pick limits, or other budgets.
- Major prerequisites, exclusions, and state changes.
- Expected build length or choice count.
- Layout and text-density assumptions.
- At least three sample builds if balance matters.
- Test cases for the major gates.
- The ICC Plus 2 features needed to implement the plan.

Short projects can omit parts that do not apply.