---
name: caption-doctor
description: >-
  Clean ANY subtitle / auto-caption .srt from any source — CapCut, DaVinci, YouTube, Premiere,
  Whisper, Rev, Zoom, Descript, or any tool that exports SRT — and hand back a clean SRT that
  re-imports into any editor. Use whenever the user has messy captions/subtitles
  and wants them fixed: recognition errors, Simplified→Traditional, awkward mid-phrase line
  breaks, missing punctuation, bad timing, spoken English mis-transcribed. Trigger on "fix my
  captions," "clean the subtitles," "the auto-caption got X wrong," "make these captions
  Traditional," "fix this SRT," or when a caption/subtitle/.srt file is shared. Reads the
  transcript, fixes errors by MEANING, and outputs a clean UTF-8 .srt. Built for Taiwanese
  Mandarin (繁體中文) but works in English too.
---

# Caption Doctor

Auto-captions and subtitles from **any source** (CapCut, DaVinci, YouTube, Premiere, Whisper,
Rev, Zoom, Descript, hand-made SRTs…) are fast but sloppy: they mishear words, output Simplified
even for Taiwanese speakers, break lines mid-phrase, drop punctuation, and mistime. Caption Doctor
works on any `.srt` and hands back a clean one that re-imports into any editor (CapCut: *Captions →
Add Captions*; most editors: *Import → Subtitle*). No timecode round-trip — timing is preserved.

**Division of labour:** the *AI agent* reads the transcript and decides the **recognition fixes**
(it understands meaning — it knows "clot" was "Codex" and "代辦事項" should be "待辦事項"). The
bundled `scripts/captiondoctor.py` does the mechanical work: Traditional conversion, CJK–Latin
spacing, filler-drop, SRT output — while preserving the original timecodes.

## The four fixes
1. **Recognition errors** — the AI agent supplies a corrections list from reading the transcript in
   context (homophones, brand/tech names, Taiwanese slang). Passed to the tool as `--fix`.
2. **Traditional Mandarin** — Simplified is converted with OpenCC **`s2twp`** (Taiwan vocab);
   already-Traditional lines are left untouched so domain words like **腳本** aren't mangled.
3. **Line breaks** — mid-phrase fragments are merged, then re-split into readable lines of
   `--maxlen` characters, re-timed by character share. (Short-form: 12–14 chars reads best.)
   For English/bilingual delivery, follow Subtitle Translator's
   `references/english-caption-layout.md`: one semantic cue, one line when possible, and only wrap
   to two lines when the rendered width genuinely cannot fit.
4. **Timing** — enforces a minimum on-screen duration and removes overlaps.

## Language mode — DEFAULT: all Traditional Mandarin (Taiwan)
The finished caption track should be **one language: Traditional Mandarin (繁體中文, Taiwan)**.
- **Spoken English → translate to natural 繁中.** Auto-transcribers mangle spoken English into wrong
  Chinese homophones (e.g. "Codex" → 扩/阔) or leave it garbled. The AI agent must recognise it was
  English and render the *meaning* in Traditional Mandarin — e.g. "this is a game changer" →
  「這真的改變了一切」.
- **Keep genuine proper nouns as-is** — product/brand names and people's names stay in their real
  form (Codex, CapCut, iPhone). Don't phoneticise or translate a name.
- Net effect: no stray English words, no Simplified, natural Taiwanese phrasing throughout.
- *(Alternate mode if asked: "faithful bilingual" — keep English where the speaker spoke English.)*

## Step 0 — Interview the user first, then save a reusable profile
Corrections are far better when you know the creator's world **before** reading the transcript.

**Shared profile folder:** resolve `<project>/.ai-video-workstation/creator/`; create it in the writable project when missing. Read `editing-setup.md` and `creator-profile.md` before asking anything, and save the caption glossary there. Never write profile data into the installed Skill.

**If a profile already exists** (look for `editing-setup.md` / `creator-profile.md` +
`caption-glossary.txt` in `.ai-video-workstation/creator/`), load them and skip the questions — only ask about
anything genuinely new.

**Otherwise, interview the user with 一個簡短問題 (one quick round):**
1. **Niche / field** — what are your videos about? (beauty, gaming, tech, cooking, finance, travel,
   fitness…) → primes you for the domain jargon the transcriber will mishear.
2. **Recurring wrong words** — names, brands, products, or terms the auto-captions always get wrong?
   (their own name, channel name, products they mention, English terms) → each becomes a glossary
   entry `wrong=>right` (e.g. `扩=>Codex`).
3. **Preferences:**
   - Traditional Taiwan? (default yes)
   - Spoken English → translate to Mandarin (default) or keep bilingual?
   - Drop filler cards 嗯/呃? (default yes)
   - Any punctuation or line-style preference?

**Save the answers** so the user never repeats them:
- `.ai-video-workstation/creator/caption-glossary.txt` — one `wrong=>right` per line (`#` comments allowed). Grows over time:
  whenever you catch a NEW recurring error while fixing, append it here.
- the niche goes into `.ai-video-workstation/creator/creator-profile.md`, the preference choices into
  `.ai-video-workstation/creator/editing-setup.md` (update existing files rather than duplicating them).

