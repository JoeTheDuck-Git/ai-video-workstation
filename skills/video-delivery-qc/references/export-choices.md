# Ask for export choices before rendering

This is an export-choice workflow, not authorization to start 4K rendering. Collect audio quality intent during pre-edit intake with duration/transcript-preview preferences; resolve detailed export settings before the render job. Retain the established subtitle, source-review and mouth-noise rules.

## Inspect, then ask together

Run ffprobe on the original media, showing the actual video dimensions, pixel/display aspect, rational nominal and average FPS, codec, pixel format/color, video stream average bitrate and every audio track's codec/sample rate/channels/bitrate. Use stream bitrate, not container total bitrate. Missing bitrate is `unknown`, not zero or a guessed 128 kbps. Nominal FPS alone does not establish CFR: inspect packet/frame PTS cadence. Show VFR or uncertain cadence explicitly.

Present a compact source summary followed by the still-unanswered choices in one question panel (or grouped questions when the UI has a count limit):

1. **Resolution and frame rate:** keep original dimensions and FPS, or customize. Retain selectable resolution options `480p (草稿)`, `720p`, `1080p`, `4K`, `原始解析度`. Selecting 480p only chooses resolution; separately offer `原片幀率` or a supported custom rational FPS. Never silently halve 59.94 to 29.97. For VFR, ask whether to use a PTS-capable renderer or explicitly convert to a selected CFR; the current frame-index adapter cannot preserve VFR.
2. **Video codec:** source codec (display its actual name, e.g. HEVC/H.265) or a supported alternative such as H.264. Enumerate installed encoders; unsupported choices need an explicit alternative, not a silent fallback. Explain same codec means a re-encode, not lossless/original-equivalent quality.
3. **Audio bitrate:** source track bitrate (show value), or custom. Unknown source bitrate requires a custom value or a separately supported measurement/copy workflow. List all tracks; retain their selection/order or ask about a deliberate track selection. The current adapter only supports one mono/stereo audio track and AAC re-encoding; disclose source audio codec conversion. Audio bitrate preservation does not imply codec preservation or bit-exact audio.
4. **Video variable bitrate:** offer a resolution-appropriate draft target, `source measured average bitrate`, or custom (including 55 Mbps when explicitly requested). Do not make 55 Mbps a default for every video or 480p. Explain the target is an approximate average; per-second and measured final average will vary. For this adapter, libx264/libx265 single-pass average-target bitrate mode is supported, not guaranteed exact average, two-pass or fixed-per-second 55 Mbps.

Reuse explicit answers already given for this export. Do not re-ask a selected 480p resolution, but ask the remaining FPS/codec/audio/video bitrate choices. A previous task's answers or a preselected UI option are not this task's choices. Do not start the render while required choices are missing. The agent shows the questions; no graphical application controls are implied.

## Audio quality question before editing

Ask “這次音訊希望如何保留？精準剪輯需要處理接點；相同取樣率與聲道不代表音質完全不變。” Offer selectable choices:

- **高品質 AAC（精準剪輯）**: edit from original-source audio and encode once for the deliverable. Show source bitrate and confirm `source` target or a supported custom target (for example 320 kbps for stereo when appropriate, not a universal default). The target is not a guaranteed measured average; same codec, sample rate, channels or bitrate does not mean lossless. If the user requires a minimum measured bitrate, record it separately and verify it instead of treating a target as compliance.
- **另附無損 PCM WAV**: deliver a synchronized WAV master of the edited source-decoded audio alongside the playable video. This avoids an additional lossy codec stage in the WAV; it cannot recover information already lost in the original AAC, nor make repaired/processed samples identical to the original. Confirm intended sample rate, channels and supported PCM precision; keep the same EDL and verify alignment. Explain the larger file and that the video audio remains a separately selected encode unless a verified container/codec alternative is chosen.
- **原音訊不重編碼（剪點受限）**: preserve compressed audio packets only with a verified stream-copy path. Packet boundaries, timestamps and priming may limit precise edits; no sample-level mouth-noise repair, fades or mixing in copied regions. Verify synchronization and packet preservation, and explain any required cut adjustment before committing it. Do not promise arbitrary speech cuts with byte-identical audio.

Allow custom input and reuse explicit choices for this task. “原畫質／其他品質不能變” is not permission to silently choose AAC re-encoding: resolve whether high-quality re-encoding, a PCM master, or packet preservation is intended. Do not transcode an already compressed preview to a higher bitrate as a repair; return to the original source and the approved EDL. Keep original video and all source audio tracks unchanged.

Record the selected `audio_quality_mode` (`aac_high_quality`, `aac_plus_pcm_wav`, or `packet_copy`) and any measured-bitrate requirement in the task request, separately from the renderer settings schema below. The current shared adapter implements AAC re-encoding only: WAV-master and source packet-copy choices require a separately verified adapter or implementation before rendering. Show unsupported choices with that limitation and do not substitute a supported mode without the user's agreement. This Skill update adds the question and decision rules, not new codec/render capabilities. Group intake questions within the tool's question limit without dropping duration, transcript-preview or resolution choices.

## Draft package choice

Use one two-stage question flow alongside existing duration, transcript-preview, video and audio choices:

