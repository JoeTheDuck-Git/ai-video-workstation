import { existsSync, readFileSync } from 'node:fs';
import { isAbsolute, resolve, sep } from 'node:path';

export function loadProject(directory) {
  const root = resolve(directory);
  const manifestPath = resolve(root, 'canvas-video.json');
  if (!existsSync(manifestPath)) throw new Error(`Missing canvas-video.json in ${root}`);
  const manifest = JSON.parse(readFileSync(manifestPath, 'utf8'));
  if (manifest.version !== 1) throw new Error(`Unsupported manifest version: ${manifest.version}`);
  if (typeof manifest.entry !== 'string' || !manifest.entry.endsWith('.html')) throw new Error('entry must be an HTML file');
  if (isAbsolute(manifest.entry)) throw new Error('entry must be relative to the project');
  const entryPath = resolve(root, manifest.entry);
  if (entryPath !== root && !entryPath.startsWith(`${root}${sep}`)) throw new Error('entry escapes the project directory');
  if (!existsSync(entryPath)) throw new Error(`Missing entry file: ${manifest.entry}`);

  const width = Number(manifest.width);
  const height = Number(manifest.height);
  const fps = Number(manifest.fps);
  const duration = Number(manifest.duration);
  if (!Number.isInteger(width) || width < 1 || width > 7680) throw new Error('width must be an integer from 1 to 7680');
  if (!Number.isInteger(height) || height < 1 || height > 7680) throw new Error('height must be an integer from 1 to 7680');
  if (!Number.isFinite(fps) || fps <= 0 || fps > 120) throw new Error('fps must be greater than 0 and at most 120');
  if (!Number.isFinite(duration) || duration <= 0 || duration > 3600) throw new Error('duration must be greater than 0 and at most 3600 seconds');
  if (!['opaque', 'transparent'].includes(manifest.background)) throw new Error('background must be opaque or transparent');

  return { ...manifest, root, manifestPath, entryPath, width, height, fps, duration };
}
