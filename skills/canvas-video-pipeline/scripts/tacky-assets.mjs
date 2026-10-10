#!/usr/bin/env node
import { existsSync, mkdirSync, readFileSync, readdirSync, writeFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { spawnSync } from "node:child_process";

const here = path.dirname(fileURLToPath(import.meta.url));
const skill = path.resolve(here, "..");
const templatesRoot = path.join(skill, "assets", "tacky-templates");
const scenesRoot = path.join(skill, "assets", "tacky-scenes");
const templatesDir = path.join(templatesRoot, "templates");

function die(message) {
  console.error(`ERROR: ${message}`);
  process.exit(1);
}

function names(dir) {
  return readdirSync(dir)
    .filter((name) => name.endsWith(".html"))
    .map((name) => name.slice(0, -5))
    .sort();
}

function safeName(value, available, kind) {
  const name = value?.replace(/\.html$/i, "");
  if (!name || !/^[a-z0-9][a-z0-9_-]*$/i.test(name) || !available.includes(name)) {
    die(`Unknown ${kind}: ${value || "(missing)"}`);
  }
  return name;
}

function writeNew(destination, data, force) {
  if (existsSync(destination) && !force) die(`Refusing to replace ${destination}; pass --force to replace it.`);
  mkdirSync(path.dirname(destination), { recursive: true });
  writeFileSync(destination, data);
}

const args = process.argv.slice(2);
const command = args.shift();
const forceAt = args.indexOf("--force");
const force = forceAt >= 0;
if (force) args.splice(forceAt, 1);

const templateNames = names(templatesDir);
switch (command) {
  case "list":
    console.log("Tacky templates:");
    templateNames.forEach((name) => console.log(`  ${name}`));
    console.log("\nEffects gallery:");
    console.log(`  ${path.join(scenesRoot, "scenes", "effects-gallery.html")}`);
    break;

  case "gallery":
    console.log(path.join(templatesRoot, "gallery.html"));
    break;

  case "copy-template": {
    const name = safeName(args[0], templateNames, "template");
    const destination = path.resolve(args[1] || `${name}.html`);
    writeNew(destination, readFileSync(path.join(templatesDir, `${name}.html`)), force);
    console.log(destination);
    break;
  }

  case "render-template": {
    const sourceArg = args.shift();
    const outputArg = args.shift();
    if (!sourceArg || !outputArg) die("Usage: tacky-assets.mjs render-template <name-or-html> <output.mp4> [renderer options]");
    const candidate = path.resolve(sourceArg);
    const source = existsSync(candidate)
      ? candidate
      : path.join(templatesDir, `${safeName(sourceArg, templateNames, "template")}.html`);
    const engine = path.join(templatesRoot, "engine", "render-template.mjs");
    const result = spawnSync(process.execPath, [engine, source, path.resolve(outputArg), ...args], { stdio: "inherit" });
    process.exit(result.status ?? 1);
  }

  default:
    die("Usage: tacky-assets.mjs <list|gallery|copy-template|render-template> ...");
}
