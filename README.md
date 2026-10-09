# AI Video Workstation Bootstrap

把本機 AI 影片工作環境用一個可重複執行的安裝流程建立起來。這個套件目前以 macOS／Linux 為主，會安裝或設定：

- Node.js 22（從 Node.js 官方發行檔下載並驗證 SHA-256）
- FFmpeg／FFprobe（優先沿用既有安裝，缺少時使用系統套件管理器）
- HyperFrames CLI 與核心 Skills
- 即夢畫布 `dreamina-canvas` CLI／Skill（執行即夢官方安裝器）
- 獨立的 `canvas-video` 確定性 Canvas／Three.js renderer
- `canvas-video-pipeline` Skill，串接即夢、Canvas motion、HyperFrames 與 QC
- 本倉庫附帶的 `video-delivery-qc` 社群影片交付檢查 Skill
- 可選擇從使用者合法持有的 Hello Irene 套件導入 `footage-sifter`、
  `caption-doctor` 與 `subtitle-translator`；私人原始碼不會提交到本倉庫
- 第二階段可另外導入 `beat-cut-editor`；Canvas Skill 內建原創、確定性的
  B-roll 效果 API，不複製私有 HTML 模板

第三方程式與第三方 Skills 不直接收進本倉庫，而是在安裝時從官方來源取得。登入憑證、Cookie、API Key、生成素材與影片也不會進入 Git。

## 快速安裝

```bash
git clone https://github.com/JoeTheDuck-Git/ai-video-workstation.git
cd ai-video-workstation
./install.sh
```

若本機已有合法取得的 `hello-irene-codex` 資料夾，可在安裝時只導入三個互補 Skill：

```bash
./install.sh --irene-source "$HOME/Downloads/hello-irene-codex"
```

已完成主安裝時，也可以獨立導入：

```bash
./scripts/import-irene-skills.sh "$HOME/Downloads/hello-irene-codex"
```

導入器會先確認三個 `SKILL.md` 存在，將既有同名 Skill 備份，再複製到
`~/.codex/skills/`。字幕所需的 `opencc` 與 `jieba` 安裝在隔離的
`~/.irene/venv`，不會修改系統 Python。

第二階段導入節拍剪輯（會保留本機來源內的音樂／音效，但不會把它們提交到本倉庫）：

```bash
./scripts/import-irene-stage2.sh "$HOME/Downloads/hello-irene-codex"
# 或連同主安裝一起：
./install.sh --irene-stage2-source "$HOME/Downloads/hello-irene-codex"
```

核心剪輯依賴會放在 `~/.irene/venv`。Whisper 語音模型與自帶歌曲分析所需的
`faster-whisper`／`librosa` 採需要時才安裝，避免首次安裝先下載大型模型。

若要一次安裝 HyperFrames 發布的完整 Skill 集合：

```bash
./install.sh --all-hyperframes-skills
```

安裝完畢後進行即夢登入：

```bash
./scripts/login.sh
```

若也需要 HyperFrames／HeyGen 的雲端功能授權：

```bash
./scripts/login.sh --with-hyperframes
```

隨時重新檢查環境：

```bash
./scripts/verify.sh
```

## 安裝行為

### Node.js 22

安裝器會從 `https://nodejs.org/dist/latest-v22.x/` 下載目前的 Node.js 22 發行檔，並依官方 `SHASUMS256.txt` 驗證。檔案放在：

```text
~/.local/share/ai-video-workstation/
```

安裝器會在 `~/.zprofile`（macOS）或 `~/.profile`（Linux）加入一個有明確起訖標記的 PATH 區塊。它不會覆寫系統 Node.js。

### FFmpeg

- 已存在 `ffmpeg` 與 `ffprobe`：直接沿用。
- macOS：使用 Homebrew 的 `ffmpeg` formula；若尚未安裝 Homebrew，安裝器會停止並提供官方安裝連結。
- Debian／Ubuntu：使用 `apt-get`。
- Fedora／RHEL：使用 `dnf`。
- Arch Linux：使用 `pacman`。

### HyperFrames

CLI 透過 npm 安裝至 `~/.local`，不需要 `sudo`：

