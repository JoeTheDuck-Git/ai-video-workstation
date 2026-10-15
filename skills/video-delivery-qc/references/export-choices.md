# Ask for export choices before rendering

This is an export-choice workflow, not authorization to start 4K rendering. Apply after the existing duration/transcript-preview questions, before the render job. Retain the established subtitle, source-review and mouth-noise rules.

## Inspect, then ask together

Run ffprobe on the original media, showing the actual video dimensions, pixel/display aspect, rational nominal and average FPS, codec, pixel format/color, video stream average bitrate and every audio track's codec/sample rate/channels/bitrate. Use stream bitrate, not container total bitrate. Missing bitrate is `unknown`, not zero or a guessed 128 kbps. Nominal FPS alone does not establish CFR: inspect packet/frame PTS cadence. Show VFR or uncertain cadence explicitly.

Present a compact source summary followed by the still-unanswered choices in one question panel (or grouped questions when the UI has a count limit):

1. **Resolution and frame rate:** keep original dimensions and FPS, or customize. Retain selectable resolution options `480p (草稿)`, `720p`, `1080p`, `4K`, `原始解析度`. Selecting 480p only chooses resolution; separately offer `原片幀率` or a supported custom rational FPS. Never silently halve 59.94 to 29.97. For VFR, ask whether to use a PTS-capable renderer or explicitly convert to a selected CFR; the current frame-index adapter cannot preserve VFR.
2. **Video codec:** source codec (display its actual name, e.g. HEVC/H.265) or a supported alternative such as H.264. Enumerate installed encoders; unsupported choices need an explicit alternative, not a silent fallback. Explain same codec means a re-encode, not lossless/original-equivalent quality.
3. **Audio bitrate:** source track bitrate (show value), or custom. Unknown source bitrate requires a custom value or a separately supported measurement/copy workflow. List all tracks; retain their selection/order or ask about a deliberate track selection. The current adapter only supports one mono/stereo audio track and AAC re-encoding; disclose source audio codec conversion. Audio bitrate preservation does not imply codec preservation or bit-exact audio.
4. **Video variable bitrate:** offer a resolution-appropriate draft target, `source measured average bitrate`, or custom (including 55 Mbps when explicitly requested). Do not make 55 Mbps a default for every video or 480p. Explain the target is an approximate average; per-second and measured final average will vary. For this adapter, libx264/libx265 single-pass average-target bitrate mode is supported, not guaranteed exact average, two-pass or fixed-per-second 55 Mbps.

Reuse explicit answers already given for this export. Do not re-ask a selected 480p resolution, but ask the remaining FPS/codec/audio/video bitrate choices. A previous task's answers or a preselected UI option are not this task's choices. Do not start the render while required choices are missing. The agent shows the questions; no graphical application controls are implied.

## Save and apply

Save a JSON alongside the task, supplied through `render-spoken-preview.py prepare --export-settings PATH`. Required fields:

```json
{
  "resolution": "original",
  "frame_rate": "source",
  "video_codec": "source",
  "audio_bitrate": "source",
  "video_bitrate": 55000000,
  "rate_control": "vbr"
}
```

This is a schema example for a user who selected those values, not a default. `frame_rate` can be a supported rational string; `video_codec` can be `h264` or `hevc`; bitrate fields can be `source` or positive integer bits/second. Save user wording/answers in the task's authorization record. The prepared job records source probe data, raw choices, resolved encoder/targets, EDL/source hashes and settings-module hash. A settings change invalidates the old prepared job.

Use the original source referenced and hash-bound by the EDL for high-resolution exports. Never upscale a 480p preview as a 4K master. This adapter rejects upscaling, VFR/unknown cadence, multiple moving-video/audio tracks, nonzero start PTS and unsupported HDR/10-bit inputs (an explicit `pixel_conversion: bt709_10_to_8_draft` can convert confirmed 10-bit BT.709 to an 8-bit draft; disclose the loss of bit depth); stop with the specific limitation and ask about a supported alternative. It does not automatically convert or discard those properties. Larger PTS/multitrack/color-management support is separate work.

The shared preview renderer now applies selected FPS, H.264/HEVC encoder, video target and audio bitrate. Old per-film scripts and subtitle-only archived builders are historical workflows: do not assume they support these choices or reuse them for a new master. Audit/adapt the selected rendering path before use; if it cannot honor the choices, stop. Existing render jobs must be prepared again rather than editing bound JSON in place.

## Output verification

Write `export-spec-qa.json` with requested targets and actual ffprobe measurements separately: dimensions, nominal/average FPS, video codec, measured video bitrate, every output audio track codec and measured bitrate. Missing measurements remain unknown. Compare dimensions/FPS/codec/track count to the confirmed job; investigate mismatches before delivery. For VBR do not declare an exact target match or enforce a per-second target; disclose measured average and material difference. This specification report complements full decode, source mapping, audio checks and independent content/subtitle review; it is not a delivery pass.

Attached still thumbnails are inventory metadata, not additional moving-video tracks. The renderer explicitly selects the probed main video/audio stream indices and records excluded attached-picture indices; it never silently discards another moving video or audio track.
