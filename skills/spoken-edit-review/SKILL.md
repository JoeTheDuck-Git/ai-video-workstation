---
name: spoken-edit-review
description: Review talking-head rough cuts for missed retakes, repeated phrases, false starts, clipped words, damaged meaning and reported subtle mouth noises. Use when reviewing a speech edit or when the user reports obvious repeats or mistakes; complements technical video QC.
---

# Spoken Edit Review

Review the audible edit, including the interiors of retained clips. A correct export of a wrong cut list is still an editorial failure. This skill defines a review workflow; it does not install a listening, ASR or forced-alignment service.

## Mandatory pre-cut original-source review

Before executable cuts, run [original-source candidate detection and independent blind review](references/source-review.md). Preserve raw disfluent ASR and timings/confidence, treat >=0.90 textual similarity as a configurable review priority only, and require actual independent source review before the planner emits a bound executable map. Missing listening or unresolved candidates means needs_review. For an explicitly authorized preview, use the evidence-assisted preview path below; post-cut review remains required.

## Preview versus final

Use [the preview-mode contract](references/preview-mode.md) when the user authorizes a review preview with Codex evidence review. Both pre-cut planning and post-cut delivery have explicit `--mode preview` entries. They require a real independent reviewer, intact evidence/version bindings, whole-source/export evidence coverage and a reasoned decision for every candidate. This can authorize a candidate map without pretending Codex listened. Keep `actual_audio_review=false`, `content_status=needs_review`, `final_pass=false`, unresolved findings and before/after change evidence. Technical QC is still required after rendering. Final mode remains the default and requires actual audio review; a preview-bound map cannot be used for final delivery. Respect a request to prepare only: map authorization is not authorization to render.

## Mandatory independent review and delivery gate

For this lab’s talking-head edits, follow [the executable independent-review workflow](references/independent-review.md). Prepare the hashed evidence packet and candidate queue, **actually spawn a different review sub-agent**, preserve its real tool receipts/report, and run `scripts/review_gate.py gate` before final delivery. The reviewer covers retained interiors, joins and ending. No audio-understanding capability means `needs_review`, not an invented listening pass. The editor cannot self-certify; technical success alone never overrides open issues. This workflow does not authorize media changes beyond the user’s scope.

## Scope and evidence

- Respect inspection-only requests. Repair or render only within existing user authorization; ordinary authorized cleanup does not require renewed per-cut approval. Preserve source files and the current deliverable.
- Identify the exact export by path/hash/version, duration and frame rate. Record whether reported times refer to the master or a transcoded preview. Retain approximate reports as ranges, not frame-accurate cut instructions.
- Load the source-to-output map if available. Map all proposed changes back to original media ticks/PTS; never apply output seconds directly to the source or create a competing editorial timeline. Without a map, findings can still target the export, but source cuts remain unresolved.
- Collect original audio, actual exported audio, original ASR and export ASR when available. Reuse installed local tools; this skill does not authorize paid calls, uploads, downloads or environment changes.
- ASR may omit repetitions, disfluencies and failed takes. A clean transcript, high recognition confidence, waveform correlation or successful decode cannot prove clean speech editing. Forced alignment aligns supplied text; it cannot discover words omitted from that text.

## Review the whole speech track

1. Start with user-reported defects. Keep them open until the corrected version is verified or contrary media evidence is documented. Never downgrade them because ASR contains only one sentence.
2. Cover the entire export with overlapping listening/review intervals, including every retained clip's interior, beginning/end and all joins. Choose manageable intervals for the available tool (for example 20–30 seconds with 2–3 seconds of context overlap). Log exact coverage and evidence. Sparse samples are not full coverage.
3. Check for abandoned starts followed by a complete retake; adjacent phrase or meaning repetition; repeated connectors, names or dates; interrupted clauses; clipped phonemes; breath/noise tails carried across cuts; unnatural pauses; and missing negation, qualification or attribution. Deliberate emphasis, stutters intrinsic to the speaker and legitimate recurring terminology are not automatically mistakes.
4. Use ASR anomalies as navigation cues: implausibly long single-word durations, zero-length words, timestamp jumps, low-confidence spans, silence inside apparent uninterrupted text, or disagreement between contextual and short-window transcriptions. Thresholds are language/speaker dependent, not deletion rules. Inspect the audio on both sides of each cue.
5. For a suspected retake, compare both takes with surrounding context in the original and export. Record what was actually heard and by which supported audio-review method. Prefer the complete fluent take that preserves meaning, rather than always keeping the last take. If there is no audio-understanding capability, do not pretend playback or transcription equals listening: report `needs_review` and provide the exact evidence window.

