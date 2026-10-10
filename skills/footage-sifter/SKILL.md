---
name: footage-sifter
description: >-
  Sift a dump of raw clips into an organized, ready-to-edit project: ruthless cull, takes
  grouped, the best take picked per group, a selects order, safe rename+sort scripts, and a
  DaVinci selects timeline (FCPXML). Use whenever the user has a pile of unorganized footage
  and wants order — "sort my footage," "which take is best," "cull these clips," "organize my
  SD card dump," "build a selects timeline," "幫我整理素材" — or shares a clip list, folder
  listing, or per-clip transcripts. Works for multi-take talking-head, vlogs, interviews, and
  product B-roll. Outputs plain files any editor imports; nothing touches the originals until
  the user runs the (reviewed) rename script.
---

# Footage Sifter

The "ruthless cull → selects" pass is mandatory and hated. Footage Sifter turns a raw clip
dump into: a **cull report** (every clip judged, with reasons), takes **grouped** by content,
one **select** per group, a **selects order** (the rough assembly), **rename scripts** that
sort files into `01_精選 / 02_備用 / 03_淘汰`, and a **selects.fcpxml** that lands
the trimmed selects on a DaVinci timeline in order.

**Output language — DEFAULT: 繁體中文（台灣）.** The report, rename-script comments, and
folder names are Traditional Mandarin out of the box (the pack's audience). The AI agent's
`reason` fields should be written in 繁體中文 too. Pass `--en` for English outputs, and
write reasons in English, only if the user works in English.

**Division of labour (same as Caption Doctor / Subtitle Translator):** the *AI agent* makes every
editorial call — **by looking at the footage first** (extract frames and read them; §Step 1),
then spotting retakes of the same content, judging which take is best and *why*, ordering the
selects like a story, naming clips descriptively. It writes those judgments into a `sift.json`
manifest. The bundled `scripts/footagesifter.py` does the mechanics: validates the manifest,
reads real specs from the files (ffprobe: fps, resolution, rotation, duration), and writes the
output files.

**The one rule that keeps this trustworthy: judge on what you SEE, never on metadata.**
Duration, file size, and timestamps describe a clip; they do not tell you if it's in focus,
well-lit, well-framed, or a retake. A 5-second clip can be a perfect insert; a 90-second clip
can be an unusable ramble; two clips a minute apart can be a dog-walk and a sunset, not "two
takes." Whenever the actual video files are reachable, the frames are the evidence and
metadata is only for sorting/labelling. Metadata-only judging is a last resort (§Step 1) and
may never `reject`.

## Step 0 — Get the raw material (best first)
1. **The actual clips (best by far)** — a reachable folder of video files. In local agent
   sessions this is the normal case: you can extract frames and *watch* them (§Step 1). Run
   `ls -la` for the inventory, but treat the pixels, not the filenames, as the evidence.
2. **Per-clip transcripts** — CapCut/DaVinci auto-transcribe per clip; the user exports SRT/TXT.
   Great for talking heads: near-identical transcripts = retakes of the same beat. Use
   *alongside* the frames, not instead of them.
3. **The user's descriptions** — "4021 to 4023 are my intro attempts, 4030 is coffee-shop B-roll…"
4. **Filenames + timestamps only (last resort)** — when no files, transcripts, or descriptions
   are available. Clusters of same-minute timestamps *hint* at takes, but you are blind to
   content: soft verdicts only, never `reject` (§Step 2, thin-evidence rule).

If media file paths are accessible, pass them as `"media"` in the manifest — the tool reads
fps/resolution/duration directly (handles rotated phone footage). If not, ask for or estimate
`"duration"` per select (the tool refuses to guess).

## Step 1 — WATCH the footage (mandatory whenever the clips are reachable)

Do this before writing a single verdict. It is the eyes of the sift and the difference
between a trustworthy cull and a confident-but-wrong one.

```
bash scripts/contactsheet.sh "/path/to/clips"
# 沒有 ImageMagick（montage）時它會自動改跑內建的 ffmpeg-only 版本；也可以直接跑：
bash scripts/contactsheet_ffmpeg.sh "/path/to/clips"
```

**Missing tools on the student's machine — do NOT send them to install anything.** Most student
Macs have no Homebrew, so `montage` and a PATH `ffprobe`/`ffmpeg` are usually missing. That is fine:
- No `montage` → `contactsheet.sh` hands over to `contactsheet_ffmpeg.sh` by itself (one labelled
  strip per clip in `_sheets/<clip>.jpg` instead of combined `sheet_N.jpg` — read those instead).
- No `ffmpeg`/`ffprobe` on PATH → the AI Video Workstation installation is incomplete. Run
  its verification script and repair the managed FFmpeg installation before continuing.
- If a script prints `!! montage failed` / `!! could not read any frame`, re-run with
  `contactsheet_ffmpeg.sh`; a clip that still yields no frame is likely corrupt — say so in the report.

This extracts frames from every clip (3 for clips ≥10s, **6–8 for clips <10s** — sparse
sampling lies about short inserts that end on an empty frame *on purpose*), labels each with
its filename + duration, and tiles them into `_sheets/sheet_N.jpg`. It also prints a clip
list with durations.

**Then actually read every `sheet_N.jpg`.** For each clip note, from the pixels: the subject,
the shot type (talking head / B-roll / interview / demo), framing, exposure, focus, stability,
and whether it's a genuine retake of a neighbour or just a different shot. These observations —
not durations — become the `reason` fields. If a clip is ambiguous from the sheet (needs to
hear the audio, or motion matters), extract more frames for just that clip before ruling on it.

Only if the video files are genuinely unreachable (a listing was pasted, footage is on a
disconnected drive) do you skip this — and then the thin-evidence rule in Step 2 caps every
verdict at `backup`.

**Shared profile folder:** resolve `<project>/.ai-video-workstation/creator/`; create it in the writable project when missing. Read `editing-setup.md` and `creator-profile.md` before asking anything, and save `sift-profile.md` there. Never write profile data into the installed Skill.

## Step 2 — The AI agent judges (the actual sift)

### First: detect the shot type of EACH clip — a real dump is mixed
One SD card holds intro takes, scenery pans, and an interview answer. Detect per clip, then
judge each clip by ITS type's rules — never apply one standard to the whole folder:
- transcript with fluent first-person speech → **talking head**
- no transcript / no speech / ambient-only, esp. short clips → **B-roll / scenery**
- two voices trading turns, question-answer shape → **interview**
- speech that narrates on-screen actions step by step → **demo / tutorial**
The user's description always outranks detection; detection outranks any assumption.

### Judging rules by shot type
| Type | Group by | Selects per group | Judge on | Reject when |
|---|---|---|---|---|
| Talking head | same content beat (near-identical transcripts) | **exactly one** | delivery: energy, clean read, complete thought | a clearly better take of the same beat exists |
| B-roll / scenery | subject/location | **several is correct** — keep coverage options (wide/close, angles) | variety, steadiness, light, usable length | technically unusable (shake, focus) or true duplicate angle |
| Interview | question/topic, not take | one per question, but **never reject unique content** | completeness + authenticity of the answer | only trims of redundant restatements |
| Demo / tutorial | feature/step | one per step | **completeness first** — a flat take showing every step beats an energetic one missing a step | a step is missing or wrong |

### Then decide per clip:
- **group** — which content beat it belongs to ("opening hook", "coffee-shop B-roll"…).
  Near-identical transcripts, or same-minute timestamps + similar length, mean one group.
- **verdict** — `select`, `backup`, `reject` — applying the shot-type rules above. Say
  **why** in `reason` — the reasons ARE the product; the user learns to trust the cull by
  reading them.
- **Short clips: sample densely before judging.** When judging from extracted frames, a
  3-frame sample lies about clips under ~10s. Locked-off insert shots (a hand takes the cup,
  an object exits frame) are SUPPOSED to end on an empty frame — sampling the middle/end
  shows "nothing" and tempts a false reject. For any clip < 10s, extract 6–8 frames across
  the full duration, and read an empty tail as a *completed action*, not a failed shot.
  (Learned the hard way: a perfect match-cut insert nearly got rejected as "camera fell".)
- **Thin evidence = soft verdicts.** `reject` requires positive evidence (a visible flub, an
  abandoned take, a clearly better twin). With no transcript and only filenames/timestamps,
  the worst allowed verdict is `backup`, and the reason must admit the limit — e.g.
  「無逐字稿，只能按時間戳分組 no transcript; grouped by timestamp only」. A confident wrong
  reject is the fastest way to lose the user's trust; visible uncertainty is not a weakness.
- **order** — arrange selects like the video will flow (hook → body → B-roll inserts).
- **in / out** — trim each select to its usable range (skip the clap/setup at the head,
  the reach-for-camera at the tail) when the transcript/timing reveals it.
- **new_name** — short descriptive name; CJK is fine (開場-hook_t2).

Write it as `sift.json`:
```json
{
  "project": "0704_日常vlog",
  "fps": 30, "width": 1080, "height": 1920,
  "clips": [
    {"file": "IMG_4022.MOV", "media": "/Volumes/SD/IMG_4022.MOV",
     "group": "開場 hook", "take": 2, "verdict": "select", "order": 1,
     "reason": "最有能量，一氣呵成", "in": 2.5, "out": 14.0}
  ]
}
```
(`fps/width/height` at the top are only the fallback when no media file is probeable.)

## Step 3 — Run the tool
```
python3 scripts/footagesifter.py sift.json --out out_sift
```
Outputs:
- `sift_report.txt` — the full cull: selects order with trims + reasons, then every group
  with every take judged. Show this to the user for approval **before** the rename step.
- `rename.sh` / `rename.bat` — sort files into `01_精選/` (numbered in selects order),
  `02_備用/`, `03_淘汰/`. **Never overwrites, safe to re-run**, skips already-moved
  files. The user reviews, then runs it inside the clips folder. Rejects are *moved*, never
  deleted — deleting is the user's call, later.
- `還原.sh` / `還原.bat` — **one-command undo** (Mac / Windows): every file back to its exact original name and place.
  New names always keep the original stem (`01_開車-雪山公路_IMG_4558.MOV`), so the camera's
  ID survives for backup cross-referencing and editor relinking. Renaming is therefore fully
  reversible at zero disk cost — if a user asks about *duplicating* files to stay safe, steer
  them here instead: duplicating doubles disk for footage-sized files (a real dump is
  50–200GB) for less safety than the undo script provides. Leave a copy of `還原.sh` (Windows: `還原.bat`) and the
  report in the clips folder itself.
- `selects.fcpxml` + `selects_premiere.xml` + `resolve_selects.py` — timeline files; which
  one to hand the user depends on their editor (see the matrix below).

### Step 4 — Sort the files (in a local agent session, DO it — don't just hand over a script)
Once the user has approved the report, **actually perform the sort** — they asked for
organized footage, not a to-do list. In local sessions the AI agent has folder access, so
run it:
```
cd "/path/to/clips" && bash rename.sh
```
This moves every clip into `01_精選 / 02_備用 / 03_淘汰` (selects numbered in assembly
order). It never overwrites, never deletes, and `還原.sh` undoes it in one command, so doing
the move is safe and reversible. If a delete/move is blocked, request the folder
permission rather than telling the user it can't be done. Only *hand over the script for the
user to run themselves* when the files aren't reachable (footage on a drive the agent can't see)
or the user explicitly wants to run it manually. Either way, confirm the result: show the
count in each folder.

