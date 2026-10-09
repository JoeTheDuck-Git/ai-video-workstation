# Composition contract

## Project manifest

Each project contains `canvas-video.json`:

```json
{
  "version": 1,
  "entry": "scene.html",
  "width": 1080,
  "height": 1920,
  "fps": 30,
  "duration": 5,
  "background": "opaque"
}
```

- `entry` stays inside the project directory.
- `width` and `height` describe the native composition, not a post-render crop.
- `background` is `opaque` or `transparent` and documents intent; `--alpha` controls the output codec.
- Keep FPS constant. Common native rates are 24, 25, 30, 50, and 60.

## Page API

The entry page must expose:

```js
window.CANVAS = outputCanvas;
window.seek = async (seconds) => { /* draw the complete frame */ };
window.ready = (async () => {
  await document.fonts.ready;          // or BROLL_FX.prepare({ fonts, images })
  await Promise.all(images.map((img) => img.decode()));
  await window.seek(0);
})();
```

`window.ready` must not resolve until every font and image the scene uses has loaded. Ship
font files with the project and declare them with `@font-face`; generic families such as
`sans-serif` resolve to different faces on different machines.

`seek(t)` must clear and redraw the complete frame. Its result may depend on `t`, immutable inputs, and fixed seeds only.

Avoid in the render path:

- `Date.now()` or `performance.now()`
- `setTimeout()` or interval-driven state
- CSS animations or transitions
- unseeded `Math.random()`
- physics advanced from the previously rendered frame
- network fetches whose contents are not frozen locally

Render mode is on whenever the `render` query parameter is present, whatever its value: detect it with `new URLSearchParams(location.search).has("render")`. A wall-clock preview loop may run only when render mode is off.

## Aspect-native layout

Treat 1920×1080 and 1080×1920 as different compositions sharing design tokens, not as a crop operation.

- Landscape usually uses horizontal eye travel, side-by-side comparisons, and lower-third captions.
- Portrait uses stacked hierarchy, shorter line lengths, larger readable text, and top/bottom UI-safe margins.
- Keep essential text and faces inside platform-safe regions. Confirm actual target-platform UI before delivery when placement is critical.

## Media

Keep media inside the project or reference an approved local asset location made available by the surrounding workflow. The local server supports byte ranges and streams large files rather than reading them entirely into memory.

For transparent overlays, clear the canvas to transparent and render with `--alpha`. For a normal video, draw an opaque background and render MP4.

## Handoff

Canvas output is a versioned media asset. HyperFrames owns placement, timing against other clips, captions, audio, transitions, and final rendering. The final file—not the intermediate Canvas asset—must pass video delivery QC.
