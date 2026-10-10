#!/usr/bin/env node
import { accessSync, constants, cpSync, existsSync, mkdirSync, statSync } from 'node:fs';
import { homedir } from 'node:os';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';
import { chromium } from 'playwright';
import { loadProject } from '../lib/project.mjs';
import { renderProject } from '../lib/render.mjs';

const runtimeRoot = resolve(dirname(fileURLToPath(import.meta.url)), '..');

function parse(tokens) {
  const positionals = [];
  const flags = {};
  for (let index = 0; index < tokens.length; index += 1) {
    const token = tokens[index];
    if (!token.startsWith('--')) {
      positionals.push(token);
      continue;
    }
    const key = token.slice(2);
    const next = tokens[index + 1];
    if (next !== undefined && !next.startsWith('--')) {
      flags[key] = next;
      index += 1;
    } else {
      flags[key] = true;
    }
  }
  return { positionals, flags };
}

function usage() {
  console.log(`canvas-video

Usage:
  canvas-video doctor [--json]
  canvas-video init <directory> --aspect portrait|landscape
  canvas-video inspect <project> [--json]
  canvas-video render <project> [--still seconds] [--from seconds] [--to seconds]
                      [--output file] [--alpha|--prores] [--crf number]
                      [--motion-blur samples] [--shutter frames]
  canvas-video tacky <list|gallery|copy-template|render-template> [...args]
`);
}

function fail(message) {
  console.error(`canvas-video: ${message}`);
  process.exit(1);
}

async function doctor(asJson) {
  const checks = [];
  const nodeMajor = Number(process.versions.node.split('.')[0]);
  checks.push({ name: 'Node.js 22+', ok: nodeMajor >= 22, detail: process.version });
  const ffmpeg = spawnSync('ffmpeg', ['-version'], { encoding: 'utf8' });
  checks.push({
    name: 'FFmpeg',
    ok: ffmpeg.status === 0,
    detail: ffmpeg.status === 0 ? ffmpeg.stdout.split('\n')[0] : 'not found',
  });
  const browserPath = chromium.executablePath();
  let browserOk = false;
  try {
    accessSync(browserPath, constants.X_OK);
    browserOk = true;
  } catch {}
  checks.push({ name: 'Playwright Chromium', ok: browserOk, detail: browserPath });
  const result = { ok: checks.every(item => item.ok), checks };
  if (asJson) console.log(JSON.stringify(result, null, 2));
  else for (const item of checks) console.log(`${item.ok ? 'PASS' : 'FAIL'}  ${item.name}: ${item.detail}`);
  if (!result.ok) process.exitCode = 1;
}

function initProject(directory, aspect) {
  if (!['portrait', 'landscape'].includes(aspect)) fail('--aspect must be portrait or landscape');
  const destination = resolve(directory);
  if (existsSync(destination)) fail(`destination already exists: ${destination}`);
  mkdirSync(dirname(destination), { recursive: true });
  cpSync(join(runtimeRoot, 'templates', aspect), destination, { recursive: true, errorOnExist: true });
  console.log(`Created ${aspect} Canvas video project: ${destination}`);
}

function findTackyHelper() {
  if (process.env.AI_VIDEO_SKILLS_ROOT) {
    const explicit = join(process.env.AI_VIDEO_SKILLS_ROOT, 'canvas-video-pipeline', 'scripts', 'tacky-assets.mjs');
    if (existsSync(explicit)) return explicit;
    fail(`Tacky Templates helper was not found under AI_VIDEO_SKILLS_ROOT: ${process.env.AI_VIDEO_SKILLS_ROOT}`);
  }
  const skillRoots = [
    process.env.CODEX_HOME ? join(process.env.CODEX_HOME, 'skills') : join(homedir(), '.codex', 'skills'),
    process.env.CLAUDE_HOME ? join(process.env.CLAUDE_HOME, 'skills') : join(homedir(), '.claude', 'skills'),
  ];
  const helpers = skillRoots
    .map(root => join(root, 'canvas-video-pipeline', 'scripts', 'tacky-assets.mjs'))
    .filter(existsSync)
    .sort((a, b) => statSync(b).mtimeMs - statSync(a).mtimeMs);
  if (helpers[0]) return helpers[0];
  fail('Tacky Templates helper was not found. Reinstall the canvas-video-pipeline Skill for Codex or Claude Code.');
}

function runTacky(tokens) {
  if (tokens.length === 0) fail('tacky requires list, gallery, copy-template, or render-template');
  const result = spawnSync(process.execPath, [findTackyHelper(), ...tokens], { stdio: 'inherit' });
  if (result.error) fail(result.error.message);
  process.exitCode = result.status ?? 1;
}

const [command, ...rest] = process.argv.slice(2);
const { positionals, flags } = parse(rest);

if (!command || command === 'help' || flags.help) {
  usage();
  process.exit(0);
}

if (command === 'doctor') {
  await doctor(Boolean(flags.json));
} else if (command === 'init') {
  if (!positionals[0]) fail('init requires a destination directory');
  initProject(positionals[0], String(flags.aspect ?? 'landscape'));
} else if (command === 'inspect') {
  if (!positionals[0]) fail('inspect requires a project directory');
  const project = loadProject(positionals[0]);
  if (flags.json) console.log(JSON.stringify(project, null, 2));
  else console.log(`${project.root}\n${project.width}x${project.height} · ${project.fps} fps · ${project.duration}s · ${project.entry}`);
} else if (command === 'render') {
  if (!positionals[0]) fail('render requires a project directory');
  if (flags.alpha && flags.prores) fail('--alpha and --prores are mutually exclusive');
  const result = await renderProject(positionals[0], {
    still: flags.still === undefined ? undefined : Number(flags.still),
    from: flags.from === undefined ? undefined : Number(flags.from),
    to: flags.to === undefined ? undefined : Number(flags.to),
    output: flags.output,
    alpha: Boolean(flags.alpha),
    prores: Boolean(flags.prores),
    crf: flags.crf === undefined ? 16 : Number(flags.crf),
    motionBlur: flags['motion-blur'] === undefined ? undefined : Number(flags['motion-blur']),
    shutter: flags.shutter === undefined ? 0.5 : Number(flags.shutter),
  });
  console.log(JSON.stringify(result, null, 2));
} else if (command === 'tacky') {
  runTacky(rest);
} else {
  usage();
  fail(`unknown command: ${command}`);
}
