# Canvas B-roll effect recipes

These are original deterministic Canvas 2D recipes informed by common motion-design
languages. They do not include or reproduce third-party HTML templates.

## Install in a scene

Copy this Skill's bundled `assets/broll-effects.js` beside the scene as
`./motion-asset/broll-effects.js`, then load it before the scene script. The active AI
agent must resolve the current Skill directory instead of assuming a Codex- or
Claude-specific installation path.

```html
<script src="./broll-effects.js"></script>
<script src="./scene.js"></script>
```

All functions draw only from explicit inputs and `time`; never call `Math.random()`.

### Progress and easing

Helpers that take a `progress` argument apply their own easing (`smooth` or `outBack`).
Pass **linear** progress from `fx.progress(time, start, duration)`. Passing
`fx.enter(...)`, which is already eased, eases twice and makes motion feel sluggish.
Use `fx.enter` only when you drive your own transforms or alpha.

For per-frame effects, derive the frame with `fx.frameIndex(time, fps)` rather than
`Math.floor(time * fps)`, which loses frames to floating-point error.

### Fonts and images

Do not rely on `sans-serif` or other generic families: the face differs per machine, and
CJK text renders as tofu where no CJK font is installed. Ship font files in the project,
declare them with `@font-face`, and load them before the first frame:

```js
window.ready = fx.prepare({
  fonts: ["900 96px 'Noto Sans TC'"],
  text: "滿天流星",
  images: [photo],
}).then(() => window.seek(0));
```

`prepare` throws when a named font does not load, so the render fails instead of silently
using a fallback face.

The text helpers `neonText`, `flapText`, and `kineticText` require an explicit
`options.font`. They reject generic families such as `sans-serif`, `serif`, and
`system-ui`; pass the same bundled `@font-face` shorthand that was checked by `prepare`.

### Seed stability

`fx.seeded(seed)` preserves the original random stream for backward-compatible renders.
Existing VHS noise, highlighter, rough-circle, and particle effects therefore keep their
approved pattern when re-rendered with the same inputs. For a new custom effect that
benefits from decorrelating nearby seed numbers, opt in with `fx.seededHashed(seed)`.

## Route by communication goal

| Goal | Recipe | Canvas helpers | Motion rule |
|---|---|---|---|
| Documentary explanation | paper, highlighter, rough annotation | `highlighter`, `roughCircle` | calm type; annotation supplies energy |
| Corporate/data | quiet grid, one accent, thin rules | `minimalBars`, `editorialRule` | slow reveal; one highlighted datum |
| Comic emphasis | flat primaries, heavy outline, burst | `popBurst` | one overshoot impact; do not shake continuously |
| Analog memory | dark CRT, scanlines, stable seeded noise | `scanlines`, `vhsNoise` | short tracking event, then readable hold |
| Soft tech | ivory/pastel background, code panel | `terminalPanel`, `editorialRule` | fade/type softly; no impact motion |
| Digital terminal | fixed dark panel, syntax colors | `terminalPanel`, `minimalBars` | discrete ticks; no floating camera |
| Editorial quote | ivory field, serif type, hairlines | `editorialRule` | mask/rise type; generous whitespace |
| Night-city accent | physical tube lettering | `neonText` | flicker only during ignition; keep dark tube readable |
| Premium UI | refractive translucent panels | `glassCard` | small squash/overshoot, then subtle drift |
| Travel/status board | mechanical character tiles | `flapText` | staggered lock in reading order |
| Kinetic identity | bold type, one accent, beat-safe entrances | `kineticText` | stagger glyphs; settle before the next message |
| Shape-led transition | one silhouette becomes another | `shapeMorph`, `matchCut` | match position and mass before changing detail |
| Particle reveal | dots gather into a supplied target field | `particleReveal` | use a fixed seed; hold the resolved subject |
| Infinite zoom | nested scenes or objects share one optical center | `infiniteZoom` | cross a portal on a deliberate story beat |
| Layered collage | foreground, subject, and background move at different rates | `parallaxImage` | keep motion subtle enough to preserve readability |
| Timeline/map | a path reveals events, stops, or progress | `timelinePath` | reveal in chronological or geographic order |
| Product breakdown | components separate without losing assembly logic | `explodedView` | move on meaningful axes; annotate after separation |
| Audio-reactive accent | precomputed amplitude drives rings or emphasis | `sampleEnvelope`, `audioPulse` | analyze audio before render; never sample live playback in `seek(t)` |
| Bento showcase | modular cards enter and reorganize | `bentoShowcase` | keep one hierarchy and use normalized item coordinates |

