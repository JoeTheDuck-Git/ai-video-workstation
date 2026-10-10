# Style 10 — Split-flap 翻牌看板 (departure board) ★ LOCKED v1.0 · 2026-07-04

The final style. A mechanical station departure board: every character is a flap tile
that CLATTERS through random characters (decelerating) and locks with a clack. The
studio's only mechanical/tactile system — the rhythm IS the style, and the SFX cue
sheet matters more here than anywhere else. For 旅行/日常 vlog/成長敘事 creators —
the "journey" register.

## Card types — route by pasted content
| Context contains… | Build | Template |
|---|---|---|
| one line with a rejected idea + a payoff | 文字卡 | `templates/flap.html` |
| a schedule, routine, step list, day plan | 時刻表卡 timetable | `templates/flap_board.html` |
| numbers, stats, results | 數字卡 flap digits | `templates/flap_stats.html` |

## The emphasis vocabulary (unique — never borrow)
- `key:true` — after everything lands, the word RE-SHUFFLES tile by tile and locks
  INVERSE AMBER (amber tile, dark char) + an amber frame snaps around it. Emphasis =
  the board singles out one service.
- `out:true` — the word re-flips to red em-dashes「—」+ 已取消 tag: a cancelled
  service. The strike stays legible as dead tiles.
- 時刻表卡: TIME | SERVICE | STATUS columns, all tiles, columns aligned (short names
  pad with blank tiles). status 延誤 = red chars on normal tiles (a third state
  between 準時 and cancelled); ONE `focus:true` row's status flips LAST to 登機中 on
  amber + row frame. Punchline lives in the last row (23:00 上片 登機中).
- 數字卡: values spelled in flap tiles (digits/units all flip); ONE `hl:true` row
  flips last, all-amber + frame + label turns amber. Source line MANDATORY.
- Ambient signature: every few seconds a random settled tile "re-adjusts" itself
  (sticky flap) — keep it; it's what makes the board feel real on a long hold.

## Directing rules
- The board FLIPS, it never fades — words arrive in reading order, key/focus/hl
  always last. Blank tiles are part of the board; don't collapse them.
- Tiles use ONE font only ('Noto Sans TC') — mixing a Latin-first stack makes Safari
  seat CJK glyphs on the wrong baseline inside the fixed tiles (CJK-in-container
  rule; single-font flex-centering is the lightweight escape hatch).
- Furniture: amber header + hairline (出發/今日班次 + tracked EN), live clock
  (`clock:"auto"`), painted corner marks (PLATFORM 10). Wall has faint vertical
  brushed strips — no other texture.
- No camera, no glow (glow = Neon), no shake. Energy = clatter timing. SFX language:
  vestibule hum bed, station chime, flap clatter per row, hard clack for the
  cancellation, tile-by-tile clacks + low thunk for the amber lock. This style sells
  ~90% on sound — always deliver the S cue sheet.
- O outro = the board CLEARS: every tile cascades back to blank, L→R. R / S as always.

## Palette
board #0f1114 · tile #22262e→#191c22 (split line + side pins) · flap char #f2f0e6
(warm off-white) · amber #ffb02e (inverse tile, ink #191204) · cancelled red #e0483e ·
painted dim #6a707c
Fonts: Noto Sans TC 900 (all tiles — single font, see rule) · Inter (painted Latin
furniture only, never in tiles).
