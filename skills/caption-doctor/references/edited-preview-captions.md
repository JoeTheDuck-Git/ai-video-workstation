# Captions on an approved edited preview

Use when the user requests subtitles on an existing cut, including a low-resolution sample for timing and scale adjustment. Retain the approved picture sequence, duration, frame rate and audio; save a new captioned file. Burn-in necessarily re-encodes video. Stream-copy audio where compatible and verify its packet payloads/timing. Do not re-edit, speed up or truncate speech to fit captions.

## Timing and text

- Bind the input video, transcript, and approved source-to-output map by path and hash. State whether timestamps refer to original media or final output. Map source words through retained intervals, or use the final audio's timed words. Never apply original timestamps directly to a cut output.
- Reconcile overlapping ASR windows before cue creation; do not duplicate their repeated words. At deleted retakes, compare source context and the final audio transcript. Inadequate word timing requires a local short-window alignment or an explicitly flagged uncertainty, not invented character-proportional timing.
- Keep semantic phrases together. Use word onset/end as the cue anchor. A small configurable lead (up to about 80 ms) and tail (up to about 150 ms) can help readability when bounded by neighboring speech and cuts; record the applied values. Avoid showing the next sentence early or leaving the previous one across unrelated speech.
- Prefer roughly 1–4 second cues, with 0.8 seconds as a warning threshold, not a reason to overlap another sentence. Merge compatible short fragments; flag unavoidable fast speech instead of silently deleting words. At most two lines; break at a phrase boundary, keeping numbers, units and proper names together.
- Preserve spoken meaning, negation and quantities. Use the creator's confirmed name/glossary. Numbers, dates or English names that disagree across transcripts remain `needs_review`; include their exact times in an uncertainty list and visibly mark uncertain wording in a draft when appropriate. Do not fact-correct the speaker or invent wording.
- Keep the farewell subtitle through the actual last word without extending beyond the media. Subtitle gaps are separate from audio pauses: do not alter audio to satisfy caption spacing.

## Short-phrase technology captions

The optional technology talking-head style uses short semantic captions, not an entire transcript paragraph on screen. Apply this preference when authoring new cues or when the user requests this restyling; do not silently re-time an existing SRT supplied only for spelling corrections.

- Prefer one line. If the current semantic phrase genuinely needs more width, wrap at a meaningful boundary into at most two lines. Readability and complete meaning take priority over a fixed character count. Measure the actual font width; do not mechanically cut every N characters.
- One spoken sentence may become several successive cues. Place each new cue at that phrase's actual speech onset and keep enough time to read it. Do not reveal the rest of a long sentence while the speaker is still on its first phrase. Use existing word anchors, not character-share duration estimates. If timing evidence is insufficient, flag it rather than invent precision.
- A line break within one cue shows both lines simultaneously and keeps one start/end pair. A new cue changes text later on the timeline and needs its own speech anchors. Do not treat these as interchangeable ways of shortening a line.
- Replace phrase commas (both `，` and `,`) with exactly two U+0020 half-width spaces between phrases. Preserve conventional numeric thousands separators (for example `1,234,567`); ambiguous numeric grouping remains for review. Usually omit ordinary terminal full stops. Retain question marks, exclamation marks and meaningful punctuation such as decimal points, quotations, list marks and uncertainty markers `〔待核對〕`; do not globally strip punctuation.
- Keep personal names, product names, English proper nouns, numbers and their units together within a line and cue. Retain negation and qualifiers with what they modify. A long protected name can justify a longer line or a two-line cue rather than splitting the name itself.
- Avoid one-word flashes, rapid successive cards and over-fragmentation. When a proposed phrase is too short to read, combine it with the adjacent semantically connected phrase if their speech timing supports that. Do not fix readability by showing unrelated later words early, overlapping cues, deleting meaningful words or changing the audio.

### Examples (illustrative wording, not this video's asserted transcript)

| Situation | Prefer | Avoid |
| --- | --- | --- |
| Speaker delivers two phrases in succession | Cue A `先把資料備份下來` at phrase A, then cue B `再等恢復入口打開` at phrase B | Showing both clauses from the start while phrase B is still several seconds away |
| One phrase is too wide for the chosen style | One cue with two lines: `這次更新支援 DJI Osmo 360` / `以及原始解析度匯出` | Splitting `DJI Osmo` / `360` or showing the second line later without creating a new timed cue |
| Declarative short phrase | `年化收入達到 1 億美金` | A card for `1 億` followed by a flashing `美金` card |
| Meaningful punctuation | `你還會繼續使用嗎？` / `真的回來了！` / `提升到 1.5 倍` | Removing `？` / `！`, or turning `1.5` into `15` |
| Phrase separator in one cue | `先備份  再登入` (exactly two U+0020 spaces) | Leaving `先備份，再登入`, collapsing to one space, or using a full-width space |
| Commas at a cue/line edge | `先備份，\n再登入` → `先備份\n再登入`; trailing comma → no trailing spaces | Indenting the next line, creating an empty cue, or carrying whitespace across a timed cue boundary |
| Numeric punctuation | `1,234 美金  成長 1.5 倍！` | Changing thousands commas or decimal points into spaces |