### Step 5 — AFTER the sort: ask about the timeline handoff (once, ever)
Check `.ai-video-workstation/creator/sift-profile.md` and `.ai-video-workstation/creator/editing-setup.md`. If either records the user's editor, skip
straight to that row of the matrix. Otherwise ask ONE question with 一個簡短問題:

> 素材整理好了！你用哪個剪輯軟體？我可以多給你一條「精選時間軸」直接拉進去。
> 選項：**CapCut**（不需要時間軸檔——編號資料夾就是順序）／ **DaVinci Resolve** ／
> **Final Cut Pro** ／ **Premiere Pro** ／ 其他・不確定

Then hand over ONLY that editor's file per the matrix below, and **save the answer to
`.ai-video-workstation/creator/sift-profile.md`** so no future sift ever asks again. Timing matters: ask *after* the
sort is done, not before — the user has already gotten the core value (the sorted folders), so
the question reads as a bonus offer, not a form to fill in. If the answer is CapCut or 不確定, never
mention XML files at all.

### Editor handoff — give each user ONLY their path (never recite this table)
| Editor | Hand them | How | Notes |
|---|---|---|---|
| **CapCut** | the sorted `01_精選/` folder | import the folder; numbering = assembly order | No timeline import exists; the numbered folder IS the product. Don't mention XML files. |
| **DaVinci Resolve** | **untrimmed selects:** `selects.fcpxml` (verified on real DaVinci 2026-07: 12 clips, frame-exact, audio linked). **trimmed selects (any in/out):** `resolve_selects.py` | fcpxml: *File → Import → Timeline*. Script: clips into Media Pool → *Workspace → Console* (Py3) → `exec(open("<path>", encoding="utf-8").read())` | The split exists because DaVinci's fcpxml import can ignore in-points (hard-won lesson) — full-clip timelines are safe, trimmed ones go through the console script, which reads each clip's REAL fps and is exact even in mixed-fps dumps. |
| **Final Cut Pro** | `selects.fcpxml` | *File → Import → XML* | fcpxml is FCP's NATIVE format (verified on real FCP 2026-07). Needs FCP 10.6+; relinks by filename if `media` paths moved. macOS only. |
| **Premiere Pro** | `selects_premiere.xml` | *File → Import* (FCP7-XML/xmeml) | Premiere does NOT read fcpxml. Clips land trimmed, in order, with audio. If media shows offline, right-click → *Link Media* (relinks by filename). |

