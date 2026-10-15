---
name: reference-edit-analyzer
description: Analyze an edited reference video into evidence-linked shot, pacing, caption and effect annotations. Use for understanding an existing edit, not raw-footage selection or recovering an editable project.
---

Installed package: when `runtime-root.json` is present beside this file, use its `runtime_root` for repository-relative `scripts/lab`, `docs`, and `WORKSTATION_PROMPTS.md` references. The snapshot contains independent copies of the public tools. Store user media, profiles and outputs in the user's writable project, never inside the installed package.


# reference-edit-analyzer

Status: project-local draft; no autonomous analysis/render service is implemented.

Read [the local editing prompt](../../docs/reference-editing-lab/EDITING_PROMPT.md) and [version/conflict notes](../../docs/reference-editing-lab/INTEGRATION.md) before upstream references. For speech, require actual audio/transcript word-timing evidence; mark missing modalities as blockers. Student short-form reference analysis is guidance, not proof. Return stable source segment IDs with context for later review.

Produce an evidence-based breakdown of a user-provided finished edit. Read [the shared contract](../../docs/reference-editing-lab/CONTRACT.md) before authoring output.

Work locally on read-only source media. Reuse `footage-sifter` contact-sheet extraction for initial coverage, but inspect additional frames around suspected cuts and listen to relevant audio intervals. Sparse stills cannot establish exact transitions, speed ramps, music sync, or continuity. Do not run its rename/sort step for reference analysis.

Register actual ffprobe metadata, checksum and source version; use source ticks with the recorded timebase. Each annotation must identify source interval, evidence artifact/frame ticks or audio interval, knowledge state (`observed`, `inferred`, `unknown`), confidence and pending human review. Narrative role is usually an inference, even when a shot boundary is visible. Unknown claims use null confidence.

A flattened MP4 does not expose original layers, plug-in names, keyframes, camera source focal length, or pre-retime source speed. Describe visible behavior; never invent these internals. User-provided editor projects may supply additional evidence, labelled separately. Similar-looking transitions do not prove the same plug-in.

Return a breakdown table, annotation bundle and unresolved questions. If no footage is available, use only explicitly synthetic fixtures, never a fabricated analysis. No external uploads/model calls or paid requests are authorized by this skill. Do not extract reusable style rules here; hand reviewed evidence to `editing-style-profile`.
