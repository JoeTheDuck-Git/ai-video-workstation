# Style 03 — Pop Art 普普 (Lichtenstein comic) ★ LOCKED v1.0 · 2026-07-04
Approved by the pack author ("this style is good"). Same rule as Vox: don't restyle it.

Replaced Grunge (the pack author's veto 2026-07-04: too close to Vox's design language). Pop Art
shares NOTHING with Vox: no paper texture, no hand-drawn ink, no handwriting, no grain.
The system is Ben-Day dots, flat primaries (red/yellow/blue/black/cream), fat black
outlines, CMYK misprint shadows, starbursts, speech bubbles, onomatopoeia. For hot takes,
反轉觀點, entertainment/lifestyle creators, anything that wants LOUD and fun.

## Card types — route by pasted content
| Context contains… | Build | Template |
|---|---|---|
| a hot take / contrast line (Ⅹ✗ → Ｙ!) | 文字卡 | `templates/pop.html` |
| a mini STORY with a reversal — before/after, 過程, 對比劇情 | 分格卡 comic strip | `templates/pop_strip.html` |
| numbers, %, comparisons | 數據卡 | `templates/pop_chart.html` |

**分格卡 rules:** 2–3 panels, setup → beat → PUNCHLINE. Panel text ≤ 2 short lines (use
`\n`); captions are the clock/context (第1天…). Give ONLY the last panel a `burst`
(2–4 chars — the reveal). Comedy lives in the gap between panels 2 and 3.
**數據卡 rules:** comic-block bars, hl value lands in a starburst with flash + shake.
Real numbers + `source` mandatory (Studio-wide ethics).

## The emphasis vocabulary (never mix with other styles')
- `key:true` — the word lives INSIDE a red starburst that spins in with a full-frame
  color flash + screen shake; sunray背景 centers on it.
- `x:true` — the rejected idea gets a fat red ✗ slapped over it (this style's strike).
- `bubble` — the tag is a speech bubble with tail + hard offset shadow (not handwriting).
- `pow` — 2–3 char onomatopoeia burst (砰！蹦！啥？) top-right; pick one that matches
  the line's emotion.
- `flashColor` — yellow default; red for angrier lines.

## Directing rules
- Copy should sound like a comic panel: short, punchy, spoken. 2 lines max, the key word
  LAST. If the line is thoughtful/nuanced → wrong style, suggest Vox or Minimal.
- Motion language is pop-and-shake (scale overshoot, screen shake) — no camera push, no
  drift; the energy comes from impacts, not movement.
- Word tilts are random ±3°; misprint shadows (red+cyan) are automatic on all words.
- SFX language: boings, pops, POW hits (cue sheet reflects it). R/S keys as always.

## Palette
cream #fdf3dc · red #e2262b · yellow #ffd400 · blue #1c6fd6 · black #17120e · cyan dots #37b6e2
14px black comic frame + caution-stripe footer are part of the identity.
