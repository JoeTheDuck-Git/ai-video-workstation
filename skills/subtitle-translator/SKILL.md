---
name: subtitle-translator
description: >-
  Translate a subtitle/caption .srt into another language while keeping the timing perfectly in
  sync. Use whenever the user wants subtitles in more languages — "translate my captions to
  English," "add Japanese subs," "make an English version of this SRT," "translate these subtitles,"
  or shares an SRT and a target language. The AI agent translates naturally and culturally (not
  word-for-word), keeps names, and condenses so each line is readable in its time; the bundled tool
  merges the translation onto the original timecodes and checks reading speed. Pairs with
  Caption Doctor (clean once, publish in every language). Handles any encoding; outputs UTF-8 SRT.
---

# Subtitle Translator

Turns one clean SRT into subtitle tracks for other languages, **preserving the original timecodes
exactly** so every version stays in sync. Best run *after* Caption Doctor — clean the master once,
then translate it to English / Japanese / Simplified / anything.

**Division of labour (same as Caption Doctor):** the *AI agent* does the translation — natural, culturally
adapted, condensed to fit the time. `scripts/subtitletranslator.py` does the mechanics: merge the
translation onto source timecodes, format for the target language, and run a **reading-speed check**.

## Why reading speed matters here
Chinese is compact; English, German, Spanish, Japanese often **expand**. A literal translation can be
correct but too many characters for the card's duration → unreadable. Subtitles favour brevity:
**condense the meaning, don't translate every word.** The tool flags any card over the limit
(CJK/JA ~9 cps, Latin ~17 cps); tighten those lines and re-run.

**Shared profile folder:** resolve `<project>/.ai-video-workstation/creator/`; create it in the writable project when missing. Read `editing-setup.md` and `creator-profile.md` before asking anything. If `editing-setup.md` lists regular publishing languages, offer those without asking. Never write profile data into the installed Skill.

## Workflow
1. Start from a clean SRT (run **Caption Doctor** first if it's raw auto-captions).
2. **The AI agent reads the source SRT and translates each card** into the target language:
   - natural and idiomatic, adapted to the culture (not literal),
   - **keep proper nouns / names** (Codex, CapCut, place & people names),
   - **condense** so the line reads comfortably in its on-screen time,
   - translate per card, but read the whole thing first so meaning flows across cards.
3. Write the translations as JSON keyed by the source card number:
   `{"1": "Today I'm going to show you", "2": "...", ...}` → save as e.g. `en.json`.
4. Run the tool per language:
```
python3 scripts/subtitletranslator.py <source.srt> --lang en --translations en.json --out <source.en.srt>
```
   English/Latin output automatically keeps short cues on one line and wraps only over-wide cues
   at a semantic phrase boundary. Read `references/english-caption-layout.md` before producing
   English or bilingual subtitles.
5. If the report flags **too-fast** cards, shorten those translations in the JSON and re-run.
   If it flags a cue as wider than two visual lines, split that source cue at real word timings;
   do not shrink the font or leave a long paragraph on screen.
6. Import each `<source.LANG.srt>` into the editor as a separate subtitle track.

## Target-language handling
- `--lang zh-hant` / `zh-tw` → OpenCC **s2twp** (Taiwan Traditional) applied automatically.
- CJK–Latin spacing added for all targets (先用 Codex). Timing is never changed.
- Reading-speed limit auto-set by script family; override with `--max-cps`.
- Run once per language; each writes its own SRT.

## Quality checklist
- [ ] Translation reads naturally to a native speaker — not literal, not machine-stiff.
- [ ] Names/brands kept; culture-specific references adapted, not transliterated.
- [ ] Reading-speed report shows 0 too-fast cards (or you deliberately accept them).
- [ ] Timecodes identical to the source (the tool guarantees this — don't hand-edit).
- [ ] English: one visual line when it fits; at most two natural lines; no orphan word.
- [ ] Output is UTF-8 SRT; card count matches the source.

## Bundled assets
- `scripts/subtitletranslator.py` — merge translation onto timecodes, target formatting, reading-speed QC.
- `examples/` — a Traditional-Mandarin source and its English translation (timing identical).

## Pairs with
- **Caption Doctor** — clean & fix the master first, then translate. Same SRT pipeline, same reliability.
- **HyperFrames** — import the approved language track for subtitle styling and burn-in.

Use the managed AI Video Workstation Python environment. On macOS/Linux it is
`~/.local/share/ai-video-workstation/python-venv/bin/python3`; on Windows it is
`%LOCALAPPDATA%\AI-Video-Workstation\python-venv\Scripts\python.exe`. The installer supplies
`opencc-python-reimplemented`; never use `--break-system-packages`.