On every later run, pass the glossary with `--fix-file <project>/.ai-video-workstation/creator/caption-glossary.txt` and apply the saved
preferences automatically. The skill gets smarter each time it's used.

## Step 1 — Get the raw captions (any source)
Any `.srt` works — the tool only needs a valid SRT. Common exports:
- **CapCut**: Captions → Auto captions → Export as SRT.
- **DaVinci**: Create Subtitles from Audio / AutoSubs → export SRT.
- **YouTube Studio**: Subtitles → download .srt. **Premiere**: export captions as SRT.
- **Whisper / Rev / Zoom / Descript**: export/download the .srt.
Import back into whatever editor you use (CapCut: Captions → Add Captions; others: Import → Subtitle).

Robust to real-world files: accepts **.srt or .vtt**, and auto-detects the encoding
(**UTF-8, GBK/GB2312 Simplified, or Big5 Traditional**) — students' files are often not UTF-8.

**Runtime:** use the AI Video Workstation Python environment installed with this Skill. On
macOS/Linux it is `~/.local/share/ai-video-workstation/python-venv/bin/python3`; on Windows it is
`%LOCALAPPDATA%\AI-Video-Workstation\python-venv\Scripts\python.exe`. The installer supplies OpenCC
and jieba there. If the environment is missing, run the workstation installer or verification script;
never use `--break-system-packages` or modify the system Python.

## Step 2 — The AI agent reads and corrects
Read the SRT. List every likely misrecognition with its fix, using meaning and context:
- homophones / near-homophones (待辦↔代辦, 帳號↔賬號),
- brand & tech names the recognizer won't know (Codex, CapCut, app names),
- Taiwanese-Mandarin words and slang,
- obvious wrong characters (溜溝→溜狗).
Do **not** rewrite the speaker's phrasing — only correct genuine errors. Keep it verbatim.

## Step 3 — Run the tool (default = PRESERVE original timing)
```
~/.local/share/ai-video-workstation/python-venv/bin/python3 scripts/captiondoctor.py <raw.srt> --out <clean.srt> --drop-fillers \
    --fix-file caption-glossary.txt \
    --fix "代辦=>待辦; 指令碼=>腳本; 4點=>四點"
```
- `--fix-file` — the user's saved glossary (from Step 0). `--fix` — additional per-clip corrections
  the AI agent spots while reading. Both are merged.
The default fixes only the **text** and keeps every original timecode **exactly** — so captions stay
perfectly in sync with the audio. This is the single job of the skill, and what you want ~always.
- `--fix "a=>b; c=>d"` — the AI agent's corrections, applied **before and after** conversion (so it also
  undoes s2twp domain errors like 指令碼→腳本). Put number-style fixes here too (4點→四點).
- `--drop-fillers` — removes lone 嗯/呃/啊 cards.
- Automatic: Traditional (`s2twp`, smart) + CJK↔Latin spacing, digits included (先用Codex → 先用 Codex; Pocket 3跟 → Pocket 3 跟).
- Dependencies: OpenCC and jieba are installed in the managed AI Video Workstation environment.

The tool prints a **reading-speed report** flagging any card that is over-long or too fast, so you
can spot the few you might hand-break in CapCut — *without the tool re-timing anything*.

### Scope discipline — one job, done well
Caption Doctor **cleans language and preserves timing.** It does NOT re-cut lines to a target length
by default, because shortening a line means re-timing its pieces by guesswork (the SRT has no
word-level timing), which trades away CapCut's correct sync for a styling preference. Line length /
wrapping is CapCut's job; the word-by-word "karaoke" look is **CapCut's built-in word-by-word
captions** (they carry real word timings). Don't rebuild those here.

### Advanced only: `--reflow`
`--reflow --maxlen 8` re-chunks long lines (word-aware, via jieba). **It re-times split cards by
estimate and can drift from the audio** — off by default, use only if a client insists on shorter
lines and accepts the drift.

## Step 4 — Import to CapCut
CapCut Desktop/Web: **Captions → Add Captions → pick `<clean.srt>`** (UTF-8). Each line becomes
an editable caption. Style once and "Apply to all."

## Quality checklist
- [ ] Every correction is a real error fix, not a rephrase; verbatim meaning kept.
- [ ] Traditional 繁體中文 (Taiwan); no 腳本→指令碼 mangling; spoken English handled per language mode.
- [ ] Names/brands intact (Codex, CapCut); numbers consistent (四點, not 4點).
- [ ] Word-aware breaks: no split words/names/English; no stranded single characters; ≤ maxlen.
- [ ] Reading speed OK (report shows 0 flagged, or you accept them); ≥ 0.8s each; gaps between cards.
- [ ] Valid UTF-8 SRT; no overlapping timecodes.

## Bundled assets
- `scripts/captiondoctor.py` — the cleaner (fixes, s2twp Traditional, line reflow + re-time, SRT).
- `examples/` — a real before/after (raw NZ auto-caption → cleaned).

## Pairs with
- **Subtitle Translator** — feed the cleaned SRT in to get other languages.
- **HyperFrames** — import the cleaned SRT only after text and timing are approved; use HyperFrames for styling and burn-in.
