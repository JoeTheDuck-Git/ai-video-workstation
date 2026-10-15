# DJI 0043 pilot: known review gaps

The user reported missed repetition around output 00:28–00:34, 01:45 and 02:42 in rough-cut-v2. These are approximate user reports, not independently confirmed phoneme boundaries. All three remain open. Do not label a new review passed because it repeats the existing clean ASR text.

Evidence root: `productions/dji-0043-pilot/rough-cut-v2/` from the project root. Read `render-bundle.json`, `source-timeline-map.json`, `expected-transcript.json` and `verification.json`; original ASR is in `productions/dji-0043-pilot/evidence/transcript.json`. Use actual media to confirm take content.

- 00:28–00:34 lies inside the first retained clip, not at an authored splice. Source offset is approximately +1.15115 seconds. Original ASR represents the disputed passage as one sentence and gives a single Chinese character roughly 2.78 seconds; export ASR similarly gives it roughly 2.82 seconds. This is a candidate cue, not proof of which words to remove.
- 01:45 maps to source approximately 02:58.040 inside V2-05. Original and edited transcripts differ near the lawsuit phrasing. The user report stays open even though the edited ASR looks fluent.
- 02:42 is near the V2-10/V2-11 join (V2-11 begins about 02:42.045). Inspect both sides and source context; do not assume all three cases share an identical cause merely because they were reported as repeats.

Existing technical QC sampled 24 clip boundary frames and 12 audio windows. It did not listen to every retained sentence. Its pass therefore does not resolve these reports.

Expected review behavior: retain all three reports, flag the timing anomaly, inspect interiors as well as joins, identify missing listening coverage, and withhold a speech-edit pass until verified. Do not treat this case list as a blind independent evaluation.
