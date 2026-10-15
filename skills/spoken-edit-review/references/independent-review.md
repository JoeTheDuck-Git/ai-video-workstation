# Executable independent review

This lab requires a separate review sub-agent after each talking-head export, before claiming editorial completion. The editing agent owns the map/render; a different agent owns the review. Use the actual `collaboration.spawn_agent` tool, not a role-play prompt in the editing agent. If unavailable, retain `needs_review`, report the missing capability and deliver only an explicitly labelled review draft when authorized. No installation or paid service is implied.

## 1. Prepare a bound packet

Run `python3 skills/spoken-edit-review/scripts/review_gate.py prepare CONFIG.json PACKET.json` from the lab. CONFIG has:

- `editor_id`: actual editing agent ID/task path, not a fictional person.
- `duration`: full exported video duration in seconds (use video stream duration for frame-aligned coverage).
- `files`: absolute paths keyed `source`, `export`, `map`, `asr`, `technical`; optional `cues`, source transcript, waveforms and any other evidence. Technical JSON has `all_technical_checks_pass` plus nonempty `checks` with `passed` booleans. Bind the QC code and any expected-audio provenance in versions/evidence.
- `implementations`: required absolute paths keyed `renderer`, `technical_qc`, `asr`; these code hashes are bound separately.
- `versions`: absolute paths of this Skill, planner, entry prompt, editing contract, renderer, QC implementation, relevant helpers and this reference. The gate always binds its own code, this lab’s Skill/planner/prompts/contract and protected-phrase list too. It probes the actual video duration and rejects mismatching declared/map duration.
- `asr` is a JSON list of output-time windows `{start,end,text,words:[{text,start,end}]}`; source-time ASR must first be mapped by the existing EDL, never mixed with output-time timings.
- Optional `cues` JSON is `[{kind,start,end,details}]` in output seconds. Include measured phrase-interior low-energy intervals, source-boundary residue, final-word truncation, authored holds, known user defects, and contextual ASR differences. Record evidence/provenance in details. Unknown cues are unresolved, not silent passes.

The helper hashes all inputs and versions, computes union ASR coverage, and generates a candidate queue from long/zero-length word timing, overlap-window differences, plus supplied cues. It does NOT run audio analysis or discover all defects. Existing FFmpeg/ASR tools must generate waveform/low-energy/boundary evidence over all retained interiors as well as joins. A long word, repetition or low energy is a navigation cue, never an automatic deletion. Include normal emphasis and breathing controls when tuning heuristics. Never equate an empty queue with content pass.

## 2. Actually dispatch

Call `collaboration.spawn_agent` with `fork_turns="none"` and a focused request: read this Skill/reference, packet, original audio/export/map and evidence; inspect the whole retained track, joins and ending; independently enumerate open issues and methods/coverage; do not modify media or map; write a report to the designated review directory. Give the reviewer raw evidence and user requirements, not an instruction to confirm the author's verdict. Provide tools/cached local model paths where needed. No new paid calls/downloads.

Capture the returned agent ID and raw tool result in `dispatch-tool-receipt.json`. Capture the actual completed agent response in `completion-tool-receipt.json` after waiting for completion. Do not fabricate either receipt or declare review complete while the agent is running. Save `dispatch.json` with `tool: collaboration.spawn_agent`, `agent_id`, `run_id`, `packet_sha256` (exact packet file), `packet_content_sha256` (SHA256 of Python `json.dumps(packet,sort_keys=True).encode()`), and `tool_receipt`/`completion_receipt` file records `{path,sha256}`. The host verifies the tool-returned identity. These are audit records, not cryptographic proof of agent identity.

## 3. Reviewer output

Reviewer writes JSON with:

- `run_id`, `packet_sha256`, `reviewer_id` matching actual dispatch; `status: pass|fail|needs_review`.
- `evidence`: dictionary of named file records `{path,sha256}`.
- `audio_review`: ranges `{start,end,method,evidence_id,finding}`. Only actual `human_listening` or supported `audio_understanding` counts here. ASR, playing audio through speakers, waveform measurements and reading transcripts do not count. Without listening capability, use an empty array and needs_review; still complete feasible source/map/visual/ASR analysis.
- `interiors_reviewed`, `joins_and_ending_reviewed`: scope declarations backed by the range evidence, not substitutes for coverage.
- `issue_resolutions`: keyed by queue ID, each `{disposition,reason,evidence_id}`. Only `intentional_keep` or `false_positive` may clear a candidate for this immutable export. Confirmed defects and uncertain cues stay open. A fix needs a new export/map packet and re-review; no `fixed` override.
- `open_findings`: list of reviewer-discovered defects or uncertainty, including issues missed by the candidate generator. Include output/source ranges and evidence.

All retained interiors, starts, joins, final words and motion must be covered, not just queued candidates. Reviewer cannot certify its own edited export. If reviewer proposes corrections, editor implements only within authorization, then dispatches another review of the changed export. Explicit user approval of a draft is not evidence of full listening and is not a fabricated human review.

## 4. Delivery gate

Run `python3 skills/spoken-edit-review/scripts/review_gate.py gate PACKET.json REVIEW.json DISPATCH.json RESULT.json`. Exit 0 means the supplied independent evidence meets the gate; exit 2 blocks final pass. Changed source/export/map/skills/code/evidence invalidates the run. Missing reviewer, incomplete audio review, unresolved issues or non-pass technical/content status blocks final delivery. A `review_draft_only` result allows only an authorized, clearly labelled draft with unresolved limitations; never advertise it as fully reviewed. Do not bypass the gate with technical QC alone.

The helper validates records; it cannot prove that a caller told the truth about listening. The host must preserve real tool output and reject invented review/approval. Record ASR coverage separately; it is neither necessary nor sufficient proof of audible cleanliness. Preview transcodes with changed frames/audio need bound verification, and substantive edit changes require a fresh independent run.

## Regression acceptance

- Real 0044 v1: merged full-window ASR must still queue its 2.18-second single-character span at output ~71–73; short-window evidence reveals repeated start. It must not get final pass while this is unresolved, even if technical QC passes.
- 0043 v5: source-boundary residual speech, farewell truncated despite ASR word-end, and v4 authored freeze remain blocking candidates. Use existing case evidence, never transplant these timestamps into new clips.
- Normal emphasis/repeated terminology and normal breathing may be intentional. Candidate generation must never issue an edit; only evidenced independent keep/false-positive decisions clear cues. Do not hard-code all repetition as failure.
- needs_review, zero listening coverage, self-review, missing receipt, stale map/export or modified evidence cannot produce final pass. Tests are structural/behavioral checks, not proof of an audio model's accuracy.

## Delivery entry wiring

The talking-head delivery entry is `python3 scripts/lab/deliver-spoken-cut.py PACKET REVIEW DISPATCH OUTPUT`. It defaults to final mode, re-evaluates the gate against current files and returns exit 2 with no authorized artifact for needs_review. Explicit `--mode draft` may authorize only an UNREVIEWED_DRAFT with blockers visible. This command does not render or upload. The existing 0044 pilot exposes the same entry through `productions/dji-0044-pilot/rough-cut-v1/deliver.py`. After render and technical QC, the host prepares evidence, actually spawns/waits for the reviewer, then calls this entry before handing an artifact to Library/upload tools. Render/verify completion is never delivery permission.

There is no backend auto-spawn service. Platform collaboration and Library tools are host-agent capabilities, outside the Python process. The host must honor this receipt; direct manual upload tools cannot be technically intercepted by this local CLI. Do not claim a universal upload sandbox or automatically wired Manim service. Existing Manim demo delivery is a different pipeline.

## Evidence-assisted preview

Use the explicit `--mode preview` source/planner/delivery path in [preview-mode.md](preview-mode.md) for an authorized candidate preview. Post-export review still requires a real independent agent, all retained interiors/joins/ending and every queued candidate, but evidence coverage is separate from audio coverage. Neither legacy draft mode nor a successful render substitutes for this preview review. Final remains the default.