## Subtle mouth-noise reports

For reported swallowing, lip clicks or small noises between phrases, use [mouth-noise candidate review](references/mouth-noise.md). Local waveform/spectral events are navigation candidates, never confirmed swallowing or automatic edits. Preserve quiet speech, aspiration, word tails and natural breaths; absent ASR words do not prove non-speech.

For this user's cleanup, prefer the stronger local attenuation approach approved in the [0034 listening case](references/mouth-noise-0034-stronger-case.md) when evidence supports an isolated event. Aim for a clearly reduced distraction while preserving speech and ambience; do not default to an imperceptibly mild repair or apply the case's numeric settings to every candidate. Follow the bounded preference in the mouth-noise reference.

## Sentence pacing

For this user's talking-head edits, plan AI-created joins between complete sentences with an initial target of **0.12–0.18 seconds** of natural breathing space, before committing source cuts. This is the user's preferred starting range, not a universal fluency threshold or automatic pass criterion. Measure the gap from the preceding sentence's actual audible end to the next sentence's actual onset, not between ASR segment boxes. Preserve final consonants, trailing syllables, natural breath and continuous motion before optimizing the number. Keep the audio and video on the same source map, using rational frame/sample timing; report achieved duration after quantization.

Use unaffected fluent sentences from the same speaker/video as references. Distinguish within-phrase pauses, sentence endings and topic changes; do not force the preferred range onto every pause. Retain natural longer emphasis/topic-change pauses and unflagged fluent delivery. User feedback that a join is rushed overrides a silence detector's lack of a long gap. Silence detection is a low-energy cue, not VAD or proof that no phoneme occurs there. Cut only evidenced quiet interiors. Prefer clean original moving footage and room-tone handles when adding space. Do not manufacture this gap with frozen/duplicated speaking-face frames, abrupt digital silence or overlapping words. Brief room-tone crossfades may smooth noise-floor changes without blending speech.

When clean handles cannot support 0.12–0.18 seconds, choose the closest intact, natural join and record the exception; do not clip speech, slow the whole sentence, add a visible hold, or change meaning to hit the range. If the evidence cannot establish a safe join, mark it needs_review rather than guessing. Log each AI sentence join's source handles, before/after gap, motion/voice evidence and any exception. Review the rendered join with surrounding sentences: meeting the duration alone does not prove natural pacing. Keep known retake defects open during a pacing-only revision.

### Moving picture and continuous room tone

- Remove an unintended freeze introduced solely to lengthen a talking-head pause when repairing that join. Keep the person moving naturally across the available source footage; do not duplicate frames, interpolate a face or slow facial motion just to manufacture breathing space. A deliberately requested creative freeze is a separate exception.
- Prefer clean original sentence-tail or sentence-head motion handles. Check that extending them does not reintroduce the previous failed take, another spoken word or a cut-off syllable. If none exist, prefer a slightly tighter intact cut to freezing the face; document a gap outside the preferred range rather than manufacturing a pause.
- Keep the background noise floor continuous across the join. Preserve appropriate original room tone and natural breath; avoid suddenly replacing it with digital silence. Reused room tone must be verified free of words, obvious breath fragments, clicks or other distracting events, and its level must fit the adjacent footage. If no suitable tone exists, retain the available natural ambience or mark the discontinuity for review instead of claiming it was fixed.
- If the ambience transition is audible, use a brief fade or crossfade confined to verified non-speech handles, with duration adapted to the available clean material. Do not blend consecutive spoken words, create double voice, fade away consonants or alter audio/video synchronization. Do not add a music bed to hide the join unless requested.
- First make the original-speed cut work with complete speech and natural motion. Do not mask a poor cut with a dissolve, morph, zoom or other unrequested transition. Review motion and background continuity together with the surrounding sentences; a low-volume or numerically compliant gap alone is not a pass.

## Findings and coverage

### Source-boundary and final-word gate

Apply this check to new footage too; the DJI timestamps below are regression examples, never reusable cut points. ASR timestamps are navigation estimates, not phoneme boundaries. At every proposed sentence splice, inspect the outgoing tail and incoming head with surrounding original audio, waveform and spectrogram where available. Check whether an incoming clip begins inside the preceding sentence's remaining syllable, even if ASR suppresses that fragment and produces a clean transcript. Distinguish residual speech, legitimate consonant attacks, breath and edit clicks; a transient or low RMS alone is not permission to delete it. Prefer a clean original handle before the intended sentence's true onset, then check complete words, room tone and motion in the rendered join. Never mute or fade a consonant merely to hide an artifact.