## Motion-component API

The advanced helpers are deliberately visual-language neutral. Combine them with one
chosen style rather than treating all of them as a single look.

```js
fx.kineticText(ctx, "MAKE IT CLEAR", 540, 280, fx.progress(time, 0.2, 0.8), {
  font: "900 92px 'Inter'",
  fill: "#f4f1e8",
});

fx.shapeMorph(ctx, triangle, roundedDiamond, fx.progress(time, 1.1, 0.7), {
  fill: "#ff5a36",
});

fx.particleReveal(ctx, logoPoints, fx.progress(time, 2.0, 1.0), {
  seed: 42,
  color: "#69f0d0",
});
```

Images and custom drawings can participate without changing the renderer contract:

```js
fx.parallaxImage(ctx, photo, { x: 80, y: 180, w: 920, h: 620 }, time / 5);

fx.explodedView(ctx, parts, fx.progress(time, 0.5, 1.2));

fx.bentoShowcase(ctx, [
  { x: 0, y: 0, w: 0.62, h: 1, draw: drawHeroCard },
  { x: 0.62, y: 0, w: 0.38, h: 0.5, draw: drawMetric },
  { x: 0.62, y: 0.5, w: 0.38, h: 0.5, draw: drawQuote },
], { x: 70, y: 160, w: 940, h: 1420 }, fx.progress(time, 0.2, 0.9));
```

For audio-reactive motion, compute and save a normalized envelope before rendering:

```js
const level = fx.sampleEnvelope(AUDIO_ENVELOPE, time, DURATION);
// Level sets ring size and brightness; `time` only moves the rings outward.
fx.audioPulse(ctx, 540, 960, 90, level, { color: "#73e0ff", time });
```

`shapeMorph` expects point arrays shaped as `{x, y}`. `particleReveal` expects target
points shaped as `{x, y, radius?, color?, alpha?}`. `bentoShowcase` item coordinates
are normalized to its supplied box, which keeps the same recipe reusable in native
landscape and portrait compositions. `minimalBars` scales to the largest value by
default; pass `max: 1` when values are already ratios. Negative values draw as empty bars.

## Example seek fragment

```js
const fx = window.BROLL_FX;
window.seek = (time) => {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  const p = fx.enter(time, 0.35, 0.7);
  fx.glassCard(ctx, { x: 96, y: 220, w: 888, h: 390 });
  fx.neonText(ctx, "滿天流星", 540, 410, {
    alpha: p,
    color: "#7ddcff",
    font: "900 96px 'Noto Sans TC'",
  });
};
```

## Quality rules

- Pick one primary visual language per card. A secondary language may support it, but
  never combine VHS scanlines, paper ink, glass refraction, and comic bursts at once.
- Give each card one focal word or datum. Split two ideas into two cards.
- Land the complete message by about five seconds and hold it long enough to read.
- For sourced numbers, preserve the value and source in the production record. Never
  invent metrics.
- In portrait, compose natively at 1080×1920 and keep captions and platform UI zones
  clear. Do not crop a 16:9 card into 9:16.
- Render stills at entrance, focal reveal, and hold before rendering the full motion.
- Add SFX in HyperFrames after the animation is approved; do not make `seek(t)` depend
  on live audio playback.
- Use `sampleEnvelope` only with a checked-in job asset or generated scene constant.
  The envelope must be derived before render and must not depend on browser playback.
- For `infiniteZoom`, `parallaxImage`, and image-backed Bento cards, preload every image
  and load every font with `fx.prepare` before resolving `window.ready`.
