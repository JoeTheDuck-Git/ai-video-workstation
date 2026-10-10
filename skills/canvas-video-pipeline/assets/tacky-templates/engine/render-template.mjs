/*
 * render-template.mjs — 把 Tacky 風格模板直接渲染成影片（免螢幕錄影）
 * 用法：node render-template.mjs <模板.html> <輸出.mp4> [--dur=8] [--fps=30] [--ffmpeg=路徑]
 * 尺寸自動照模板 CONFIG.orientation（portrait 1080×1920／landscape 1920×1080）。
 */
import { existsSync } from "node:fs";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { spawn, spawnSync } from "node:child_process";
import { chromium } from "playwright-core";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const args = process.argv.slice(2);
const files = args.filter((a) => !a.startsWith("--"));
const opt = (name, dflt) => {
  const hit = args.find((a) => a.startsWith(`--${name}=`));
  return hit ? hit.split("=").slice(1).join("=") : dflt;
};
const tplPath = path.resolve(files[0] || "");
const outPath = path.resolve(files[1] || "card.mp4");
const DUR = parseFloat(opt("dur", "8"));
const FPS = parseInt(opt("fps", "30"), 10);
const FFMPEG = opt("ffmpeg", "ffmpeg");
if (!existsSync(tplPath)) { console.error("找不到模板：" + tplPath); process.exit(1); }
const ffmpegCheck = spawnSync(FFMPEG, ["-version"], { stdio: "ignore" });
if (ffmpegCheck.error || ffmpegCheck.status !== 0) {
  console.error("找不到可執行的 FFmpeg：" + FFMPEG);
  process.exit(1);
}

function findChrome() {
  const candidates = [
    process.env.CHROME_PATH,
    chromium.executablePath(),
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
    "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
    "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe",
  ].filter(Boolean);
  for (const p of candidates) if (existsSync(p)) return p;
  console.error("找不到 Tacky Templates 可用的 Chromium、Chrome 或 Edge；請重新執行工作站安裝器，或設定 CHROME_PATH");
  process.exit(1);
}

const browser = await chromium.launch({
  executablePath: findChrome(),
  headless: true,
  args: ["--force-color-profile=srgb", "--font-render-hinting=none", "--hide-scrollbars"],
});
const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
await page.addInitScript({ path: path.join(__dirname, "seek-shim.js") });
await page.goto(pathToFileURL(tplPath).href);
await page.evaluate(() => document.fonts.ready.then(() => true));

// 尺寸照模板 CONFIG；沒有 CONFIG 的模板退回預設橫式
const [W, H] = await page.evaluate(() => {
  try { return CONFIG.orientation === "portrait" ? [1080, 1920] : [1920, 1080]; }
  catch (e) { return [1920, 1080]; }
});
await page.setViewportSize({ width: W, height: H });
await page.evaluate(() => window.__seekInit());

const ff = spawn(FFMPEG, [
  "-y", "-v", "error",
  "-f", "image2pipe", "-framerate", String(FPS), "-c:v", "png", "-i", "-",
  "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "17", outPath,
], { stdio: ["pipe", "inherit", "inherit"] });

const frames = Math.ceil(DUR * FPS);
console.log(`渲染 ${path.basename(tplPath)}：${frames} 格 @ ${FPS}fps（${DUR}s，${W}x${H}）`);
const t0 = Date.now();

for (let i = 0; i < frames; i++) {
  await page.evaluate((t) => window.__tick(t), i / FPS);
  const buf = await page.screenshot({ type: "png" });
  if (!ff.stdin.write(buf)) await new Promise((r) => ff.stdin.once("drain", r));
  if (i > 0 && i % 90 === 0) {
    const rate = i / ((Date.now() - t0) / 1000);
    console.log(`  ${i}/${frames}（${rate.toFixed(1)} fps）`);
  }
}
ff.stdin.end();
await new Promise((res, rej) => ff.on("exit", (c) => (c === 0 ? res() : rej(new Error("ffmpeg exit " + c)))));
await browser.close();
console.log(`完成：${outPath}（片長 ${DUR}s，渲染耗時 ${((Date.now() - t0) / 1000).toFixed(1)}s）`);