Treat the final utterance separately from sentence-to-sentence pacing. Inspect source audio beyond the proposed final out-point; if voiced energy continues or a short contextual transcription of the excluded tail still contains the farewell, mark possible truncation and extend the candidate to include the complete utterance. Do not accept ASR's end time as the actual sound ending. After the full audible tail decays, retain approximately 0.3–0.5 seconds of clean natural motion/ambience for this user's talking-head ending when available; this is a preference, not a universal threshold. Do not apply the 0.12–0.18 sentence-gap target to the end of the film. If clean closing footage is unavailable, report that limitation rather than freeze a face, clip the farewell or restore another take. Fade only after speech ends if needed.

For each repaired boundary, save the old/new source limits, export time, waveform/spectral evidence, contextual transcript uncertainty and listening status. Verify the actual output, including its final seconds and any phone preview. A clean transcript, numerical gap or technical pass does not close a user-reported audible defect; retain `fixed_pending_review` until suitable listening evidence or user confirmation resolves it. This gate reduces risk and must not be represented as a guarantee of error-free edits.

DJI v5 regression examples: the 39.723-second splice began at source 69.81975 while preceding speech remained; the intended next phrase's main onset was around 70.30. The final out-point at source 293.159533 cut audible farewell material continuing until about 294.10. See `productions/dji-0043-pilot/rough-cut-v5-natural/audio-diagnosis/FINDINGS.md` from the project root. These supersede any earlier assumption that ASR-supported endpoints established intact speech.

### Protected phrases and natural motion

Read the project user's [protected-phrase list](../../docs/reference-editing-lab/protected-phrases.json) when present. Check each requested unit against actual source and export, including its intended opening/closing position and surrounding breath/tail. Approximate wording and ASR spelling differences do not nullify protection. Mark a missing protected unit as an editorial blocker even when an earlier cut plan called it redundant. A later user instruction can change the list; do not impose this user's exact catchphrases on other users.

An added audio pause must also preserve acceptable visual motion. For this user's talking-head edits, do not default to freezing a speaking face to create breathing room: the v4 82.148733–82.398983 second hold was reported as a stutter. Prefer clean original motion handles where speech evidence allows, or a smaller gap/alternative edit with its limitation disclosed. Use a visible hold only for a requested creative effect. Existing hold detection and source-map comparison must report such a designed freeze, not silently treat it as valid because it matches the plan.

For each finding record:

```text
id; export hash/version; output interval; source interval(s) or unknown
kind: retake | repetition | false_start | clipped_speech | pause | meaning_loss
expected; observed; evidence paths/method; user_reported: true/false
confidence: media_confirmed | likely | user_reported | unresolved
action: keep | candidate_remove | replace_take | needs_review
status: open | fixed_pending_review | resolved
```

Do not invent exact quoted speech or exact edit boundaries from approximate user timestamps. Store candidate boundaries separately from confirmed frame/sample-aligned decisions.

Report three independent results:

- `technical`: export/decode/spec/map checks from the existing delivery workflow.
- `speech_edit`: `pass`, `fail` or `needs_review`, based on audible evidence and open defects.
- `coverage`: reviewed ranges, method, unreviewed ranges and percentage. Compute the union of intervals, not the sum including overlaps. ASR-only coverage must be labelled separately from listening coverage.

Any unresolved reported mistake or confirmed missed retake prevents a speech-edit pass. Unavailable listening evidence is `needs_review`, not pass. Do not present an artifact as fully reviewed while speech-edit blockers remain; a clearly labelled review draft may still be delivered. Do not require the user to discover all remaining defects one by one.

## If repair is authorized

Feed confirmed changes to the existing owning cut planner and the same source map. Preserve negation, dates/numbers, units and attribution. Regenerate a new version; old reviews do not automatically apply to changed ranges. Review every changed join with context and replay the complete new speech sequence for new rhythm/meaning problems. Then rerun affected technical checks. Never equate a successful alternative renderer with validation of the failed renderer.

Read [the pilot cases](references/pilot-cases.md) when checking this project's DJI 0043 example or testing whether the workflow handles ASR-hidden repeats. They are reported defects, not ground-truth edit boundaries.