### The promise vs. the bonus — and the no-dead-end rule
The **guaranteed product is the report + sorted folders**: pure file moves, works for every
editor, every OS, forever. The timeline files are a **bonus accelerator** — present them
that way (「幫你多做了一條時間軸，能用就賺到」), never as the core promise. Confidence
tiers: `resolve_selects.py` proven; `selects.fcpxml` in FCP is native-format (reliable);
`selects_premiere.xml` is spec-correct but less battle-tested.

**If any timeline import misbehaves, do NOT debug the editor.** One sentence — 「沒關係，
直接把 01_精選 資料夾拉進去，編號就是順序」 — and the student is editing again in ten
seconds. A stuck student is the only real failure mode this skill has. If the user's editor
isn't listed (CapCut Web, mobile apps…), the numbered `01_精選/` folder is always the answer.

The review-then-move order is what matters: the user approves the report, *then* the AI agent runs
the sort (Step 4). The scripts still ship so the move is reviewable and reversible (`還原.sh`),
and so a user on a disconnected drive can run it themselves — but in a local agent session, doing the move is
the finish line, not handing over homework.

## Scope discipline — one job, done well
Footage Sifter **organizes and assembles selects; it does not edit.** It doesn't cut
mistakes inside a take, doesn't fix captions (**Caption Doctor**), and never
deletes anything. The rename script is the only thing that touches the user's files, it's
plain text they can read first, and it only ever *moves*.

