# Style 08 — Neon 霓虹 (night-sign) ★ LOCKED v1.0 · 2026-07-04

A physical neon sign on a dark night wall. Every element is a GLASS TUBE: visible as
unlit dark glass before ignition, lights with buzz-flicker, and can die. Third dark
style but a different object entirely: VHS is a screen, DarkTerm is a terminal — Neon
is a thing hanging outside a shop at 2 AM. For hustle/深夜/城市感 creators — the
"night-shift romance" register.

## Card types — route by pasted content
| Context contains… | Build | Template |
|---|---|---|
| one line with a rejected idea + a payoff | 文字卡 | `templates/neon.html` |
| a list, routine, framework, step menu | 菜單卡 night-diner menu | `templates/neon_menu.html` |
| numbers, stats, results | 計分板 glowing scoreboard | `templates/neon_score.html` |

## The emphasis vocabulary (unique — never borrow)
- `key:true` — STUTTER-START ignition: tries to light, fails twice, then BANG — full
  hot pink, and the wall's glow pool warms from cyan to pink. Color-of-light is the
  emphasis, not size.
- `out:true` — the tube SHORTS OUT: lights normally with the others, then electrical
  crackle → dies to dark glass (still legible as unlit tube). Twitches faintly every
  few seconds afterwards. The strike = a broken sign.
- 菜單卡: rows ignite down the board with dotted tube leaders; ONE `focus:true` item =
  tonight's special (bigger, pink, Latin script tag blinks beside it). The joke lives
  in the last item's value (準時睡覺 ⋯ 無價).
- 計分板: tube digits COUNT UP while flickering on; ONE `hl:true` stat pink, bigger,
  lights last + script tag. Source line MANDATORY — never invent data (mark 示意).
- Latin script accents ('Mr Dafoe') = small secondary signs (open 24 hrs / new record).
  Latin only — CJK never goes in script font.

## Directing rules
- The sign is ALWAYS present: unlit words show as dark glass (--dead #27303f) before
  igniting — never fade in from nothing. Ignition order = reading order, key/focus/hl
  always LAST.
- Ambience: wet-street reflection under the main sign (-webkit-box-reflect), sagging
  power cable silhouette, glow pool on the wall, corner marks are unlit painted text.
- No camera, no shake, no scanlines (scanlines = VHS). Energy comes from flicker
  timing, not motion.
- SFX language: low electrical hum bed under everything; buzz-flicker per ignition;
  crackle for the short-out; one bass bloom for the key word. 4–6 cues.
- O outro = POWER CUT: every tube dies to dark glass in a fast ragged stagger (70ms
  steps). Hold the dead sign a beat before cutting. R / S as always.

## Palette
night #07090f · wall #10141f→#05060a radial · base tube: core #f2fbff / glow #3ec6ff
(ice cyan) · key tube: core #fff2fb / glow #ff4fc8 (hot pink) · dead glass #27303f ·
dim paint #5a6b80. Overrides: accentKey / accentBase (e.g. accentKey:"#ffd24d" for
gold). Fonts: Noto Sans TC 900 (tubes) · Mr Dafoe (Latin script signs only).
