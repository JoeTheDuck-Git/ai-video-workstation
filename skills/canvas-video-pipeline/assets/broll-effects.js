/* Deterministic Canvas 2D motion helpers for canvas-video scenes. */
(function (global) {
  "use strict";

  const TAU = Math.PI * 2;
  const clamp = (v, lo = 0, hi = 1) => Math.max(lo, Math.min(hi, v));
  const mix = (a, b, t) => a + (b - a) * t;
  const smooth = (t) => { t = clamp(t); return t * t * (3 - 2 * t); };
  const outBack = (t) => {
    t = clamp(t) - 1;
    return 1 + 2.70158 * t * t * t + 1.70158 * t * t;
  };
  // Eased 0..1 progress, for driving your own transforms.
  const enter = (time, start, duration = 0.5) => smooth((time - start) / duration);
  // Linear 0..1 progress. Helpers that take `progress` apply their own easing, so pass this.
  const progress = (time, start, duration = 0.5) => clamp((time - start) / Math.max(1e-6, duration));
  // Integer frame index that tolerates float error in `frame / fps * fps`.
  const frameIndex = (time, fps = 30) => Math.floor(time * fps + 1e-6);
  // Optional seed scrambling for new effects. `seeded(seed)` intentionally keeps the
  // original stream so an approved render remains pixel-compatible after upgrades.
  const hashSeed = (seed) => {
    let h = (seed | 0) ^ 0x9e3779b9;
    h = Math.imul(h ^ (h >>> 16), 0x85ebca6b);
    h = Math.imul(h ^ (h >>> 13), 0xc2b2ae35);
    h ^= h >>> 16;
    return h || 1;
  };
  const seeded = (seed) => {
    let x = (seed | 0) || 1;
    return () => {
      x ^= x << 13; x ^= x >>> 17; x ^= x << 5;
      return (x >>> 0) / 4294967296;
    };
  };
  const seededHashed = (seed) => seeded(hashSeed(seed));

  const GENERIC_FONT_RE = /(?:^|[,\s])(?:sans-serif|serif|monospace|system-ui|ui-serif|ui-sans-serif|ui-monospace|cursive|fantasy)(?=$|[,\s])/i;
  function requiredFont(font, helper = "text helper") {
    if (typeof font !== "string" || !font.trim()) {
      throw new Error(`${helper} requires options.font using a bundled @font-face family`);
    }
    if (GENERIC_FONT_RE.test(font)) {
      throw new Error(`${helper} rejects generic font families; use a bundled @font-face family`);
    }
    return font;
  }

  // Load fonts and decode images before the first frame. Each font must match an @font-face
  // the page declares; otherwise this throws so the render fails instead of using a fallback face.
  async function prepare({ fonts = [], images = [], text = "" } = {}) {
    const doc = global.document;
    if (doc?.fonts) {
      const specs = fonts.map((font) => requiredFont(font, "prepare"));
      const loaded = await Promise.all(specs.map((font) => doc.fonts.load(font, text || undefined)));
      await doc.fonts.ready;
      const missing = specs.filter((font, i) => !loaded[i].length);
      if (missing.length) throw new Error(`Fonts not loaded (declare them with @font-face): ${missing.join(", ")}`);
    }
    await Promise.all(images.map((image) => (image?.decode ? image.decode() : Promise.resolve())));
  }

  function roundRect(ctx, x, y, w, h, r) {
    w = Math.max(0, w);
    h = Math.max(0, h);
    const rr = Math.max(0, Math.min(r, w / 2, h / 2));
    ctx.beginPath();
    ctx.moveTo(x + rr, y);
    ctx.arcTo(x + w, y, x + w, y + h, rr);
    ctx.arcTo(x + w, y + h, x, y + h, rr);
    ctx.arcTo(x, y + h, x, y, rr);
    ctx.arcTo(x, y, x + w, y, rr);
    ctx.closePath();
  }

  function glassCard(ctx, box, options = {}) {
    const { x, y, w, h } = box;
    const radius = options.radius ?? Math.min(w, h) * 0.1;
    ctx.save();
    roundRect(ctx, x, y, w, h, radius);
    const fill = ctx.createLinearGradient(x, y, x + w, y + h);
    fill.addColorStop(0, options.light ?? "rgba(255,255,255,.30)");
    fill.addColorStop(0.55, options.mid ?? "rgba(255,255,255,.12)");
    fill.addColorStop(1, options.dark ?? "rgba(120,150,255,.10)");
    ctx.fillStyle = fill;
    ctx.fill();
    ctx.lineWidth = options.lineWidth ?? 2;
    ctx.strokeStyle = options.stroke ?? "rgba(255,255,255,.62)";
    ctx.stroke();
    ctx.globalCompositeOperation = "screen";
    const shine = ctx.createLinearGradient(x, y, x + w, y);
    shine.addColorStop(0, "rgba(255,255,255,0)");
    shine.addColorStop(0.45, "rgba(255,255,255,.18)");
    shine.addColorStop(0.7, "rgba(255,255,255,0)");
    roundRect(ctx, x + 3, y + 3, w - 6, h * 0.35, radius * 0.8);
    ctx.fillStyle = shine;
    ctx.fill();
    ctx.restore();
  }

  function scanlines(ctx, width, height, options = {}) {
    const step = options.step ?? 4;
    ctx.save();
    ctx.globalAlpha = options.alpha ?? 0.12;
    ctx.fillStyle = options.color ?? "#001018";
    for (let y = 0; y < height; y += step) ctx.fillRect(0, y, width, 1);
    ctx.restore();
  }

  function vhsNoise(ctx, width, height, time, options = {}) {
    const frame = options.frame ?? frameIndex(time, options.fps ?? 30);
    const rng = seeded(frame + (options.seed ?? 404));
    ctx.save();
    ctx.globalAlpha = options.alpha ?? 0.12;
    const count = options.count ?? 90;
    for (let i = 0; i < count; i++) {
      const white = rng() > 0.48;
      ctx.fillStyle = white ? "#d9f6ec" : "#061014";
      ctx.fillRect(rng() * width, rng() * height, 1 + rng() * 12, 1 + rng() * 3);
    }
    ctx.restore();
  }

  function neonText(ctx, text, x, y, options = {}) {
    const color = options.color ?? "#40d9ff";
    const font = requiredFont(options.font, "neonText");
    const align = options.align ?? "center";
    const alpha = options.alpha ?? 1;
    ctx.save();
    ctx.font = font;
    ctx.textAlign = align;
    ctx.textBaseline = options.baseline ?? "middle";
    ctx.globalAlpha = alpha;
    ctx.lineJoin = "round";
    ctx.strokeStyle = color;
    ctx.lineWidth = options.tubeWidth ?? 5;
    ctx.shadowColor = color;
    ctx.shadowBlur = options.glow ?? 34;
    ctx.strokeText(text, x, y);
    ctx.shadowBlur = (options.glow ?? 34) * 0.35;
    ctx.fillStyle = options.core ?? "#f7fdff";
    ctx.fillText(text, x, y);
    ctx.restore();
  }

  function highlighter(ctx, x, y, w, h, progress, options = {}) {
    const p = smooth(progress);
    const rng = seeded(options.seed ?? 77);
    ctx.save();
    ctx.globalAlpha = options.alpha ?? 0.72;
    ctx.strokeStyle = options.color ?? "#f5c842";
    ctx.lineWidth = h;
    ctx.lineCap = "round";
    ctx.beginPath();
    const points = options.points ?? 8;
    for (let i = 0; i <= points; i++) {
      const q = Math.min(i / points, p);
      const px = x + w * q;
      const py = y + (rng() - 0.5) * h * 0.16;
      if (i === 0) ctx.moveTo(px, py); else ctx.lineTo(px, py);
      if (i / points >= p) break;
    }
    ctx.stroke();
    ctx.restore();
  }

  function roughCircle(ctx, x, y, rx, ry, progress, options = {}) {
    const p = clamp(progress);
    const rng = seeded(options.seed ?? 19);
    ctx.save();
    ctx.strokeStyle = options.color ?? "#c94f34";
    ctx.lineWidth = options.lineWidth ?? 7;
    ctx.lineCap = "round";
    ctx.beginPath();
    const steps = options.steps ?? 64;
    const end = steps * p;
    let prev = null;
    for (let i = 0; i <= Math.ceil(end); i++) {
      const a = -Math.PI / 2 + TAU * i / steps;
      const jitter = 1 + (rng() - 0.5) * 0.035;
      let px = x + Math.cos(a) * rx * jitter;
      let py = y + Math.sin(a) * ry * jitter;
      // Interpolate the last segment so the stroke grows smoothly instead of in 1/steps jumps.
      if (i > end && prev) {
        const f = end - (i - 1);
        px = mix(prev.x, px, f);
        py = mix(prev.y, py, f);
      }
      if (i === 0) ctx.moveTo(px, py); else ctx.lineTo(px, py);
      prev = { x: px, y: py };
    }
    ctx.stroke();
    ctx.restore();
  }

  function popBurst(ctx, x, y, radius, progress, options = {}) {
    const p = outBack(progress);
    const spikes = options.spikes ?? 18;
    ctx.save();
    ctx.translate(x, y);
    ctx.scale(p, p);
    ctx.rotate(options.rotation ?? -0.08);
    ctx.beginPath();
    for (let i = 0; i < spikes * 2; i++) {
      const a = -Math.PI / 2 + i * Math.PI / spikes;
      const r = i % 2 === 0 ? radius : radius * 0.56;
      const px = Math.cos(a) * r;
      const py = Math.sin(a) * r;
      if (i === 0) ctx.moveTo(px, py); else ctx.lineTo(px, py);
    }
    ctx.closePath();
    ctx.fillStyle = options.fill ?? "#ffd400";
    ctx.fill();
    ctx.lineWidth = options.lineWidth ?? 10;
    ctx.strokeStyle = options.stroke ?? "#17120e";
    ctx.stroke();
    ctx.restore();
  }

  function terminalPanel(ctx, box, options = {}) {
    const { x, y, w, h } = box;
    ctx.save();
    roundRect(ctx, x, y, w, h, options.radius ?? 18);
    ctx.fillStyle = options.fill ?? "#10151d";
    ctx.fill();
    ctx.lineWidth = 2;
    ctx.strokeStyle = options.stroke ?? "#2b3340";
    ctx.stroke();
    const colors = options.lights ?? ["#ff7b72", "#ffa657", "#7ee787"];
    colors.forEach((color, i) => {
      ctx.beginPath(); ctx.arc(x + 28 + i * 24, y + 26, 7, 0, TAU);
      ctx.fillStyle = color; ctx.fill();
    });
    ctx.fillStyle = options.bar ?? "#0c1016";
    ctx.fillRect(x, y + h - 34, w, 34);
    ctx.restore();
  }

  function editorialRule(ctx, x, y, width, progress, options = {}) {
    ctx.save();
    ctx.strokeStyle = options.color ?? "#5f6a3a";
    ctx.lineWidth = options.lineWidth ?? 2;
    ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(x + width * smooth(progress), y); ctx.stroke();
    ctx.restore();
  }

  function minimalBars(ctx, bars, box, progress, options = {}) {
    if (!bars?.length) return;
    const values = bars.map((b) => Math.max(0, Number(b.value) || 0));
    // Scale to the largest bar unless the caller fixes the full-scale value (e.g. max: 1 for ratios).
    const max = options.max ?? Math.max(...values);
    const gap = options.gap ?? 18;
    const rowH = (box.h - gap * (bars.length - 1)) / bars.length;
    ctx.save();
    bars.forEach((bar, i) => {
      const p = smooth((progress - i * 0.08) / 0.65);
      const y = box.y + i * (rowH + gap);
      ctx.fillStyle = options.track ?? "rgba(127,133,142,.18)";
      roundRect(ctx, box.x, y, box.w, rowH, rowH / 2); ctx.fill();
      ctx.fillStyle = bar.highlight ? (options.accent ?? "#2456e6") : (options.fill ?? "#8a8f98");
      const ratio = max > 0 ? clamp(values[i] / max) : 0;
      roundRect(ctx, box.x, y, box.w * ratio * p, rowH, rowH / 2); ctx.fill();
    });
    ctx.restore();
  }

  function flapText(ctx, text, x, y, options = {}) {
    const size = options.size ?? 66;
    const gap = options.gap ?? 8;
    const tileW = options.tileWidth ?? size * 0.82;
    const tileH = options.tileHeight ?? size * 1.18;
    const progress = clamp(options.progress ?? 1);
    const chars = graphemes(String(text));
    const total = chars.length * tileW + Math.max(0, chars.length - 1) * gap;
    const left = options.align === "left" ? x : x - total / 2;
    ctx.save();
    const baseAlpha = ctx.globalAlpha;
    ctx.font = requiredFont(options.font, "flapText");
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    chars.forEach((char, i) => {
      const p = smooth((progress - i * 0.055) / 0.45);
      const tx = left + i * (tileW + gap);
      roundRect(ctx, tx, y - tileH / 2, tileW, tileH, 7);
      ctx.fillStyle = options.tile ?? "#20242b"; ctx.fill();
      ctx.strokeStyle = options.edge ?? "#343a44"; ctx.lineWidth = 2; ctx.stroke();
      ctx.fillStyle = options.ink ?? "#f2f0e6";
      ctx.globalAlpha = baseAlpha * p;
      ctx.fillText(char, tx + tileW / 2, y + mix(16, 0, p));
      ctx.globalAlpha = baseAlpha * 0.48;
      ctx.fillRect(tx + 4, y, tileW - 8, 1);
      ctx.globalAlpha = baseAlpha;
    });
    ctx.restore();
  }

  // Split into user-perceived characters so emoji and combining marks stay intact.
  function graphemes(text) {
    if (typeof Intl !== "undefined" && Intl.Segmenter) {
      return Array.from(new Intl.Segmenter(undefined, { granularity: "grapheme" }).segment(text), (s) => s.segment);
    }
    return Array.from(text);
  }

  function kineticText(ctx, text, x, y, progress, options = {}) {
    const chars = graphemes(String(text));
    const font = requiredFont(options.font, "kineticText");
    const stagger = options.stagger ?? 0.55;
    const rise = options.rise ?? 42;
    ctx.save();
    ctx.font = font;
    ctx.textBaseline = options.baseline ?? "middle";
    const widths = chars.map((char) => ctx.measureText(char).width);
    const total = widths.reduce((sum, width) => sum + width, 0);
    let cursor = options.align === "left" ? x : options.align === "right" ? x - total : x - total / 2;
    chars.forEach((char, i) => {
      const delay = chars.length > 1 ? (i / (chars.length - 1)) * stagger : 0;
      const p = outBack((progress - delay) / Math.max(0.001, 1 - stagger));
      const alpha = smooth((progress - delay) / Math.max(0.001, 0.45 * (1 - stagger)));
      const width = widths[i];
      ctx.save();
      ctx.translate(cursor + width / 2, y + (1 - clamp(p)) * rise);
      ctx.scale(mix(options.startScale ?? 0.82, 1, p), mix(options.startScaleY ?? 1.18, 1, p));
      ctx.globalAlpha = alpha * (options.alpha ?? 1);
      ctx.textAlign = "center";
      if (options.stroke) {
        ctx.strokeStyle = options.stroke;
        ctx.lineWidth = options.lineWidth ?? 3;
        ctx.strokeText(char, 0, 0);
      }
      ctx.fillStyle = options.fill ?? "#f7f4eb";
      ctx.fillText(char, 0, 0);
      ctx.restore();
      cursor += width;
    });
    ctx.restore();
  }

  function pointOnLoop(points, position) {
    if (!points.length) return { x: 0, y: 0 };
    if (points.length === 1) return points[0];
    const wrapped = ((position % 1) + 1) % 1;
    const scaled = wrapped * points.length;
    const index = Math.floor(scaled) % points.length;
    const next = (index + 1) % points.length;
    const p = scaled - Math.floor(scaled);
    return { x: mix(points[index].x, points[next].x, p), y: mix(points[index].y, points[next].y, p) };
  }

  function shapeMorph(ctx, fromPoints, toPoints, progress, options = {}) {
    if (!fromPoints?.length || !toPoints?.length) return;
    const count = Math.max(options.points ?? 0, fromPoints.length, toPoints.length, 3);
    const p = smooth(progress);
    ctx.save();
    ctx.beginPath();
    for (let i = 0; i < count; i++) {
      const a = pointOnLoop(fromPoints, i / count);
      const b = pointOnLoop(toPoints, i / count);
      const x = mix(a.x, b.x, p);
      const y = mix(a.y, b.y, p);
      if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
    }
    if (options.closed !== false) ctx.closePath();
    if (options.fill !== false) {
      ctx.fillStyle = options.fill ?? "#f04d2f";
      ctx.fill();
    }
    if (options.stroke) {
      ctx.strokeStyle = options.stroke;
      ctx.lineWidth = options.lineWidth ?? 3;
      ctx.stroke();
    }
    ctx.restore();
  }

  function particleReveal(ctx, targets, progress, options = {}) {
    const p = clamp(progress);
    const rng = seeded(options.seed ?? 618);
    const spread = options.spread ?? 260;
    const stagger = options.stagger ?? 0.35;
    const count = targets?.length ?? 0;
    if (!count) return;
    ctx.save();
    for (let i = 0; i < count; i++) {
      // Draw the random values before skipping holes so one missing target does not shift the rest.
      const angle = rng() * TAU;
      const distance = spread * (0.35 + rng() * 0.65);
      const target = targets[i];
      if (!target) continue;
      const delay = count > 1 ? (i / (count - 1)) * stagger : 0;
      const local = smooth((p - delay) / Math.max(0.001, 1 - stagger));
      const sx = target.x + Math.cos(angle) * distance;
      const sy = target.y + Math.sin(angle) * distance;
      const x = mix(sx, target.x, local);
      const y = mix(sy, target.y, local);
      const radius = (target.radius ?? options.radius ?? 3) * mix(0.35, 1, local);
      ctx.globalAlpha = clamp(local * 1.5) * (target.alpha ?? options.alpha ?? 1);
      ctx.fillStyle = target.color ?? options.color ?? "#69f0d0";
      ctx.beginPath();
      ctx.arc(x, y, radius, 0, TAU);
      ctx.fill();
    }
    ctx.restore();
  }

  function drawCover(ctx, image, box, scale = 1, offsetX = 0, offsetY = 0) {
    if (!image?.width || !image?.height) return;
    const ratio = Math.max(box.w / image.width, box.h / image.height) * scale;
    const w = image.width * ratio;
    const h = image.height * ratio;
    ctx.drawImage(image, box.x + (box.w - w) / 2 + offsetX, box.y + (box.h - h) / 2 + offsetY, w, h);
  }

  function parallaxImage(ctx, image, box, progress, options = {}) {
    const p = smooth(progress);
    const dx = mix(options.fromX ?? -24, options.toX ?? 24, p);
    const dy = mix(options.fromY ?? 12, options.toY ?? -12, p);
    const scale = mix(options.fromScale ?? 1.08, options.toScale ?? 1.16, p);
    ctx.save();
    roundRect(ctx, box.x, box.y, box.w, box.h, options.radius ?? 0);
    ctx.clip();
    ctx.globalAlpha = options.alpha ?? 1;
    drawCover(ctx, image, box, scale, dx, dy);
    ctx.restore();
  }

  function timelinePath(ctx, points, progress, options = {}) {
    if (!points?.length) return;
    const segments = [];
    let total = 0;
    for (let i = 1; i < points.length; i++) {
      const length = Math.hypot(points[i].x - points[i - 1].x, points[i].y - points[i - 1].y);
      segments.push(length);
      total += length;
    }
    let remaining = total * clamp(progress);
    ctx.save();
    ctx.strokeStyle = options.color ?? "#2f67ff";
    ctx.lineWidth = options.lineWidth ?? 6;
    ctx.lineCap = options.lineCap ?? "round";
    ctx.lineJoin = "round";
    ctx.beginPath();
    ctx.moveTo(points[0].x, points[0].y);
    for (let i = 1; i < points.length && remaining > 0; i++) {
      const length = segments[i - 1];
      const q = length ? clamp(remaining / length) : 1;
      ctx.lineTo(mix(points[i - 1].x, points[i].x, q), mix(points[i - 1].y, points[i].y, q));
      remaining -= length;
    }
    ctx.stroke();
    let travelled = 0;
    points.forEach((point, i) => {
      if (i > 0) travelled += segments[i - 1];
      const visible = total === 0 ? progress > 0 : progress >= travelled / total;
      if (!visible) return;
      ctx.fillStyle = point.color ?? options.nodeFill ?? "#f7f4eb";
      ctx.strokeStyle = point.stroke ?? options.nodeStroke ?? options.color ?? "#2f67ff";
      ctx.lineWidth = options.nodeLineWidth ?? 4;
      ctx.beginPath();
      ctx.arc(point.x, point.y, point.radius ?? options.nodeRadius ?? 9, 0, TAU);
      ctx.fill();
      ctx.stroke();
    });
    ctx.restore();
  }

  function explodedView(ctx, parts, progress, options = {}) {
    const p = clamp(progress);
    const list = parts ?? [];
    // Spread the stagger across the whole part list so every part finishes by progress = 1.
    const totalStagger = clamp(options.totalStagger ?? (options.stagger ?? 0.035) * (list.length - 1), 0, 0.8);
    list.forEach((part, index) => {
      const delay = clamp(part.delay ?? (list.length > 1 ? (index / (list.length - 1)) * totalStagger : 0), 0, 0.95);
      const local = smooth((p - delay) / (1 - delay));
      const x = part.x + (part.dx ?? 0) * local;
      const y = part.y + (part.dy ?? 0) * local;
      const rotation = (part.rotation ?? 0) * local;
      ctx.save();
      ctx.globalAlpha = mix(part.fromAlpha ?? 1, part.alpha ?? 1, local);
      ctx.translate(x + part.w / 2, y + part.h / 2);
      ctx.rotate(rotation);
      if (typeof part.draw === "function") {
        part.draw(ctx, { x: -part.w / 2, y: -part.h / 2, w: part.w, h: part.h, progress: local });
      } else if (part.image) {
        ctx.drawImage(part.image, -part.w / 2, -part.h / 2, part.w, part.h);
      } else {
        roundRect(ctx, -part.w / 2, -part.h / 2, part.w, part.h, part.radius ?? 8);
        ctx.fillStyle = part.fill ?? options.fill ?? "#d9e2ef";
        ctx.fill();
        if (part.stroke ?? options.stroke) {
          ctx.strokeStyle = part.stroke ?? options.stroke;
          ctx.lineWidth = part.lineWidth ?? options.lineWidth ?? 2;
          ctx.stroke();
        }
      }
      ctx.restore();
    });
  }

  function sampleEnvelope(samples, time, duration) {
    if (!samples?.length || duration <= 0) return 0;
    if (samples.length === 1) return clamp(Number(samples[0]) || 0);
    const position = clamp(time / duration) * (samples.length - 1);
    const index = Math.floor(position);
    const next = Math.min(samples.length - 1, index + 1);
    return clamp(mix(Number(samples[index]) || 0, Number(samples[next]) || 0, position - index));
  }

  // Louder level = larger, brighter rings. Pass options.time to make the rings travel outward;
  // ring position then follows time, never the level, so peaks cannot make rings jump.
  function audioPulse(ctx, x, y, radius, level, options = {}) {
    const value = clamp(level);
    const rings = options.rings ?? 3;
    const spread = options.spread ?? 1.4;
    const energy = 0.35 + 0.65 * value;
    ctx.save();
    ctx.strokeStyle = options.color ?? "#73e0ff";
    ctx.lineWidth = options.lineWidth ?? 4;
    for (let i = 0; i < rings; i++) {
      const phase = options.time === undefined
        ? (i + 1) / rings
        : ((i / rings + options.time * (options.speed ?? 0.8)) % 1 + 1) % 1;
      ctx.globalAlpha = (1 - phase * 0.85) * energy * (options.alpha ?? 0.8);
      ctx.beginPath();
      ctx.arc(x, y, radius * (1 + phase * spread * energy), 0, TAU);
      ctx.stroke();
    }
    ctx.restore();
  }

  function bentoShowcase(ctx, items, box, progress, options = {}) {
    const count = Math.max(1, items?.length ?? 0);
    const gap = options.gap ?? 18;
    (items ?? []).forEach((item, index) => {
      const delay = count > 1 ? (index / (count - 1)) * (options.stagger ?? 0.3) : 0;
      const p = outBack((progress - delay) / Math.max(0.001, 1 - (options.stagger ?? 0.3)));
      const card = {
        x: box.x + item.x * box.w + gap / 2,
        y: box.y + item.y * box.h + gap / 2,
        w: item.w * box.w - gap,
        h: item.h * box.h - gap,
      };
      ctx.save();
      ctx.globalAlpha = clamp(p) * (item.alpha ?? 1);
      ctx.translate(card.x + card.w / 2, card.y + card.h / 2);
      ctx.scale(p, p);
      if (typeof item.draw === "function") {
        item.draw(ctx, { x: -card.w / 2, y: -card.h / 2, w: card.w, h: card.h, progress: clamp(p) });
      } else {
        roundRect(ctx, -card.w / 2, -card.h / 2, card.w, card.h, item.radius ?? options.radius ?? 24);
        ctx.fillStyle = item.fill ?? options.fill ?? "#171b22";
        ctx.fill();
        if (item.image) {
          ctx.save();
          roundRect(ctx, -card.w / 2, -card.h / 2, card.w, card.h, item.radius ?? options.radius ?? 24);
          ctx.clip();
          drawCover(ctx, item.image, { x: -card.w / 2, y: -card.h / 2, w: card.w, h: card.h });
          ctx.restore();
        }
      }
      ctx.restore();
    });
  }

  function infiniteZoom(ctx, layers, progress, options = {}) {
    const p = clamp(progress);
    const centerX = options.centerX ?? ctx.canvas.width / 2;
    const centerY = options.centerY ?? ctx.canvas.height / 2;
    const zoom = options.zoom ?? 4;
    (layers ?? []).forEach((layer, index) => {
      const depth = layer.depth ?? index / Math.max(1, layers.length - 1);
      const scale = Math.pow(zoom, p - depth);
      const visibility = clamp(1 - Math.abs(Math.log2(Math.max(scale, 0.0001))) / (options.fadeRange ?? 3));
      ctx.save();
      ctx.globalAlpha = visibility * (layer.alpha ?? 1);
      ctx.translate(centerX + (layer.x ?? 0) * scale, centerY + (layer.y ?? 0) * scale);
      ctx.scale(scale, scale);
      if (typeof layer.draw === "function") layer.draw(ctx, { progress: p, scale, depth });
      else if (layer.image) ctx.drawImage(layer.image, -(layer.w ?? layer.image.width) / 2, -(layer.h ?? layer.image.height) / 2, layer.w ?? layer.image.width, layer.h ?? layer.image.height);
      ctx.restore();
    });
  }

  function matchCut(ctx, from, to, progress, draw, options = {}) {
    if (typeof draw !== "function") return;
    const p = smooth(progress);
    const state = {
      x: mix(from.x ?? 0, to.x ?? 0, p),
      y: mix(from.y ?? 0, to.y ?? 0, p),
      scaleX: mix(from.scaleX ?? from.scale ?? 1, to.scaleX ?? to.scale ?? 1, p),
      scaleY: mix(from.scaleY ?? from.scale ?? 1, to.scaleY ?? to.scale ?? 1, p),
      rotation: mix(from.rotation ?? 0, to.rotation ?? 0, p),
      alpha: mix(from.alpha ?? 1, to.alpha ?? 1, p),
    };
    ctx.save();
    ctx.globalAlpha = state.alpha * (options.alpha ?? 1);
    ctx.translate(state.x, state.y);
    ctx.rotate(state.rotation);
    ctx.scale(state.scaleX, state.scaleY);
    draw(ctx, state);
    ctx.restore();
  }

  global.BROLL_FX = Object.freeze({
    clamp, mix, smooth, outBack, enter, progress, frameIndex,
    seeded, seededHashed, requiredFont, prepare, roundRect,
    glassCard, scanlines, vhsNoise, neonText, highlighter,
    roughCircle, popBurst, terminalPanel, editorialRule,
    minimalBars, flapText, kineticText, shapeMorph, particleReveal,
    drawCover, parallaxImage, timelinePath, explodedView,
    sampleEnvelope, audioPulse, bentoShowcase, infiniteZoom, matchCut,
  });
})(window);