## The sift profile — `.ai-video-workstation/creator/sift-profile.md` (grows like Caption Doctor's glossary)
A plain-language file in `.ai-video-workstation/creator/` recording what's been learned about this
creator, so nothing is asked twice and every correction sticks:
- **剪輯軟體** — from the Step 5 question.
- **拍攝習慣** — learned from vetoes (e.g. 「定鏡 insert 空景收尾是故意的，永不淘汰」,
  「會跨日拿舊素材當 bookend」).
- **尺度偏好** — ruthless or conservative, if the user has expressed it.
Whenever the user corrects a verdict, append the *generalized* lesson here before
regenerating the report. Load this file at the start of every sift.

## Quality checklist
- [ ] **Watched the frames of every reachable clip** (contact sheets read) before any verdict —
      no verdict from duration/size/timestamp alone.
- [ ] Every clip has a verdict AND a human reason drawn from what's visible — no unexplained
      judgments, no metadata-only reasons.
- [ ] Each clip judged by ITS shot type's rules (mixed dumps are normal, not an error).
- [ ] One select per talking-head group; B-roll keeps coverage; interviews never lose unique content.
- [ ] No `reject` without positive evidence; thin-evidence clips are `backup` with the limit stated.
- [ ] Selects order tells the story; trims skip dead head/tail material.
- [ ] `sift_report.txt` approved by the user before anyone runs the rename script.
- [ ] Rename script reviewed; originals safe (no overwrite, rejects moved not deleted).
- [ ] DaVinci users pointed to `resolve_selects.py` first; timeline length matches the
      report's selects runtime.
- [ ] Windows users: `rename.bat` is best-effort with Chinese filenames — if it garbles,
      the AI agent performs the moves directly instead of debugging cmd.exe encodings.

## Bundled assets
- `scripts/contactsheet.sh` — folder of clips → labelled contact sheets (`_sheets/sheet_N.jpg`)
  the AI agent reads to WATCH the footage before judging (Step 1). The eyes of the sift.
- `scripts/contactsheet_ffmpeg.sh` — same job with ffmpeg only (no ImageMagick); used automatically
  when `montage` is missing. `scripts/media_tools.py` finds the bundled static-ffmpeg when PATH has none.
- `scripts/footagesifter.py` — manifest → report, rename scripts, selects FCPXML, Resolve script.
- `examples/` — a real 7-clip vlog dump: `example_sift.json` → `example_sift_report.txt`.

## Pairs with
- **Caption Doctor → Subtitle Translator** — once the cut is locked, clean and translate captions.
- **HyperFrames** — hand the approved selects to HyperFrames for timeline assembly, styling, audio, and delivery.
