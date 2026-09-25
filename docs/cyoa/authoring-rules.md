# Generic CYOA authoring rules

These rules apply when creating, expanding, restructuring, or rewriting a CYOA. They are prevention rules. Apply them before adding content rather than relying on a later audit to catch avoidable problems.

## Start with the design model

Before writing a choice, identify what question the player is answering and which section owns that question. Search the project for the same concept, close synonyms, broader concepts, and narrower implementations. Decide whether the new item is a new axis, a tier on an existing axis, a child option, a modifier, or a duplicate.

Keep one global design model. A locally reasonable choice can still be wrong if another section already answers the same question or if its requirements conflict with the rest of the project.

## Keep ownership clear

Define the project's major domains and keep each concept under its natural owner. Do not use a generic advantages, drawbacks, or miscellaneous section when a more specific home exists.

When the project separates layers such as character, species, world, faction, civilization, equipment, powers, or scenario rules, do not let one layer silently redefine another. Put the underlying capability where it belongs and put social use, environmental context, deployment, or policy in the layer that actually owns it.

## Use meaningful hierarchy

A useful hierarchy is:

```text
major domain -> topic -> decision axis -> choices -> conditional detail
```

Do not add navigation rows that only create another click. Do not show detailed variants before the player has established that the parent concept exists. Parent questions should appear before dependent children.

Keep independent questions separate. Size and shape, capability and prevalence, technology and deployment, method and performance, legal status and social role, or baseline value and variability are different axes unless the design deliberately bundles them.

## Prevent duplicates and false alternatives

Before adding a choice, check whether the same concept already exists under another name. Merge true duplicates. If two choices look similar but represent different mechanics, make the distinction explicit in the title, description, placement, or requirements.

Do not put a parent concept beside one of its own implementations as though they are peers. Do not force independent choices into a single-select row merely because they are related.

## Make titles and descriptions agree

A title and its description must define the same trait. Do not use a narrow title for a broad package or a broad title for a narrow special case.

Use scientific, technical, legal, demographic, economic, and other real terms according to their normal meanings. Literal words such as `none`, `single`, `all`, `majority`, `immune`, `universal`, `permanent`, and `zero` must remain literal unless the description clearly qualifies them.

State the selected capability or state directly. Avoid descriptions that only imply the mechanic through mood, examples, or consequences.

Do not infer unrelated properties. Fast travel does not imply high cargo capacity. Longevity does not imply low fertility. A harsh environment does not automatically imply a particular government. A technology level does not prove that every settlement has deployed every technology.

## Price understandable things

A paid choice should give the player an understandable benefit, tradeoff, state, or limitation. Do not charge points for ordinary baseline behavior unless the choice defines a meaningful improvement or the project intentionally prices all baseline configuration.

If a choice bundles several independent benefits, split it or state that the bundle is deliberate and price it as a package.

## Requirements must match the prose

Encode every prerequisite, exclusion, dependency, limit, and content gate that the description assumes. Do not rely on prose alone for a mechanical restriction.

Requirements must not be broader than the description. A rule that forbids one mechanism should not block other mechanisms merely because they are nearby in the taxonomy.

Avoid confusing forward dependencies. If a player must select something later before an earlier section works, reorganize the flow or explain the dependency clearly.

## Separate capability, state, prevalence, and implementation

These are often different questions:

- Can this exist?
- Does this instance have it now?
- How common is it?
- How strong or extensive is it?
- How is it implemented?
- Who has access to it?

Do not answer several of these with one choice unless the coupling is intentional.

## Keep content controls separate from in-world meaning

A content-rating, spoiler, mature-content, optional-module, or accessibility toggle is a presentation or access control unless the setting explicitly makes it an in-world rule. Do not let a UI gate silently redefine age, biology, legality, prevalence, or canon status.

Neutral mechanics should stay neutral even if they are stored near restricted material. Restricted wording and explicit material should remain properly gated.

## Write for the player

A choice should tell the player what changes when selected, how it differs from nearby choices, and any important limitation needed to use it correctly. Do not expose authoring metadata, internal IDs, compiler terminology, source notes, or validation language in player-facing prose.

Keep examples selective. Do not bury the defining distinction under a long list of edge cases.

Use consistent terms for the same concept throughout the project. Repetition is better than synonym cycling when the repeated word is a game term.

## Preserve stable identifiers

Once content is in active use, treat IDs as stable interfaces. Preserve them through wording, ordering, and ordinary mechanical repairs. Change an ID only when there is a clear migration reason, then update every reference and regression test that depends on it.

## Authoring checklist

Before committing a batch, verify that each changed item has the correct owner and parent, appears after any required parent decision, does not duplicate an existing answer, keeps independent axes separate, uses literal and technical terms correctly, has requirements that agree with its prose, has a price that matches what it grants, and contains no authoring metadata in player text.

After a larger batch, run global checks for duplicate IDs, missing references, impossible requirements, stranded content, ordering problems, contradictory same-row selections, unreachable branches, and unexpected point changes. Then test representative player paths rather than relying only on static validation.
