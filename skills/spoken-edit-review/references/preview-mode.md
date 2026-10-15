# Evidence-assisted preview contract

This mode applies only to an authorized review preview. It does not install an audio model, authorize external calls or turn ASR into listening. A request to prepare without rendering stops at the candidate map.

## Before rendering

1. Prepare a fresh source packet with `source_review.py prepare CONFIG PACKET`. Complete the real independent blind phase and capture its returned assessment hash before sharing recommendations, as in source-review.md.
2. Give the reviewer the frozen blind assessment, source packet, proposed map, boundary measurements and before/after change list. The reviewer must assess every source candidate and retained content, including protected phrases and the ending. Preserve evidence disagreements rather than choosing a transcription because it supports the cut. Prefer preserving uncertain material; a candidate change needs corroborating local evidence and must preserve a complete take.
3. Reviewer report uses the existing identity/run/packet, blind assessment, evidence records and open_findings fields, plus:
   - `status: needs_review`, `actual_audio_review: false`, `audio_review: []`.
   - `evidence_review_complete: true` only after full source evidence review. `evidence_review` contains `{start,end,method:codex_evidence_review,evidence_id,finding}` rows. Coverage is the union of ranges. Mention ASR gaps/tails explicitly; viewing metadata alone cannot assess their speech.
   - `preview_decisions` keyed by every queue ID, with `{action:keep|candidate_change|already_excluded,reason,evidence_id}`. This acknowledges review, not certainty or automatic deletion.
   - `preview_map_content_sha256`: SHA256 of `json.dumps(map_without_source_review,sort_keys=True).encode()`. The reviewer must compute it from the map actually reviewed.
   - `open_findings`: nonempty list including unavailable actual listening, remaining uncertainties, and changed boundaries pending rendered review.
4. Proposed map: `review_mode:preview`, `actual_audio_review:false`, `content_status:needs_review`, `final_pass:false`, and nonempty `unresolved_findings`. Each source clip has `boundary_status:candidate_evidence_reviewed` and a hashed boundary JSON with exact native source frames, source hash, `method:codex_evidence_review`, `actual_audio_review:false`, actual independent reviewer ID, findings and hashed `inputs`. Evidence can be measured by the editor; the reviewer explicitly attests the exact map and all boundaries. No reordered or duplicated source spans in this initial preview path. Frame bounds, continuity, native FPS and duration still validate.
5. Run `source_review.py authorize PACKET REVIEW DISPATCH RESULT --mode preview`, then `scripts/lab/plan-spoken-cut.py PACKET REVIEW DISPATCH PROPOSED_MAP OUTPUT --mode preview`. Preserve real tool/blind/completion receipts. Both entries default to final when mode is omitted. Never hand-edit the bound map after approval. Renderer integration must call `validate_authorized_plan(path,allow_preview=True)` explicitly for previews; default validation refuses preview maps. Re-render only when authorized and resolution is settled.

## After rendering

Create a fresh export packet with source/export/map/ASR/technical checks and renderer/QC code hashes. The technical report must bind `export_sha256` and `map_sha256` to the exact tested files, alongside `all_technical_checks_pass` and nonempty passing checks. Independently review the whole export evidence, all interiors, joins and ending. Preview report uses the fields above (no blind phase required again for post-cut), with `preview_decisions` keyed by every export issue. Keep `interiors_reviewed` and `joins_and_ending_reviewed` true only when supported by evidence. New defects stay in open_findings; changes require another map/export and review.

Run `scripts/lab/deliver-spoken-cut.py PACKET REVIEW DISPATCH RESULT --mode preview`. Authorization requires intact source-plan binding, current independent review, full evidence coverage and passing technical checks. Receipt includes `preview_allowed`, `delivery_allowed`, `actual_audio_review:false`, `content_status:needs_review`, `final_pass:false`, `unresolved_findings`, separate audio/evidence coverage and the exact artifact hash. Label the deliverable **待審預覽，未完成實際音訊聽辨**. Technical failure or stale/missing review blocks even preview. Upload/publication authorization remains separate.

## Final

Final mode retains full actual audio review, resolved issues, immutable boundary verification, independent review and hash/version binding. A preview-bound map cannot pass final validation even if someone changes the report status. A genuine final review requires new final authorization and post-cut review of the exact artifact. Do not claim preview tests establish subjective listening quality.
