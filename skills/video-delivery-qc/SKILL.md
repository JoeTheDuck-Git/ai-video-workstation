---
name: video-delivery-qc
description: Inspect a social video before export or delivery, including technical integrity, social-ready encoding, audio loudness, subtitle-to-speech timing, shot structure, and character/prop/scene continuity. Use for final video QC, social delivery checks, subtitle verification, or diagnosing a rendered video; do not invoke for ordinary video creation that has not reached a review or delivery stage.
---

# Video Delivery QC

Run an evidence-backed quality gate without treating unmeasured properties as passed. Preserve the approved creative intent: inspect first, then fix or render only when the user's request authorizes it.

## Choose the gate

- For a HyperFrames project, run its owning HyperFrames checks first, then inspect the rendered artifact with this skill.
- For an existing video file, start with the deterministic technical scan.
- When the user reports a story, character, prop, scene, or subtitle mismatch, also run semantic continuity review.

## Technical scan

Use the `social` profile by default when the user says 社群影片, 短影音, Reels, Shorts, TikTok, or does not name another delivery destination. Read [references/social-profile.md](references/social-profile.md) for the profile contract and platform-specific overrides.

```bash
python3 scripts/video_qc.py VIDEO \
  --profile social \
  --expected-duration 45 \
  --samples-dir /tmp/video-qc-frames
```

The social profile is a creator-safe master target, not a claim that every platform has one permanent upload specification. It uses MP4/H.264 High Profile/AAC-LC, progressive 4:2:0 SDR, common native frame rates, 48 kHz audio, a common social aspect ratio, and 1080-class output as its preferred technical shape. It sets a production loudness target of `-16 LUFS ±2` and true peak at or below `-1 dBTP`; these audio values are workflow targets because major social platforms do not publish one shared loudness requirement.

The script returns JSON with measured streams, decode status, black/freeze/silence observations, loudness when available, sampled frames, and findings. Explicit user or platform requirements override the profile. A missing measurement is `not_checked` or `null`, never a pass. Treat decode failure, a missing required stream, or a material explicit-spec mismatch as blocking.

## Subtitle and speech alignment

When captions or narration matter:

1. Read the authored caption timeline if available.
2. Transcribe the actual exported audio with the available local transcription workflow. Prefer word- or segment-level timestamps; use WhisperX or faster-whisper when installed.
3. Compare spoken text and caption intervals. Allow normal reading lead/lag, but flag captions that show a different sentence, begin after speech has substantially progressed, end before speech finishes, or represent speech absent from the audio.
4. Spot-check flagged intervals against the media. ASR is evidence, not ground truth; ambiguous recognition is `needs_review`.

Do not retain planned dialogue that is not audible in the final export. Do not rewrite dialogue merely to match an uncertain transcription.

## Semantic continuity

Read [references/semantic-review.md](references/semantic-review.md) whenever the check involves character count or identity, duplicate/morphed subjects, costumes, props, locations, story actions, or shot-to-shot continuity.

For vertical social video, also inspect that captions, faces, products, and calls to action remain inside the current platform's safe-zone overlay. Exact UI exclusion zones change; if no current overlay or platform specification is available, report safe-zone status as `not_checked` instead of guessing pixel bounds.

## Decision and report

Classify findings:

- `blocking`: corrupt or undecodable delivery, missing required audio/video, materially wrong duration/spec, confirmed subtitle/speech mismatch, or confirmed story-continuity failure.
- `warning`: suspicious freeze/silence/black interval, uncertain ASR/vision finding, or non-critical platform mismatch.
- `pass`: measured and within the known requirement.
- `not_checked`: no suitable evidence or tool.

Report exact timecodes and evidence. Separate deterministic measurements from model inferences. If the user asked only to inspect, stop after the report. If they asked to export, do not call the artifact final while blocking findings remain; correct in-scope problems, re-run the affected checks, and verify the final file by full decode plus `ffprobe`.

Never claim that a contact sheet proves audio synchronization or that a technical metric proves narrative correctness. VMAF/SSIM require a valid reference video and do not detect wrong characters or dialogue.
