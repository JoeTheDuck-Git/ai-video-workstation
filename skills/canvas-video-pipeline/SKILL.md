---
name: canvas-video-pipeline
description: Create deterministic Canvas 2D or Three.js video scenes, native landscape or portrait compositions, transparent overlays, and reusable motion assets, then hand them to HyperFrames for editing and video-delivery-qc for final validation. Use when a request names canvas-video, coded animation, Canvas, Three.js, HUD, charts, particles, custom motion graphics, transparent overlays, or combining Dreamina-generated media with coded visuals.
---

# Canvas Video Pipeline

Use `canvas-video` as an isolated deterministic renderer. Do not merge its dependencies or `node_modules` with HyperFrames.

## Route the work

- Use Dreamina Canvas for requested generative image, video, voice, or music assets. Follow `$dreamina-canvas-cli`, including live capability discovery and credit confirmation.
- Use `canvas-video` for visuals whose value comes from code: Canvas drawing, Three.js, data animation, HUDs, particles, branded titles, or transparent overlays.
- Use HyperFrames for the final timeline, captions, scene assembly, audio mix, transitions, and delivery render. Start with `$hyperframes` and load its domain skills as required.
- Use `$video-delivery-qc` on the final exported file. Measured QC is authoritative; do not assume the mux target guarantees compliance.

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

## Review loop

1. Inspect `canvas-video.json` and confirm width, height, FPS, duration, entry file, and intended aspect.
2. Make the smallest deterministic scene change.
3. Render 2–4 representative stills before a full video.
4. Inspect the stills for safe areas, typography, clipping, contrast, and aspect-specific layout.
5. Render the motion asset. Use alpha output only when HyperFrames will composite it over footage.
6. Add the rendered asset to the HyperFrames project rather than copying Canvas runtime code into the HyperFrames composition.
7. Render the full edit and run video delivery QC.

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
- Preview-only `requestAnimationFrame` is allowed only when `render=1` is absent.
- Store aspect-specific layout decisions in the scene. Letterboxing is not a substitute for portrait composition.
- Keep generated inputs, source footage, outputs, snapshots, credentials, and provider payloads out of the Skill and Git history.
- Keep provider identity, prompt, model, source asset, and generation timestamp in the production job record when generated media is used.
