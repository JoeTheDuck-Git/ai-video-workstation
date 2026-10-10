# Style 05 — Pastel Code 粉彩程式 (soft saturated pastels × coding vibes) ★ LOCKED v1.0 · 2026-07-04

the pack author's brief: 「AI coding design language — soft yet saturated pastel colours, courier
coding vibes, light and airy.」 Warm ivory, big drifting pastel blobs (sage/sky/butter/
lavender, blurred to air), Noto Serif TC warmth + Courier Prime code chrome, coral accent.
For AI/tech/productivity/知識型 creators — the cozy-intelligent register.

## Card types — route by pasted content
| Context contains… | Build | Template |
|---|---|---|
| one line with a keeper + a rejected idea | 文字卡 | `templates/pastel.html` |
| a method, routine, framework, how-to | 終端機步驟卡 | `templates/pastel_steps.html` |
| a journey, 成長史, timeline, before/after arc | 提交紀錄卡 git log | `templates/pastel_log.html` |
(Data needs → borrow Minimal's chart with `accent:"#d97757"` until this style grows one.)

## The emphasis vocabulary (unique — never borrow)
- `key:true` (text card) — the word becomes an **inline code chip**: coral, rounded,
  TYPES itself in with a cursor, then a ✳ sparkle badges its corner and twinkles.
- `dep:true` — the rejected idea gets a **linter squiggle** + floating tooltip (its
  `tip`, e.g. "// 已棄用 deprecated"). The gentlest strike in the Studio.
- 步驟卡: commands type after coral `>` prompts; each confirms with a sage `✓ done` line;
  ONE `focus:true` step runs in coral and earns ✳. The rhythm IS the typing.
- 紀錄卡: commits pop down the rail with auto-hashes; ONE `key:true` commit in coral with
  a pill `badge` ("HEAD → 現在的你") + ✳. Counters/hashes are set dressing; the messages
  carry the story.
- tag (text card) = terminal prompt line, keeps its blinking cursor forever.

## Directing rules
- Motion is EXHALE-soft: floats, fades, typing. No impacts, no shake, no camera push.
  If the line wants punch → wrong style (Pop/VHS), don't harden this one.
- Copy register: reflective, encouraging, 知性 — the demo lines are the tone guide
  (別再等完美腳本…先跑初稿再迭代).
- Eyebrows are code comments (// …); status bars stay quiet and cute (已儲存 ✓).
- SFX language: soft keyboard taps, air, one clean ✳ chime; 2–4 cues total.
- O outro = lift-and-dissolve (closing the laptop). R / S as always.

## HARD ENGINEERING RULE (learned over 4 rounds)
Any text inside a chip/pill with CJK: canvas-measure the ink
(actualBoundingBoxAscent/Descent) and render as SVG <text> with computed baseline
y=(H+(a-b))/2 in a fixed-size box. Never padding/line-height/flex-center alone — Safari
seats CJK fallback glyphs differently. The text card's chip is the reference
implementation. Latin-only pills (badges) may use normal CSS.

## Palette
ivory #f2efe7 · card #fbf9f3 · ink #3d3629 · soft #9a917e · coral #d97757 ·
sage #a9c3a2 · sky #a9c4de · lavender #c7b5d8 · butter #f0d494 · squiggle #e06c5a
Fonts: Noto Serif TC 900 (human words) · Courier Prime (all code chrome) · Noto Sans TC.