1. **「這次是否要生成可編輯草稿包（時間軸、片段裁切及素材引用／素材）？目前 exporter 尚未支援，選是會先記錄需求。」** Options: **「否，不生成草稿包」／「是，需要草稿包」**.
2. Only after yes, ask **「草稿包要用在哪個軟體？」** Options: **「剪映」／「CapCut」／「兩者都要」**.

Reuse actual answers; missing answers stay pending, and preselection is not consent. Do not show a second competing Jianying-only question. For each selected product separately confirm desktop platform (`macOS`/`Windows`), full version, and build when known. Never copy one product's version or compatibility result into the other. Confirm material mode (`copy`/`reference`) for the package delivery; copy increases size, references require original paths/media. Do not generate or revise subtitles unless requested and available.

Store a single `draft_package` object in the task request and `--export-settings` JSON:

```json
{
  "requested": true,
  "selection": "both",
  "materials": null,
  "targets": {
    "jianying": {"platform": null, "version": null},
    "capcut": {"platform": null, "version": null, "build": null}
  }
}
```

This is a schema example, not a default answer. `requested` is null/false/true; `selection` is null/`jianying`/`capcut`/`both`. Keep pending answers null. Preserve original answers and later explicit changes. The legacy `jianying_draft` input is accepted as Jianying-only by the same helper; never supply both keys. Prepared jobs use only the canonical `draft_package` state.

The existing `render-spoken-preview.py prepare` calls `draft-package-choice.py`, binds its code hash and records the state. Unanswered is `pending_confirmation`; no is `not_requested`; yes without a target is `pending_target`; selected targets currently remain **unsupported**. Each target independently records `support_status: unsupported`, `validation_status: not_tested`, missing details, `artifact: null`, and `generation_allowed: false`. No exporter is implemented for either product. Structural prototype tests or a readable older draft sample do not prove app compatibility, open/save/reopen, linked audio, or successful generation.

Prepare creates no media/draft directory. Render stops for pending/yes choices before output creation or FFmpeg, rather than silently substituting a movie. If the user separately wants a supported movie, clarify that independent deliverable and preserve unresolved draft requests in the task record. Do not rewrite yes as no. Custom adapters follow the same question/state contract; changed code/settings require a fresh prepared job, never modifications to historical deliveries.

For future verified adapters, share the neutral source-frame timeline but use separate product schemas, version bindings and import tests. Renaming one package never establishes dual compatibility. Both requested targets must be reported separately; partial success is not “both complete.” Resolve output through `output-location.py`, then separate `jianying-draft` and `capcut-draft` children under the configured external job directory. These are proposed paths, not artifacts. Missing external access stops output without an internal-disk fallback. Selecting a target does not authorize new software/dependencies or bypassing permissions.

## Local output location

Before any new media output, read the workstation's optional `.local/output-location.json` via `scripts/lab/output-location.py`. A configured external drive must actually be mounted and its output root writable; stop otherwise, with no fallback to the system disk or synthetic mount directory. Use a fresh film/version subdirectory and preserve original/previous files. Shared render prepare reads this policy and binds it into the job; render revalidates it. Custom task adapters must use the same resolver. This local preference is excluded from the installation manifest and Git; do not copy a person's volume path into public skill defaults.

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

Write `export-spec-qa.json` with requested targets and actual ffprobe measurements separately: dimensions, nominal/average FPS, video codec, measured video bitrate, every output audio track codec and measured bitrate. Missing measurements remain unknown. Compare dimensions/FPS/codec/track count to the confirmed job; investigate mismatches before delivery. For VBR do not declare an exact target match or enforce a per-second target; disclose measured average and material difference. For audio, also compare the requested quality mode, source bitrate, configured target and measured result separately. If an explicit minimum or preservation requirement is missed, revise from original audio or obtain agreement to a concrete alternative before delivery; do not certify it on sample rate/channels alone. Verify any WAV master against its intended PCM settings, EDL and video alignment; verify packet preservation for a copy mode. This specification report complements full decode, source mapping, audio checks and independent content/subtitle review; it is not a delivery pass.

Attached still thumbnails are inventory metadata, not additional moving-video tracks. The renderer explicitly selects the probed main video/audio stream indices and records excluded attached-picture indices; it never silently discards another moving video or audio track.

### 中立時間線小樣本（尚非草稿 exporter）

`scripts/lab/draft-timeline-prototype.py` 僅供結構驗證：`neutral_sample(map_path, expected_sha256, indices)` 以已確認 EDL 的 SHA-256 綁定 2–3 個按順序選取的片段，保留來源幀界線、分數 FPS、嵌入音訊連結及原時間線位置。`capcut_proposal()` 與 `jianying_proposal()` 分別產生提案，版本／平台須由呼叫端提供。來源路徑保持不變，Windows 路徑不可在 Mac 上重新解析。

這個工具沒有原生草稿 writer，不複製媒體、不啟動編輯器、不重新編碼。兩種提案的 artifact 都是 null，相容性都是 unverified；不得把提案 JSON 當成已交付的草稿包。仍需各產品目標版本的原生範例、獨立 adapter，以及真實開啟、儲存、重新開啟測試。
