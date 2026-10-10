# Tacky Templates

Use this library when a request benefits from a complete designed motion system rather
than one isolated Canvas helper. The bundled name is **Tacky
Templates**. Do not present it under a previous package or creator name.

## Choose the asset type

- Use `assets/broll-effects.js` for a small deterministic overlay or an original scene.
- Use a Tacky template for a complete title card with a coherent type, color, texture,
  entrance, hold, and exit system.
- Use `effects-gallery` to inspect motion primitives and then adapt only the effects the
  current story needs. Do not place all effects in one video.

## Commands

```bash
canvas-video tacky list
canvas-video tacky gallery
```

Copy a template, edit only its `CONFIG`, and render it with the isolated template engine:

```bash
canvas-video tacky copy-template vox ./title-card.html
canvas-video tacky render-template ./title-card.html ./title-card.mp4 --dur=8 --fps=30 --ffmpeg=ffmpeg
```

The installer prepares the Tacky template engine in its own `node_modules`. It must not
share dependencies with the Canvas runtime or HyperFrames.

## Ten style families and 31 templates

| Family | Templates | Best use |
|---|---|---|
| Vox documentary | `vox`, `vox_chart`, `vox_news`, `vox_board` | claims, data, sources, causal explanations |
| Minimal | `minimal`, `minimal_chart`, `minimal_steps` | corporate copy, metrics, frameworks |
| Pop Art | `pop`, `pop_chart`, `pop_strip` | hot takes, comic beats, energetic data |
| VHS | `vhs`, `vhs_chart`, `vhs_log` | memory, chronology, analog signal language |
| Pastel Code | `pastel`, `pastel_steps`, `pastel_log` | software, workflows, development history |
| Dark Terminal | `darkterm`, `darkterm_top`, `darkterm_status` | commands, monitoring, progress states |
| Editorial | `editorial`, `editorial_quote`, `editorial_contents` | premium statements, quotes, structured lists |
| Neon | `neon`, `neon_menu`, `neon_score` | nightlife, music, menus, scoreboards |
| Liquid Glass | `glass`, `glass_widgets`, `glass_notif` | premium UI, statistics, notification stacks |
| Split-flap | `flap`, `flap_board`, `flap_stats` | schedules, status boards, mechanical numbers |

Read the matching card under `assets/tacky-templates/styles/` before editing a template.
Preview `assets/tacky-templates/gallery.html` when the user has not selected a family.

## Effects demonstrated in the gallery

- Entrances: fade, slide, overshoot scale, center growth, mask reveal, stroke draw,
  typewriter, and character pop.
- Data: counter, growing bars, shape morph, ranking race, line draw, radial reveal,
  focus isolation, and benchmark line.
- Transitions: crossfade, push, wipe, zoom-through, and circular reveal.
- Atmosphere: seeded particles, breathing glow, animated gradient, geometric field, and
  subtle camera push/shake.
- Timing: ease-out, ease-in-out, back-out, spring, and stagger.

## Adaptation and review rules

- Templates are starting systems, not finished user deliverables. Replace demo facts,
  labels, sources, logos, and brand colors.
- The template engine virtualizes timers and CSS animation for frame rendering. Canvas
  scenes still follow the normal `window.seek(t)` contract.
- Several templates contain Google Fonts links. For offline, repeatable, or commercial
  delivery, replace them with locally bundled, properly licensed `@font-face` files.
- Render entrance, focal reveal, and hold stills before the full clip.
- Keep one focal idea per card and one primary visual family per sequence.
- Treat any sample metric as placeholder content; never deliver it as a factual claim.
