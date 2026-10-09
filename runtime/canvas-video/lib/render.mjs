import { mkdirSync, writeFileSync } from 'node:fs';
import { basename, dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawn } from 'node:child_process';
import { chromium } from 'playwright';
import { loadProject } from './project.mjs';
import { startServer } from './server.mjs';

const runtimeRoot = resolve(dirname(fileURLToPath(import.meta.url)), '..');

function finite(value, label) {
  if (!Number.isFinite(value)) throw new Error(`${label} must be a finite number`);
  return value;
}

function ffmpegArgs(project, options, output) {
  const common = ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(project.fps), '-i', '-'];
  if (options.alpha) return [...common, '-c:v', 'qtrle', '-pix_fmt', 'argb', output];
  if (options.prores) return [...common, '-c:v', 'prores_ks', '-profile:v', '3', '-pix_fmt', 'yuv422p10le', output];
  return [...common, '-c:v', 'libx264', '-preset', 'slow', '-crf', String(options.crf), '-pix_fmt', 'yuv420p', '-movflags', '+faststart', output];
}

export async function renderProject(directory, options = {}) {
  const project = loadProject(directory);
  const from = finite(options.from ?? 0, 'from');
  const to = finite(options.to ?? project.duration, 'to');
  if (from < 0 || to <= from || to > project.duration) throw new Error(`render range must satisfy 0 <= from < to <= ${project.duration}`);
  if (options.still !== undefined && (options.still < 0 || options.still > project.duration)) throw new Error('still time is outside the project duration');
  if (!Number.isInteger(options.motionBlur ?? 1) || (options.motionBlur ?? 1) < 1 || (options.motionBlur ?? 1) > 64) throw new Error('motion-blur must be an integer from 1 to 64');
  finite(options.shutter ?? 0.5, 'shutter');
  finite(options.crf ?? 16, 'crf');

  const outputDir = join(project.root, 'out');
  mkdirSync(outputDir, { recursive: true });
  const baseName = basename(project.entry, '.html');
  const defaultExt = options.alpha || options.prores ? 'mov' : 'mp4';
  const output = resolve(options.output ?? join(outputDir, options.still === undefined ? `${baseName}.${defaultExt}` : `${baseName}-${Number(options.still).toFixed(2)}.png`));
  mkdirSync(dirname(output), { recursive: true });

  const { server, port } = await startServer(project.root, runtimeRoot);
  let browser;
  try {
    const gpuArgs = process.platform === 'linux'
      ? ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist']
      : ['--ignore-gpu-blocklist'];
    browser = await chromium.launch({ headless: true, args: gpuArgs });
    const page = await browser.newPage({ viewport: { width: project.width, height: project.height } });
    page.on('pageerror', error => console.error(`Canvas page error: ${error.message}`));
    const entryUrl = new URL(project.entry, `http://127.0.0.1:${port}/`);
    entryUrl.searchParams.set('render', '1');
    await page.goto(entryUrl.href, { waitUntil: 'load' });
    await page.waitForFunction(() => window.ready !== undefined && typeof window.seek === 'function' && window.CANVAS instanceof HTMLCanvasElement);
    await page.evaluate(() => window.ready);
    const pageContract = await page.evaluate(() => ({
      width: window.CANVAS.width,
      height: window.CANVAS.height,
      duration: window.DURATION,
      fps: window.FPS,
    }));
    if (pageContract.width !== project.width || pageContract.height !== project.height) {
      throw new Error(`scene canvas ${pageContract.width}x${pageContract.height} does not match manifest ${project.width}x${project.height}`);
    }
    if (pageContract.duration !== undefined && Math.abs(Number(pageContract.duration) - project.duration) > 1e-9) throw new Error('scene duration does not match manifest');
    if (pageContract.fps !== undefined && Math.abs(Number(pageContract.fps) - project.fps) > 1e-9) throw new Error('scene FPS does not match manifest');

    const grab = async time => {
      const fixedSamples = options.motionBlur;
      const samples = fixedSamples ?? await page.evaluate(t => {
        if (typeof window.motionBlurAt === 'function') return window.motionBlurAt(t);
        return window.MOTION_BLUR ?? 1;
      }, time);
      const count = Math.max(1, Math.min(64, Math.round(Number(samples) || 1)));
      const dataUrl = await page.evaluate(async ({ time, count, shutter, fps, duration }) => {
        const source = window.CANVAS;
        let rendered = source;
        if (count === 1) {
          await window.seek(time);
        } else {
          const accumulator = window.__canvasVideoAccumulator ??= Object.assign(document.createElement('canvas'), { width: source.width, height: source.height });
          const context = accumulator.getContext('2d');
          context.globalCompositeOperation = 'copy';
          context.globalAlpha = 1;
          context.clearRect(0, 0, accumulator.width, accumulator.height);
          for (let index = 0; index < count; index += 1) {
            const sampleTime = Math.min(duration, Math.max(0, time + (index / (count - 1) - 0.5) * shutter / fps));
            await window.seek(sampleTime);
            context.globalCompositeOperation = index === 0 ? 'copy' : 'source-over';
            context.globalAlpha = 1 / (index + 1);
            context.drawImage(source, 0, 0);
          }
          context.globalAlpha = 1;
          rendered = accumulator;
        }
        return rendered.toDataURL('image/png');
      }, { time, count, shutter: options.shutter ?? 0.5, fps: project.fps, duration: project.duration });
      return Buffer.from(dataUrl.split(',')[1], 'base64');
    };

    if (options.still !== undefined) {
      writeFileSync(output, await grab(Number(options.still)));
      return { ok: true, type: 'still', output, width: project.width, height: project.height, time: Number(options.still) };
    }

    const firstFrame = Math.round(from * project.fps);
    const lastFrame = Math.round(to * project.fps);
    const ffmpeg = spawn('ffmpeg', ffmpegArgs(project, options, output), { stdio: ['pipe', 'ignore', 'pipe'] });
    let stderr = '';
    ffmpeg.stderr.on('data', chunk => { stderr = `${stderr}${chunk}`.slice(-8000); });
    for (let frame = firstFrame; frame < lastFrame; frame += 1) {
      const png = await grab(frame / project.fps);
      if (!ffmpeg.stdin.write(png)) await new Promise(resolveDrain => ffmpeg.stdin.once('drain', resolveDrain));
    }
    ffmpeg.stdin.end();
    const exitCode = await new Promise((resolveClose, rejectClose) => {
      ffmpeg.once('error', rejectClose);
      ffmpeg.once('close', resolveClose);
    });
    if (exitCode !== 0) throw new Error(`FFmpeg failed with exit ${exitCode}: ${stderr}`);
    return {
      ok: true, type: options.alpha ? 'alpha-video' : options.prores ? 'prores-video' : 'video', output,
      width: project.width, height: project.height, fps: project.fps, from, to, frames: lastFrame - firstFrame,
    };
  } finally {
    if (browser) await browser.close();
    await new Promise(resolveClose => server.close(resolveClose));
  }
}
