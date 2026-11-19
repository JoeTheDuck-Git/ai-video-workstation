# M0：程式碼動畫渲染測試

目的：在 Mac mini（M4）上確認「HTML 動畫 → 無頭 Chromium 逐幀擷取 → FFmpeg → MP4」這條路可用，並量出速度。

## 在 Mac 上執行

```bash
brew install ffmpeg node        # 已安裝可略過
cd experiments/m0-programmatic-render
npm run setup                   # 安裝 playwright 與 Chromium
npm run test:render             # 720p / 30fps / 5 秒
npm run test:draft              # 480p 草稿
npm run test:1080               # 1080p
```

可另外試：`node render.mjs --format jpeg`、`--codec h264_videotoolbox`（硬體編碼）。

## 它檢查什麼

1. ffmpeg／ffprobe 與 H.264 編碼器（libx264、videotoolbox）。
2. 動畫頁載入、字型就緒、中文字可量測。
3. **確定性**：同一時間點在中間插入其他時間點後再擷取，位元組必須相同。
4. 輸出的解析度、影格數、時長、像素格式（yuv420p）。
5. 效能：每秒幾幀、每幀耗時、記憶體；寫入 `out/report.json`。

## 把結果貼回來

- `out/report.json` 的內容（三個設定各一份最好）。
- 看一眼 `out/*.mp4`：中文字有沒有缺字或字型很奇怪、動畫是否平順。

## 設計重點（已在雲端環境驗證）

- 動畫頁只提供 `window.renderFrame(t)`，畫面完全由 t 決定；不用 `requestAnimationFrame`、CSS animation、`Date`、隨機數。
- 會變透明度或位移的元素要固定在合成層（`will-change: transform, opacity`），否則同一 t 會因前一幀狀態而產生不同的文字抗鋸齒，確定性檢查會失敗。這是第一次執行時實際遇到並修好的問題。
- 雲端環境（Linux、Chromium、libx264）結果：720p PNG 約 27 幀/秒、1080p JPEG 約 19 幀/秒。**Mac 的數字不同，請以你的實測為準。**