### Formatter order and boundaries

Author semantic cues first. Run `scripts/caption_style.py::format_technology_caption` after glossary/language/spacing normalization, then serialize that same text to SRT and ASS (`ass_text` preserves spaces and only encodes line breaks). Do not run whitespace collapsing afterward. The SRT cleaner exposes this as `--technology-style`; it rejects estimated `--reflow` in this mode. It does not invent short-phrase timing. The current preview builder uses the same formatter before measuring widths and writing both formats.

At line or cue boundaries, trim the replacement spaces: a comma ending a line/cue disappears rather than leaving trailing spaces or indenting the next line. A punctuation-only line is dropped; the cleaner omits an empty cue, while the preview builder flags it for the author to resolve before rendering. These are display changes only; preserve speech timing. Consecutive phrase commas collapse to one two-space separator. Reapplying the formatter must preserve those two spaces. A new render requires fresh caption review because old subtitle files and review hashes describe the old style.

### Short-phrase QA checklist

- [ ] No paragraph-sized transcript dump; each cue is a useful semantic phrase.
- [ ] One line preferred, maximum two; line wrapping and timed cue replacement are explicitly distinguished.
- [ ] Cue changes use the corresponding spoken phrase's word timing; later clauses are not prematurely revealed.
- [ ] Names, product models, numbers/units, negation and qualifiers are intact.
- [ ] Phrase commas become exactly two U+0020 spaces; numeric thousands commas remain. Cue/line edges are trimmed; ordinary terminal full stops are usually omitted. Meaningful punctuation and uncertainty markers remain.
- [ ] No fixed-character hard cuts, flashing cards or excessive fragmentation; duration and reading-speed warnings are reviewed in context.
- [ ] Final-output alignment, scalable font/safe margins, rendered glyph/width checks and uncertainty review below still pass. Record visual checks separately from actual listening.

## Scalable preview style

An adjustable 480p starting style: Traditional Chinese, white text with black outline, bottom center. Starting settings at 480 px picture height: font size 26, outline 2, bottom margin 30, left/right margin 40. Scale each by output height / 480, with an explicit override for user adjustment. Record the actual installed font family and renderer. Use ASS PlayRes equal to the actual frame dimensions; provide editable SRT, ASS, and a style settings file. Preserve aspect ratio. These are initial settings, not a universal layout requirement.

Measure every rendered line's width and inspect representative actual frames, including longest/two-line captions, numerals/Latin names, first/last cues, and cut boundaries. Check glyph availability and clipping in the renderer; a font name or character count alone does not prove it fits. Keep the user's subject visible. Do not claim current platform UI safe zones unless actually checked.

When sampling a future frame before burn-in, preserve or restore its output-timeline PTS before the subtitle filter. An input seek that resets timestamps can incorrectly show the first caption over every sampled frame. Check the visible words against the expected cue at the sampled timestamp; inspect the encoded output again after full rendering.

## Verification and delivery

- Programmatically check valid positive cue intervals, ordered cues, no accidental overlaps, no negative or out-of-bounds times, max two lines, readable duration/speed warnings, and speech-anchor deviation. Preserve a cue-to-evidence map, including corresponding source ranges from the approved edit map.
- Render representative frames before the whole sample. After render, check full decode, dimensions, rational FPS, frame count/duration, required audio stream and unchanged audio payload/timestamps; compare picture outside the caption region to the input.
- Have a different reviewer inspect the subtitle timeline, evidence, and representative rendered frames when independent review is requested. Preserve the actual reviewer report. List program checks, actual visual coverage, ASR-based timing checks and actual human/audio listening separately. ASR alignment is not proof of perceived synchronization.
- Deliver the captioned MP4 plus editable subtitles/settings and QA notes. Mark unresolved recognition and unheard timing as draft limitations. Do not reuse an earlier video's content approval for changed subtitle text, or publish local Skill edits unless requested.

The final SRT/ASS/cue map is authoritative after configured lead/tail adjustments. Record authored and displayed times separately, bound both to the same output, and inspect first/last cues. Overall user satisfaction does not resolve individual recognition or unheard audio findings.
