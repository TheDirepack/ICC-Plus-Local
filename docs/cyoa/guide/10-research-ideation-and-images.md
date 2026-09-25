# Ideation, images, and reference workflow

This file covers the parts of CYOA development that happen before the final card is written.

It incorporates useful design lessons from the supplied "CYOA 101" guide while leaving its old ICC-specific instructions in the reference notes.

## Start from one clear idea

Write the premise in one sentence. Keep it narrow enough that a player can tell what kind of choices belong.

When a new idea appears, ask which existing section it serves. If it does not serve the premise or improve a planned decision, put it in a later-project list rather than forcing it into the current CYOA.

A hybrid can still work, but the parts should support one experience instead of feeling like unrelated modes attached together.

## Keep an idea inbox

Capture raw ideas before deciding whether they are good.

A simple entry can contain:

- rough choice idea,
- section it may belong to,
- mechanic or story use,
- image or visual cue,
- source or inspiration,
- reason it might be worth keeping.

Review the inbox against the section map. Moving ideas into a structured inventory is easier than trying to invent a whole section from a blank page.

## Build structure before full descriptions

For a first pass, a choice may need only a working title and one-line purpose.

Finish the section skeleton first. Then expand the choices that survive the coverage and balance review.

This prevents polished prose from making a weak or duplicate option feel too expensive to remove.

## Use references as patterns, not copy

Study other CYOAs for section order, tradeoffs, card density, naming, image treatment, and interaction patterns.

Record what the example teaches. Do not copy its prose, artwork, or distinctive set of choices into a new work without permission or a clear legal basis.

When several references solve the same problem differently, compare the methods rather than automatically copying the most elaborate one.

## Image search starts from the choice brief

Search from the traits the card needs to communicate, not only from the final title.

Useful search dimensions include subject, action, mood, environment, clothing, technology, era, color, composition, and camera angle. Tag-based image sites can be useful because related tags expose alternate vocabulary.

Keep the image source with the asset when attribution or later replacement may matter.

A basic asset record can contain:

```text
asset file:
choice or section:
source URL:
creator:
license or permission if known:
search terms or tags:
crop notes:
credit text:
```

Do not rely on an external hotlink remaining available forever for a release asset.

## Choose an image for communication

The image should help the player recognize the choice before reading the whole card.

For a character, prioritize pose, expression, silhouette, clothing, and context that match the character brief. For an item or location, prioritize the feature that distinguishes it from nearby options.

Do not keep a beautiful image that strongly contradicts the choice text merely because it is attractive.

## Crop around the focal point

Crop before shrinking.

Remove empty or distracting areas that make the subject tiny. Keep a consistent aspect ratio across a repeated card pattern unless the section intentionally uses a different layout.

Portrait art often works better beside long text than above it. Short catalog choices can use denser, more regular image crops.

Mirroring can help composition when the image contains no text, symbols, handed equipment, asymmetric clothing, or other details that would become wrong.

## Use editing to unify, not to hide problems

Basic crop, scale, contrast, background, and color adjustments can help several unrelated source images sit together.

Do not depend on heavy effects to rescue unreadable text or a poor crop. Fix the underlying layout first.

## Build a small palette

A practical way to start is to take a few colors from a strong piece of anchor art or from the intended setting, then adjust them for readability.

Keep body text and state cues within the accessibility rules in `16-visual-design-and-responsive-layout.md`. A larger palette is not automatically a richer design.

## Let images suggest ideas carefully

A strong image can inspire a new choice, character, or setting detail. Add it only after checking the section map and existing options.

The image is a prompt, not proof that the CYOA needs another mechanic.

## Character ideation

Before writing a major companion or character option, answer a few private questions.

- What do they want?
- What can they do for the player?
- What will they refuse or fail to do?
- How do they speak?
- What changes when the player chooses them?
- Which existing character are they most similar to, and how are they different?
- What should the art communicate before the text is read?

A stable brief prevents a large cast from collapsing into the same voice with different names.

## Image and source audit

Before release, check that every final asset has a known purpose, usable resolution, sensible crop, and recorded source when needed.

Also check for duplicated images, repeated compositions that make different choices hard to distinguish, and source links that no longer resolve.

For a static edition, follow the export rules in `19-publishing-and-release.md`.

## Visual manifest workflow

Keep image selection and attribution in a machine-readable asset record or style manifest when the project is large. Each sourced image should remain tied to its stable target ID, release path, source URL, creator, permission or license, credit text, and crop notes.

Use `inspect` to create a bounded visual work queue. Use `style` for repeated presentation changes and `media` for image import and crops. Prefer explicit refs or bounded selectors with an expected match count.

Current local or embedded image assignment performs compression automatically when appropriate. Before packaging, probe assigned local assets and verify the final crops in the official Viewer.