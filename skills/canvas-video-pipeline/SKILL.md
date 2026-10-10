---
name: canvas-video-pipeline
description: >-
  Create and render a standalone coded motion video (MP4, ProRes, or transparent MOV) with
  canvas-video from Canvas 2D, Three.js, or a bundled Tacky motion template. Use for 2D or 3D
  animation, data animation, data visualization video, animated infographic, motion graphic,
  coded B-roll or overlay, and requests such as「3D 動畫」「資料動畫」「數據可視化」
  「可視化動畫」「動態資訊圖」or「輸出 MP4」. When the user requests animation, video,
  motion, or MP4, deliver an actual moving video rather than a static image. Do not use for
  animation that should live inside a HyperFrames composition; route that to hyperframes.
---

# Canvas Video Pipeline

Use `canvas-video` as an isolated deterministic renderer. Do not merge its dependencies or `node_modules` with HyperFrames.

## Route the work

- Use `footage-sifter` as the primary workflow before editing whenever raw footage needs visual review, take grouping, selects, or editor handoff files.
- Use the media source the user selects for generated, recorded, or stock assets. Do not require, install, authenticate, or spend credits with a generative provider unless the user explicitly requests that provider.
- Use `canvas-video` for visuals whose value comes from code: Canvas drawing, Three.js, data animation, HUDs, particles, branded titles, or transparent overlays.
- Treat「可視化動畫」「資料／數據動畫」「動態資訊圖」「3D 動畫」「visualization video」「animated infographic」and an explicit MP4 request as coded-motion intent even when the user does not name `canvas-video`.
- A still image is only a review artifact. When the requested deliverable is animation, video, motion, or MP4, do not finish with a generated raster image, poster, storyboard, or static infographic unless the user explicitly changes the deliverable to a still.
- When the user asks for 3D, use a real Three.js scene with spatial geometry, camera, lighting, and time-based motion. A flat AI-generated image with a faux-3D look does not satisfy a 3D-animation request.
- Use the bundled Tacky Templates when the request needs a complete designed title-card system. Read [references/tacky-templates.md](references/tacky-templates.md), show the gallery or 2–4 suitable options, and adapt the selected asset rather than rebuilding its visual system from scratch.
- Use HyperFrames for the final timeline, captions, scene assembly, audio mix, transitions, and delivery render. Start with `$hyperframes` and load its domain skills as required.
- For every subtitle workflow, run `caption-doctor` first to correct the master text and timing. Use `subtitle-translator` as the primary workflow for additional languages only after the master is approved. Then hand the clean SRT tracks to HyperFrames for visual styling and burn-in; HyperFrames must not replace the text-cleaning step.
- Use `$video-delivery-qc` on the final exported file. Measured QC is authoritative; do not assume the mux target guarantees compliance.
- For social delivery, ask the finishing timeline for `-16 LUFS` unless the delivery brief says otherwise, then accept or reject by measured QC rather than by the requested encoder value.

Do not call a generative provider from `seek(t)`. Generate or download media before rendering and treat it as an immutable local input.

## Start

Check the runtime before creating a project:

```bash
canvas-video doctor
```

Create a native-aspect project. Choose the actual delivery aspect; do not make a 16:9 scene and crop it into 9:16.

```bash
canvas-video init ./motion-asset --aspect portrait
canvas-video init ./motion-asset --aspect landscape
```

Read [references/composition-contract.md](references/composition-contract.md) before authoring or modifying a scene. Read [references/pipeline.md](references/pipeline.md) when external media or HyperFrames participates in the deliverable.
When the request calls for an animated title card, B-roll graphic, data card, documentary annotation, glass panel, CRT/VHS treatment, neon lettering, terminal UI, comic impact, editorial rule, split-flap board, kinetic typography, shape morph, particle reveal, infinite zoom, parallax collage, timeline path, exploded product view, audio-reactive accent, Bento layout, or match-cut transition, also read [references/broll-effects.md](references/broll-effects.md). Copy `assets/broll-effects.js` into the Canvas project and build from those deterministic helpers; do not copy private third-party templates or creator-owned prompts into the project or repository.

For Tacky Templates or the 31-effect gallery, read [references/tacky-templates.md](references/tacky-templates.md). These assets are bundled with this Skill; copy only the selected asset into the production project. Keep the Tacky template engine, Canvas runtime, and HyperFrames in separate dependency directories.

## Review loop

1. Inspect `canvas-video.json` and confirm width, height, FPS, duration, entry file, and intended aspect.
2. Make the smallest deterministic scene change.
3. For a B-roll/title-card request, show the user 2–4 materially different visual-language options unless the project already records a chosen style. Keep one primary style and one focal word or datum per card.
4. Render 2–4 representative stills before a full video.
5. Inspect the stills for safe areas, typography, clipping, contrast, and aspect-specific layout.
6. Render the motion asset. Use alpha output only when HyperFrames will composite it over footage.
7. Add the rendered asset to the HyperFrames project rather than copying Canvas runtime code into the HyperFrames composition.
8. For a standalone request, deliver the rendered video file and report its path, duration, dimensions, FPS, and codec. For an integrated request, render the full edit and run video delivery QC.

## Completion gate

- If the user asked for animation, video, motion, or MP4, completion requires a playable video file. Preview PNGs or JPEGs do not count as the final deliverable.
- If the user asked for 3D, inspect representative frames for visible spatial depth and confirm the scene uses Three.js before rendering.
- If rendering is blocked, report the concrete failing command and preserve the project for retry; do not silently substitute a static image.

Commands:

```bash
canvas-video inspect ./motion-asset --json
canvas-video render ./motion-asset --still 0
canvas-video render ./motion-asset --still 2.5
canvas-video render ./motion-asset --output ./motion-asset/out/final.mp4
canvas-video render ./motion-asset --alpha --output ./motion-asset/out/overlay.mov

canvas-video tacky list
canvas-video tacky copy-template vox ./title-card.html
canvas-video tacky render-template ./title-card.html ./title-card.mp4 --dur=8 --ffmpeg=ffmpeg
```

## Invariants

- A Canvas runtime scene must expose `window.seek(t)`, `window.ready`, and `window.CANVAS`. Tacky HTML templates use their isolated virtual-time renderer instead.
- The same `t` and inputs must produce the same frame. No wall-clock time, unseeded randomness, or state that depends on the previous seek.
- Preview-only `requestAnimationFrame` is allowed only when the `render` query parameter is absent (any value, including `render=0`, means render mode).
- `window.ready` resolves only after every font and image has loaded. Bundle fonts with the project; never rely on a generic family such as `sans-serif`.
- Store aspect-specific layout decisions in the scene. Letterboxing is not a substitute for portrait composition.
- Keep generated inputs, source footage, outputs, snapshots, credentials, and provider payloads out of the Skill and Git history.
- Keep provider identity, prompt, model, source asset, and generation timestamp in the production job record when generated media is used.
- For a commercial deliverable, use only a voice source whose provider and selected model or voice explicitly permit the intended commercial use. Never treat an F5-TTS checkpoint or other pretrained voice model as commercially cleared by default.
