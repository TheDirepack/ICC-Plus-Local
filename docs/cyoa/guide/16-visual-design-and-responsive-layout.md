# Visual design and responsive layout

Visual design should help the player scan, compare, and understand choices.

## Build a small design system

Decide these before styling individual cards.

- Page background.
- Row background and spacing.
- Choice card treatment.
- Body font.
- Heading font.
- Accent color or accent treatment.
- Selected and disabled states.
- Image treatment.

Reuse the system. Local exceptions should have a reason.

## Section hierarchy

A player should be able to tell where one section ends and another begins without reading every title.

Use spacing, Row backgrounds, headings, or borders consistently. Do not rely on a different random color for every section.

## Keep geometry consistent

Repeated cards should use consistent padding, border thickness, corner radius, image placement, and title spacing unless the difference communicates a real state or hierarchy.

Small mismatches are easy to create when Rows use local styling. Check the final result side by side instead of assuming copied settings remain identical.

## Text readability

Test text against the actual busiest image used in production.

If text overlaps detailed art, use a solid or translucent text area, change the crop, or move the text. A shadow cannot rescue every background.

Keep decorative fonts for short headings. Body copy should remain easy to read on a phone.

## Crop for the choice

Choose the crop around the information the card needs.

Keep the focal subject large enough to read at the final card size. Remove empty or distracting areas before shrinking the image. When several cards share a Row, use a consistent aspect ratio unless a deliberate layout change improves the section.

Do not let the available picture define the mechanic by accident. The image should support the planned choice.

## Color

Do not use color as the only indicator for positive, negative, selected, invalid, or disabled state.

Use signs, labels, icons, borders, or another visible cue.

For web releases, use WCAG 2.2 contrast as a practical floor. Normal text should reach 4.5:1 against its background and large text should reach 3:1. Test real selected, disabled, and overlay states instead of only the default card.

A small palette is usually easier to keep readable than many unrelated accent colors. One practical starting point is to take a few colors from the project's anchor art, then adjust lightness and saturation until the text and state cues meet contrast needs.

## Image ratios

Consistent aspect ratios make card grids easier to scan.

This is a layout rule, not a demand that every project use the same ratio. Wide landscapes, squares, portraits, and banner art can all work if the card structure is designed for them.

Community authoring discussions often recommend consistent cropping because irregular image heights make static and interactive grids harder to read.

## Card density

Match the number of columns to the longest normal card in that Row.

Short item cards can be dense. Long companion or faction descriptions need more width.

Do not judge a layout only with the shortest placeholder text.

## Symmetry

A grid with one stranded card can look unfinished, especially in small sections. Symmetry is a visual preference rather than a hard rule. Use centered final rows or a different column count when the imbalance is distracting.

Do not distort content or add filler choices only to make the grid even.

## Responsive ICC Plus 2 controls

Use ICC Plus 2 Choices Per Row and responsive controls before adding custom CSS for normal card-count changes.

Current v2 supports a dedicated 960 to 1280 pixel range and newer controls that can retain configured Choices Per Row on smaller screens.

Test the target version because responsive behavior has changed across v2 releases.

## Point bar

The ICC Plus 2 point bar scrolls when many Point Types are visible instead of compressing them indefinitely.

Check whether the most important currencies remain easy to find and whether touch scrolling works well on phones.

## Backpack layout

A Backpack is a review tool. Favor compact readability over recreating every decorative detail from the main CYOA.

If the Backpack is used for downloadable build images, test long titles, long descriptions, and images before release.

## Interaction accessibility

For interactive controls, keep pointer targets at least 24 by 24 CSS pixels or provide enough spacing to meet the WCAG 2.2 minimum. Larger targets are often better on phones.

If an image carries information that the adjacent text does not contain, provide a concise text alternative when the target viewer and publishing route support it. Decorative images should not create duplicate spoken content.

Do not put essential rules only inside an image. Keep rules and costs as real text when the format allows it.

## Custom CSS testing

After custom CSS changes, test these states when the project uses them.

- Unselected Choice.
- Selected Choice.
- Disabled or unmet Choice.
- Hidden content.
- Addons.
- Backpack.
- Menus and dialogs.
- Phone width.
- Tablet width.
- Normal desktop.
- Wide desktop.

## Asset budget

Track the final package size and the largest files.

A CYOA with hundreds of images should have a deliberate compression and loading plan. Do not keep source-resolution art in the release when the viewer displays a small thumbnail.

## LLM visual pass

For a large project, use `inspect` to request a compact visual work queue instead of loading the entire project into the visual pass.

Calibrate a small family first, then apply the broadest native styling scope that fits. Use project styling for global defaults. Use official Row/Choice Design Groups for reusable visual families, including Group-linked inheritance when normal ICC Plus Group membership should carry the style. Use private Row or Choice styling only for a genuine one-off exception. Use custom CSS only when the native styling model cannot express the result.

Apply the treatment through `style`, using explicit refs or a selector with an expected match count. The style command rejects one private inline style item that targets several entities, so shared treatments should be represented as Design Groups instead of copied private styling. Use `media image import` and the current crop operations for local assets.

Local or embedded image assignment handles compression automatically when appropriate. The local tool still does not judge crop quality or render CSS. Final layout, state styling, responsive behavior, and image composition must be checked in the official Viewer.