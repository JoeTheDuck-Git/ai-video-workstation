# Style 09 — Liquid Glass 液態玻璃 (macOS glass) ★ LOCKED v1.0 · 2026-07-04

the pack author's pick for slot 09 ("mac OS liquid glass look"). Frosted, refractive glass
panels floating over a vivid aurora wallpaper — Apple's Liquid Glass material, not
2015 flat glassmorphism. The studio's only translucent-material world. For
tech/productivity/premium-lifestyle creators — the "clean premium" register.

## Card types — route by pasted content
| Context contains… | Build | Template |
|---|---|---|
| one claim with a rejected idea + a key word | 文字卡 | `templates/glass.html` |
| numbers, stats, results | 小工具卡 glass widgets | `templates/glass_widgets.html` |
| a list, steps, checklist, reminders | 通知卡 notification stack | `templates/glass_notif.html` |

## The emphasis vocabulary (unique — never borrow)
- key word (text card) — its OWN magnifying glass capsule: pops in last with jelly
  overshoot, refraction rim, specular sweep, caustic light pool beneath, and the whole
  wallpaper saturates. Capsule text = canvas-measured SVG w/ computed baseline
  (CJK-in-container rule), measured LAZILY at reveal.
- `cut:true` — the word FROSTS OVER: a milky ice pane grows in from the left BEHIND
  the glyphs (word stays sharp in front, flips to dark slate on the milk — never
  white-on-white), crystalline speckle + icy streaks, word contracts 2%. The gentlest
  strike after Pastel's squiggle, but colder.
- 小工具卡: stats as glass widgets that jelly-land and COUNT UP; ONE `hl:true` lands
  last in saturated pink glass + rim glow. Source line MANDATORY (never invent data).
- 通知卡: steps as macOS notification banners jelly-dropping in order (icon gradient +
  title + sub + timestamp); ONE `focus:true` pops 4% bigger in pink glass at the end.
  The `when` timestamps count down to 現在 on the focus item.
- Furniture: traffic-lights toolbar chip (Latin app name only) + glass clock chip
  (`clock:"auto"` ticks live).

## Directing rules
- Material realism carries the style: every glass element gets the refraction rim
  (ring-masked heavy backdrop-filter) + one specular sweep on landing. No rim = flat.
- LIQUID PHYSICS: everything lands with two-axis squash + border-radius morph, then
  drifts on incommensurate periods (--fd per element). Nothing is ever rigid or still.
- No ink, no texture, no camera, no shake, no scanlines. Energy = light and mass.
- Wallpaper: 4 aurora blobs (blue/purple/pink/orange), 110px blur, 23–31s drifts.
  Keep blob blur values STATIC — animating filters kills the 60fps screen recording.
- SFX language: water drops, soft glass thunks, shimmer, one frost breath, one bass
  bloom. 4–6 cues.
- O outro = defocus THROUGH the glass: everything blurs 16px, lifts, dissolves.
  R / S as always.

## Palette
bg #0e1424 · blobs #2e6cf6 / #8a3ff0 / #ff7ab8 / #ff9f3c · ink rgba(255,255,255,.96) ·
frost slate rgba(24,32,48,.85) · hl/focus glass: pink rgba(255,160,225,.3x)
Fonts: Noto Sans TC 900 (CJK) · Inter (Latin chrome, digits). No serif, no mono.

## HARD ENGINEERING RULES (learned building this style)
1. `background` shorthand + later `background-image` = the shorthand's gradient is
   silently overridden (background-image wins). Put ALL layers in ONE background-image
   list. Cost 3 review rounds on the frost pane.
2. Text over milky/frosted panes: flip the text to dark slate — white-on-milk always
   fails contrast, dimming white makes it worse.
3. Elements with base opacity:0 whose entrance animates only filter/transform never
   appear — .on must set opacity explicitly (same pitfall as Neon ignite).
