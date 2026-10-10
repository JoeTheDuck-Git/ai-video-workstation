# Style 02 — Minimal 極簡 (corporate clean) ★ LOCKED v1.0

The deliberate opposite of Vox: no paper, no ink, no grain, no camera shake. One accent
color, three font weights, hairline rules. Precision IS the style. For 知識型／B2B／
finance／tech creators who'd never touch grunge.

## Card types — route by pasted content
| Context contains… | Build | Template |
|---|---|---|
| one declarative line / a contrast (Ⅹ vs Ｙ) | 文字卡 | `templates/minimal.html` |
| numbers, %, comparisons | 數據卡 | `templates/minimal_chart.html` |
| a method, framework, N 個步驟, how-to | 步驟卡 | `templates/minimal_steps.html` |

## Directing rules
- **Fewer words than Vox.** This style dies under clutter — max ~8 chars/line on the text
  card, 3–5 steps, 3–5 bars. If the content is rich, make two cards.
- **Emphasis vocabulary** (never mix with Vox's): `key:true` = accent color + 700 weight +
  hairline underline. `dim:true` = the rejected idea recedes to gray (the corporate
  strike-through). Steps: ONE `focus:true` max. Chart: ONE `hl:true`, emphasized by color
  + a single soft pulse — never a drawn circle.
- **`theme:"dark"`** (keynote black) for tech/premium/評測 content; light is default.
  `accent:""` default blue; `"#00a8a0"` teal as an example brand accent (use the creator's brand color from `_creator/broll-profile.md` or Nora's `_brand/`).
- **Titles** accept `<b>` for the one bold phrase (三步驟，讓影片<b>被看完</b>).
- Chart: real numbers + `source` mandatory, same as Vox. Notes ≤ 8 chars.
- Motion is slow and few: nothing slams, nothing shakes. Don't add energy with timing —
  if it feels flat, the COPY is flat.
- SFX language: soft ticks and air, 2–3 cues total (the cue sheet reflects this).

## Hard guardrails
No texture, no rotation, no handwriting fonts, no ink SVG, no splice flashes. If the user
asks for "more energy," that's a signal they want a different style (Vox/Hype), not a
louder Minimal.

## Palette
light: bg #fbfbfa · ink #16181d · soft #8a8f98 · rule #e6e7e9 · accent #2456e6
dark:  bg #0f1013 · ink #f2f3f5 · soft #7f858e · rule #24262b · accent #5b82ff
Record keys: `R` = 3·2·1 restart · `S` = SFX cue sheet (same as Vox).
