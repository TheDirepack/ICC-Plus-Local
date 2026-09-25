# Phased authoring

Normal editing has three owners.

| Phase | Owns |
| --- | --- |
| `structure` | Rows, Choices, Addons, IDs, titles, text, order, move/clone |
| `rules` | Points, Requirements, Scores, Groups, gating, costs, limits, effects |
| `style` | images, templates, widths, styling, CSS/presentation |

Each phase accepts single or bulk work through the same command. There is no separate bulk command.

```bash
iccplus-local structure project.json @10-structure.json
iccplus-local rules project.json @20-rules.json
iccplus-local style project.json @90-style.json
```

Each normal edit validates automatically before writing. Validation failure leaves the target unchanged.

Use `expect` on broad selectors. Use `inspect` before a selector edit when the match set is not obvious.

Images assigned through `style` are compressed automatically.

After authoring, use `play` to audit actual player-visible behavior rather than inspecting hidden runtime mechanics.
