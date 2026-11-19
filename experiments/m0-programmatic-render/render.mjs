// M0：程式碼動畫逐幀渲染測試（無頭 Chromium → FFmpeg）
// 用法：node render.mjs [--width 1280] [--height 720] [--fps 30] [--duration 5]
//                       [--format png|jpeg] [--codec auto|libx264|h264_videotoolbox] [--out out/m0.mp4]
import { chromium } from "playwright";
import { spawn, spawnSync } from "node:child_process";
import { createHash } from "node:crypto";
import { mkdirSync, writeFileSync, statSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import os from "node:os";

const here = dirname(fileURLToPath(import.meta.url));
const argv = process.argv.slice(2);
const opt = (name, def) => { const i = argv.indexOf("--" + name); return i >= 0 ? argv[i + 1] : def; };
const width = +opt("width", 1280), height = +opt("height", 720);
const fps = +opt("fps", 30), duration = +opt("duration", 5);
const format = opt("format", "png");
const codecArg = opt("codec", "auto");
const outFile = resolve(here, opt("out", "out/m0.mp4"));
const frames = Math.round(fps * duration);

const checks = [];
const check = (name, ok, detail = "") => { checks.push({ name, ok, detail }); console.log(`${ok ? "PASS" : "FAIL"}  ${name}${detail ? "  — " + detail : ""}`); return ok; };
const run = (cmd, args) => spawnSync(cmd, args, { encoding: "utf8" });

// 0) 環境
const ffv = run("ffmpeg", ["-version"]);
if (!check("ffmpeg 可執行", ffv.status === 0, ffv.stdout?.split("\n")[0])) { console.error("請先安裝 FFmpeg（macOS：brew install ffmpeg）"); process.exit(1); }
if (!check("ffprobe 可執行", run("ffprobe", ["-version"]).status === 0)) process.exit(1);
const encoders = run("ffmpeg", ["-hide_banner", "-encoders"]).stdout;
const hasVT = /h264_videotoolbox/.test(encoders), hasX264 = /libx264/.test(encoders);
check("H.264 編碼器", hasVT || hasX264, `libx264=${hasX264} videotoolbox=${hasVT}`);
const codec = codecArg === "auto" ? (hasX264 ? "libx264" : "h264_videotoolbox") : codecArg;
const codecArgs = codec === "h264_videotoolbox" ? ["-c:v", "h264_videotoolbox", "-b:v", "8M"] : ["-c:v", "libx264", "-preset", "medium", "-crf", "18"];

mkdirSync(dirname(outFile), { recursive: true });

// 1) 瀏覽器與字型
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width, height }, deviceScaleFactor: 1 });
await page.goto(pathToFileURL(resolve(here, "animation.html")).href);
check("動畫頁載入且字型就緒", await page.evaluate(() => window.__ready) === true);
const cjk = await page.evaluate(() => { const c = document.createElement("canvas").getContext("2d"); c.font = "40px sans-serif"; return c.measureText("測").width > 20; });
check("中文字可量測寬度", cjk);

const shot = async t => { await page.evaluate(x => window.renderFrame(x), t); return page.screenshot({ type: format, ...(format === "jpeg" ? { quality: 95 } : {}) }); };
const sha = b => createHash("sha256").update(b).digest("hex");

// 2) 確定性：同一時間點擷取兩次，位元組必須相同
const a = await shot(2.0); await shot(0.3); const b = await shot(2.0);
check("確定性（同一 t 兩次擷取相同）", sha(a) === sha(b), sha(a).slice(0, 12));
const c = await shot(2.5);
check("不同 t 畫面不同（動畫有在動）", sha(a) !== sha(c));

// 3) 逐幀渲染並串流給 FFmpeg
const inCodec = format === "png" ? "png" : "mjpeg";
const ff = spawn("ffmpeg", ["-hide_banner", "-loglevel", "error", "-y", "-f", "image2pipe", "-framerate", String(fps), "-c:v", inCodec, "-i", "-",
  ...codecArgs, "-pix_fmt", "yuv420p", "-r", String(fps), "-movflags", "+faststart", outFile], { stdio: ["pipe", "inherit", "pipe"] });
let ffErr = ""; ff.stderr.on("data", d => ffErr += d);
const ffDone = new Promise(res => ff.on("close", res));
ff.stdin.on("error", () => {});

const t0 = performance.now(); const times = []; let peakRss = 0;
for (let i = 0; i < frames; i++) {
  const s = performance.now();
  const buf = await shot(i / fps);
  times.push(performance.now() - s);
  if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once("drain", r));
  peakRss = Math.max(peakRss, process.memoryUsage().rss);
  if (i % 30 === 0) process.stdout.write(`\r渲染 ${i + 1}/${frames}`);
}
ff.stdin.end();
const code = await ffDone;
const wall = (performance.now() - t0) / 1000;
await browser.close();
console.log("");
check("FFmpeg 正常結束", code === 0, ffErr.trim().slice(0, 200));

// 4) 驗證輸出
const probe = JSON.parse(run("ffprobe", ["-v", "error", "-count_frames", "-select_streams", "v:0", "-show_entries",
  "stream=codec_name,width,height,pix_fmt,avg_frame_rate,nb_read_frames:format=duration,size", "-of", "json", outFile]).stdout || "{}");
const st = probe.streams?.[0] ?? {};
check("解析度正確", st.width === width && st.height === height, `${st.width}x${st.height}`);
check("影格數正確", +st.nb_read_frames === frames, `${st.nb_read_frames}/${frames}`);
check("時長正確（±1 幀）", Math.abs(+probe.format?.duration - duration) <= 1 / fps + 1e-3, `${probe.format?.duration}s`);
check("像素格式 yuv420p（相容性）", st.pix_fmt === "yuv420p", st.pix_fmt);

// 5) 效能報告
times.sort((x, y) => x - y);
const pct = p => times[Math.min(times.length - 1, Math.floor(times.length * p))];
const report = {
  when: new Date().toISOString(),
  machine: { platform: process.platform, arch: process.arch, cpu: os.cpus()[0]?.model, cores: os.cpus().length, memGB: +(os.totalmem() / 2 ** 30).toFixed(1), node: process.version },
  settings: { width, height, fps, duration, frames, format, codec },
  perf: { wallSeconds: +wall.toFixed(2), renderFps: +(frames / wall).toFixed(2), realtimeFactor: +((frames / fps) / wall).toFixed(2),
          frameMs: { mean: +(times.reduce((s, x) => s + x, 0) / times.length).toFixed(1), p50: +pct(.5).toFixed(1), p95: +pct(.95).toFixed(1), max: +times[times.length - 1].toFixed(1) },
          nodeRssMB: +(peakRss / 2 ** 20).toFixed(0) },
  output: { file: outFile, bytes: statSync(outFile).size, probe: st },
  checks,
};
writeFileSync(resolve(dirname(outFile), "report.json"), JSON.stringify(report, null, 2));
console.log(`\n${width}x${height}@${fps} ${frames} 幀，耗時 ${wall.toFixed(1)}s，${report.perf.renderFps} 幀/秒（即時倍率 ${report.perf.realtimeFactor}x）`);
console.log(`每幀 ms：平均 ${report.perf.frameMs.mean}，p95 ${report.perf.frameMs.p95}，最大 ${report.perf.frameMs.max}`);
console.log(`輸出：${outFile}（${(report.output.bytes / 1024).toFixed(0)} KB）\n報告：${resolve(dirname(outFile), "report.json")}`);
process.exit(checks.every(x => x.ok) ? 0 : 1);
