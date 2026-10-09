---
name: canvas-video-pipeline
description: Render a standalone coded motion asset (MP4, ProRes, or transparent MOV) with the canvas-video CLI from a Canvas 2D or Three.js scene, then hand it to HyperFrames and video-delivery-qc. Use when a request names canvas-video, Canvas 2D, or Three.js, or needs a pre-rendered coded overlay or B-roll clip to combine with Dreamina or other footage. Do not use for animation that should live inside a HyperFrames composition; route that to hyperframes.
---

# Canvas Video Pipeline

Use `canvas-video` as an isolated deterministic renderer. Do not merge its dependencies or `node_modules` with HyperFrames.

## Route the work

- Use `footage-sifter` before editing when a raw footage dump needs visual review, take grouping, selects, or editor handoff files.
- Use `beat-cut-editor` after selects are approved when the job needs music-beat cuts, dialogue tightening, long-form highlight extraction, an EDL, or editable subtitle timing. It is an optional local import and is not bundled here.
- Use Dreamina Canvas for requested generative image, video, voice, or music assets. Follow `$dreamina-canvas-cli`, including live capability discovery and credit confirmation.
- Use `canvas-video` for visuals whose value comes from code: Canvas drawing, Three.js, data animation, HUDs, particles, branded titles, or transparent overlays.
- Use HyperFrames for the final timeline, captions, scene assembly, audio mix, transitions, and delivery render. Start with `$hyperframes` and load its domain skills as required.
- Use `caption-doctor` to clean an authored SRT while preserving timing, then `subtitle-translator` for additional languages. These optional Skills may be imported from a locally owned package and are not bundled here.
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

Read [references/composition-contract.md](references/composition-contract.md) before authoring or modifying a scene. Read [references/pipeline.md](references/pipeline.md) when Dreamina or HyperFrames participates in the deliverable.
When the request calls for an animated title card, B-roll graphic, data card, documentary annotation, glass panel, CRT/VHS treatment, neon lettering, terminal UI, comic impact, editorial rule, split-flap board, kinetic typography, shape morph, particle reveal, infinite zoom, parallax collage, timeline path, exploded product view, audio-reactive accent, Bento layout, or match-cut transition, also read [references/broll-effects.md](references/broll-effects.md). Copy `assets/broll-effects.js` into the Canvas project and build from those deterministic helpers; do not copy private third-party templates or creator-owned prompts into the project or repository.

## Review loop

1. Inspect `canvas-video.json` and confirm width, height, FPS, duration, entry file, and intended aspect.
2. Make the smallest deterministic scene change.
3. For a B-roll/title-card request, show the user 2–4 materially different visual-language options unless the project already records a chosen style. Keep one primary style and one focal word or datum per card.
4. Render 2–4 representative stills before a full video.
5. Inspect the stills for safe areas, typography, clipping, contrast, and aspect-specific layout.
6. Render the motion asset. Use alpha output only when HyperFrames will composite it over footage.
7. Add the rendered asset to the HyperFrames project rather than copying Canvas runtime code into the HyperFrames composition.
8. Render the full edit and run video delivery QC.

Commands:

```bash
canvas-video inspect ./motion-asset --json
canvas-video render ./motion-asset --still 0
canvas-video render ./motion-asset --still 2.5
canvas-video render ./motion-asset --output ./motion-asset/out/final.mp4
canvas-video render ./motion-asset --alpha --output ./motion-asset/out/overlay.mov
```

## Invariants

- A scene must expose `window.seek(t)`, `window.ready`, and `window.CANVAS`.
- The same `t` and inputs must produce the same frame. No wall-clock time, unseeded randomness, or state that depends on the previous seek.
- Preview-only `requestAnimationFrame` is allowed only when the `render` query parameter is absent (any value, including `render=0`, means render mode).
- `window.ready` resolves only after every font and image has loaded. Bundle fonts with the project; never rely on a generic family such as `sans-serif`.
- Store aspect-specific layout decisions in the scene. Letterboxing is not a substitute for portrait composition.
- Keep generated inputs, source footage, outputs, snapshots, credentials, and provider payloads out of the Skill and Git history.
- Keep provider identity, prompt, model, source asset, and generation timestamp in the production job record when generated media is used.
- For a commercial deliverable, use only a voice source whose provider and selected model or voice explicitly permit the intended commercial use. Never treat an F5-TTS checkpoint or other pretrained voice model as commercially cleared by default.
