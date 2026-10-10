# Style 01 — Vox 紀錄片 (kinetic documentary) ★ LOCKED v1.0 · 2026-07-04

Approved by the pack author as the pack's first style. The four card types, the cinematic layer,
the newsprint-only image rule, and the motion defaults below are the reference standard —
future styles (02–10) should match this bar. Don't restyle this without her sign-off.

**Look:** warm paper + faint grid, heavy 900 sans headline, red hand-drawn ink, yellow
highlighter, mono archive furniture. The Johnny Harris / Vox explainer energy.

## THREE card types — route by what the user pasted, not by default
Real Vox pieces are mostly NOT text cards. When the user pastes context (a script chunk,
a stat, an argument), read it and pick the form that *shows* the idea:

| The pasted context contains… | Build | Template |
|---|---|---|
| numbers, %, rankings, a comparison, growth/decline | **數據卡 chart** (bar or line) | `templates/vox_chart.html` |
| quotes, headlines, reports, "everyone says…", history, controversy | **剪報卡 newspaper cutouts** | `templates/vox_news.html` |
| MULTIPLE factors/causes/subjects that converge on one idea — an explanation | **解釋板 evidence board** | `templates/vox_board.html` |
| one punchy declarative line (no data, no sources) | **文字卡 kinetic text** | `templates/vox.html` |

A 60s explainer typically wants a MIX — offer the set: 「這段我會做三張卡：一張數據、
一張剪報、一張金句」. Edit only each template's `CONFIG` block.

**Chart rules:** use the USER'S real numbers and real source — never invent data; always
fill `source` (Vox always cites). Exactly one `hl:true` datum — that's the story. Bar for
comparisons (safest both orientations), line for change-over-time.
**Board rules:** the card for 「為什麼」moments — when the script names several causes,
pieces of evidence, or players behind one outcome. Center = the ONE idea (use `<br>` to
balance the line break); 3–5 satellite nodes mixing types (`stat` needs a real number,
`clip` a real source, `term` the concept-words); every string label answers "how does this
piece relate?" (證據／直接原因／隱形殺手…). Camera starts tight on the center and pulls
back as the pieces land — the reveal IS the explanation. Demo configs: `demos/`.
**News rules:** 2–4 clippings, exactly one `focus:true` (lands last, gets highlighter +
circle + tag + camera push-in). Paraphrase the user's REAL sources; real outlet + real
date when known, generic masthead (「產業週報」) when not — never fabricate a real
outlet saying something it didn't. `<mark>` wraps the key phrase in the focus headline.

## Motion system (what makes it feel expensive)
- **Camera rig**: 9s push-in (`camera.push`) + 3-plane parallax drift (`camera.drift`),
  plus an automatic **punch** (snap-zoom pulse) on the key-word reveal.
- **Word reveals** (`motion`): default `"rise"` — fast, confident rise-and-settle with a
  1.2% overshoot, ±0.8° tilt, no blur (the true Vox feel: text is calm, INK is the drama).
  `"slam"` = heavy oversized crash-in with blur — only when the user asks for aggressive/
  hype energy. The stagger automatically breathes (×1.7 pause) right before the key word —
  don't fight it, write the line so the key word lands last or near-last.
- **Ink suite** (all auto-measured to the real word boxes, all draw-on with jitter):
  highlighter sweep → circle (300ms later) → arrow + handwritten tag (750ms later) on the
  `key` word; rough strike on `strike`; underline on `under`.
- **Splice flashes**: 2-frame white flash on first slam and key reveal (with a scratch).
- **Film grain** at 7% multiply, always moving; content holds from ~5s (record ~6-7s).

## Directing rules (the AI agent's job when filling CONFIG)
- Lines: 2 lines, 3–7 CJK chars per word chunk, ≤ ~10 chars/line. Chunk by MEANING
  (「被記住」 is one word object, not three).
- Exactly ONE `key` word — the emotional payload. `strike` = the rejected idea (optional
  but powerful: 不是Ⅹ…是Ｙ structures are the signature Vox move).
- `tag` ≤ 6 chars, adds a *new* thought (not a repeat of the key word).
- Copy in 繁體中文（台灣）by default; eyebrow is the video's section title.
- `orientation`: "portrait" for Reels/Shorts, "landscape" for YouTube. For portrait with
  1-2 short lines, consider bumping `.portrait .word` font-size 118→132px.
- `backdrop:"map"` adds topo contours + a route that draws itself + pin drop — use when
  the line is about a journey/place; otherwise keep "paper".

## Cinematic layer (automatic in all four cards — don't disable)
- **Rough ink**: every stroke runs through an SVG turbulence filter — marker on paper
  fiber, not vector curves.
- **Handheld camera**: layered non-repeating drift + micro-rotation. `camera.drift:0` only
  if the user explicitly wants a locked-off look.
- **Focus pulls**: news card defocuses non-focus clippings during the push-in; board racks
  focus from the center card to the evidence and back for the conclusion.
- **Record keys**: `R` = 3·2·1 countdown then clean restart; `S` = toggle the SFX cue
  sheet (exact timestamps for whoosh/thunk/splice/scribble). Tell the user both, always.

## Images — ALWAYS as printed newspaper photos, never polaroids
the pack author's call: the visual world is newspaper collage, period. When the user has an image
(their screenshot, a frame from their footage), it goes INSIDE a clipping as a printed
news photo — heavy grayscale, high contrast, slight sepia — via `img:` on a news-card
clipping or a board `clip` node. Path relative to the .html (same folder easiest).
No polaroids, no tape-framed photos, nothing outside the newsprint language.

## Palette
paper #f4efe3→#e9e2cf · ink #191510 · accent red #c94f34 · highlighter #f5c842 · mono #6b6252
Brand-teal variant: set `accent:"#00a8a0"`.