```bash
npm install -g --prefix "$HOME/.local" hyperframes@latest
```

預設執行 `hyperframes skills update`，安裝／更新核心 Skills。傳入 `--all-hyperframes-skills` 時會執行 `hyperframes skills`，安裝官方發布的完整集合。

### 即夢畫布

安裝器會先把官方腳本下載到暫存檔，再交給 Bash 執行：

```text
https://jimeng.jianying.com/canvas-cli/install.sh
```

帳號登入刻意與安裝分開；請在自己的互動式終端執行 `./scripts/login.sh`，依瀏覽器畫面完成授權。

### Canvas Video Pipeline

Canvas renderer 安裝在獨立目錄，不與 HyperFrames 共用 `node_modules`：

```text
~/.local/share/ai-video-workstation/canvas-video/
```

建立原生比例專案：

```bash
canvas-video init ./motion-landscape --aspect landscape
canvas-video init ./motion-portrait --aspect portrait
canvas-video render ./motion-portrait --still 2.5
canvas-video render ./motion-portrait
```

橫式模板為 1920×1080，直式模板為 1080×1920；兩者具有各自的排版，不以裁切冒充直式構圖。Canvas 輸出會作為普通媒體素材交給 HyperFrames，最終成片再由 QC Skill 實測。

`canvas-video-pipeline/assets/broll-effects.js` 提供 documentary marker、minimal bars、
comic burst、VHS scanlines/noise、terminal panel、editorial rule、neon tube、glass card 與
split-flap 等確定性 Canvas helper，並包含 kinetic type、shape morph、particle reveal、
infinite zoom、parallax、timeline path、exploded view、預先計算音訊包絡、Bento 與 match cut。
每次以 `time` 明確驅動，適合做可重現的標題卡與透明疊加層。

### 社群影片 QC Skill

`skills/video-delivery-qc` 是本套件隨附的 Skill。它會檢查影片解碼、黑畫面／凍結／靜音、容器與編碼、畫面比例、字幕時間、語音同步抽查提示及社群交付音量等項目。

範例：

```bash
python3 ~/.codex/skills/video-delivery-qc/scripts/video_qc.py \
  path/to/video.mp4 \
  --srt path/to/subtitles.srt \
  --profile social
```

## 驗證標準

`scripts/verify.sh` 會檢查：

1. Node.js 主版本是否至少為 22。
2. npm、FFmpeg、FFprobe 是否可執行。
3. HyperFrames 版本、`doctor` 與 Skill 狀態。
4. 即夢 CLI 版本與登入狀態。
5. `canvas-video` renderer 與 Playwright Chromium 是否可執行。
6. `canvas-video-pipeline` 和 `video-delivery-qc` Skills 是否可載入。

未登入即夢不會被當成安裝失敗；驗證結果會清楚提示下一步。

## 更新

重新執行安裝器即可更新 Node.js 22、HyperFrames、HyperFrames Skills、即夢 CLI／Skill、Canvas runtime 與 QC Skill：

```bash
./install.sh
```

## 安全與隱私

- 不要把 `~/.heygen`、即夢登入資料、Cookie、API Key 或 `.env` 提交到 Git。
- 安裝器不會讀取或輸出登入憑證。
- Node.js 下載會做 SHA-256 驗證；即夢官方安裝器目前沒有由本專案維護的固定 checksum，因此每次由官方 HTTPS 網址取得。
- 建議在執行前先閱讀 `install.sh` 與 `THIRD_PARTY.md`。

## 官方資料

- [HyperFrames CLI](https://hyperframes.heygen.com/packages/cli)
- [HyperFrames GitHub](https://github.com/heygen-com/hyperframes)
- [Node.js 下載與驗證](https://nodejs.org/en/download)
- [Homebrew node@22](https://formulae.brew.sh/formula/node@22)
- [Homebrew FFmpeg](https://formulae.brew.sh/formula/ffmpeg)

## 支援範圍

目前自動安裝器已針對 macOS／Linux 設計。Windows 可依即夢官方 PowerShell／CMD 安裝命令處理；Windows 的 Node.js、FFmpeg 與 HyperFrames 整合腳本尚未納入這個版本，避免提供未實機驗證的一鍵流程。
