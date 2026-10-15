> 本獨立副本的參考剪輯／口播粗剪入口：[WORKSTATION_PROMPTS.md](WORKSTATION_PROMPTS.md)。上游安裝說明不代表本次允許安裝或更新。

# AI Video Workstation Bootstrap

把本機 AI 影片工作環境用一個可重複執行的安裝流程建立起來。這個套件目前以 macOS／Linux 為主，會安裝或設定：

- Node.js 22（從 Node.js 官方發行檔下載並驗證 SHA-256）
- FFmpeg／FFprobe（優先沿用既有安裝，缺少時使用系統套件管理器）
- HyperFrames CLI 與核心 Skills
- 獨立的 `canvas-video` 確定性 Canvas／Three.js renderer
- `canvas-video-pipeline` 與 `video-delivery-qc` Skills
- 預設內建 `footage-sifter`、`caption-doctor` 與 `subtitle-translator`
- Canvas Skill 內建確定性的 B-roll 效果 API，
  並隨附重新命名為 **Tacky Templates** 的 10 種動態風格、31 個 HTML 模板與
  31 效果展示頁

執行環境與 HyperFrames 會在安裝時從官方來源取得。登入憑證、Cookie、API Key、生成素材與影片不會進入 Git。
基本安裝不會安裝、登入或驗證任何生成式媒體供應商；可直接使用本機素材、授權素材庫，或另外安裝使用者自行選擇的生成工具。

## 快速安裝

```bash
git clone https://github.com/JoeTheDuck-Git/ai-video-workstation.git
cd ai-video-workstation
./install.sh
```

安裝器預設把九個內建 Skill 同時複製到 `~/.codex/skills/` 與
`~/.claude/skills/`，並在
`~/.local/share/ai-video-workstation/python-venv/` 建立隔離 Python 環境來安裝
OpenCC、jieba、NumPy、Matplotlib、Pillow 與 Pydantic 2，不會修改系統 Python。

若要一次安裝 HyperFrames 發布的完整 Skill 集合：

```bash
./install.sh --all-hyperframes-skills
```

若只使用其中一個 AI 工具：

```bash
./install.sh --codex-only
./install.sh --claude-only
```

若需要 HyperFrames／HeyGen 的選配雲端功能，可另外登入：

```bash
./scripts/login.sh
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

### 媒體來源

本安裝包不綁定生成式媒體供應商，也不執行供應商登入或額度驗證。可以使用相機素材、授權素材庫、既有成品，或由使用者明確指定並另行安裝的生成工具。Canvas renderer 只讀取已經完成並存放在本機專案中的媒體。

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

完整動態版型收在 `canvas-video-pipeline/assets/tacky-templates/`，安裝時會為每個已選擇的
AI 工具建立隔離的模板 renderer；不與 Canvas 或 HyperFrames 共用 `node_modules`。
`canvas-video` 會自動解析 Codex 或 Claude Code 的 Skill 位置：

```bash
canvas-video tacky list
canvas-video tacky gallery
canvas-video tacky copy-template vox ./title-card.html
canvas-video tacky render-template ./title-card.html ./title-card.mp4 --dur=8 --ffmpeg=ffmpeg
```

`assets/tacky-scenes/` 只保留 31 項通用動效展示，用於挑選並重建當前故事需要的
動效；不把展示頁當成完成場景直接交付。

### 社群影片 QC Skill

`skills/video-delivery-qc` 是本套件隨附的 Skill。它會檢查影片解碼、黑畫面／凍結／靜音、容器與編碼、畫面比例、字幕時間、語音同步抽查提示及社群交付音量等項目。

範例：

```bash
# Codex 安裝使用 ~/.codex/skills；Claude Code 安裝改用 ~/.claude/skills
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
4. `canvas-video` renderer 與 Playwright Chromium 是否可執行。
5. 指定的 Codex／Claude Code 端是否都已安裝九個內建 Skills。
6. OpenCC、jieba、Tacky Templates 清單與隔離 renderer 是否完整。

## 更新

重新執行安裝器即可更新 Node.js 22、HyperFrames、HyperFrames Skills、Canvas runtime 與 QC Skill：

```bash
./install.sh
```

## 安全與隱私

- 不要把 `~/.heygen`、任何供應商登入資料、Cookie、API Key 或 `.env` 提交到 Git。
- 安裝器不會讀取或輸出登入憑證。
- Node.js 下載會做 SHA-256 驗證。
- 建議在執行前先閱讀 `install.sh` 與 `THIRD_PARTY.md`。

## 官方資料

- [HyperFrames CLI](https://hyperframes.heygen.com/packages/cli)
- [HyperFrames GitHub](https://github.com/heygen-com/hyperframes)
- [Node.js 下載與驗證](https://nodejs.org/en/download)
- [Homebrew node@22](https://formulae.brew.sh/formula/node@22)
- [Homebrew FFmpeg](https://formulae.brew.sh/formula/ffmpeg)

## 支援範圍

本倉庫的自動安裝器針對 macOS／Linux；Windows 使用獨立的 `ai-video-workstation-windows` 倉庫。

## Talking-head editing skills

Start with [WORKSTATION_PROMPTS.md](WORKSTATION_PROMPTS.md). The workflow asks for the duration limit, optional transcript/timeline preview, and export resolution including **480p (草稿)**. The checked-in protected phrases and pacing preferences belong to this project user; replace them for another speaker.

The source review, cut planner, preview renderer and delivery gate are available under `skills/spoken-edit-review/` and `scripts/lab/`. They require Python 3.10+, locally installed FFmpeg/ffprobe, and host-provided independent review. Mouth-noise analysis additionally uses NumPy and Matplotlib. No ASR service or listening capability is installed by these scripts. Evidence-only review permits a labelled preview, never a final listening pass.

Run the portable checks with:

```sh
python3 -m unittest discover -s skills/spoken-edit-review/tests -v
python3 -m unittest discover -s docs/reference-editing-lab/tests -v
```

Private-media regression cases are explicitly skipped when their local artifacts are absent. The optional historical map fixture belongs at `productions/private-regression/planned-preview.json.map.json`; it must have valid local evidence bindings. Public tests do not establish audible quality. Historical case references describe lessons, not bundled media or reusable cut points.

## 更新剪輯與字幕 Skills（Codex）

首次安裝：先閱讀本檔與安裝腳本，再執行 `./install.sh --codex-only`。
已有可用執行環境，只更新內建規則與工具：

```sh
git status --short
# 僅在工作樹乾淨且目前為 main 時：
git pull --ff-only origin main
./install.sh --codex-only --skills-only
```

若有本機修改，先另存備份並處理衝突，不使用 reset --hard。安裝器依 `skills-manifest.json` 安裝九個 Skill，包含 caption-doctor、reference-guided-cut-planner、spoken-edit-review 與 video-delivery-qc，以及它們所需的 scripts/lab 和通用契約。更新時把原有同名 Skill 完整移至該次快照的 backups；自訂規則不自動合併，可從備份選擇性恢復。無關 Skill 不變。

每次安裝建立獨立檔案快照於 `~/.local/share/ai-video-workstation/skill-releases/`。各已安裝 Skill 的 `runtime-root.json` 記錄完整工具根目錄及來源commit；即使移動下載repo，工具仍可使用。使用者固定句清單預設為空，請在自己的專案設定。不要把素材、密鑰或個人profile寫入安裝快照。

`--skills-only` 不下載依賴、不更新Node/FFmpeg/HyperFrames、不執行影片渲染。它需要現有Python3；缺執行依賴時改用完整安裝。完整環境檢查：`./scripts/verify.sh --codex-only`。更新後開新Codex對話以重新發現Skills。

短句字幕與可配置附件大小流程見 `WORKSTATION_PROMPTS.md`。技術通過、實際視覺檢查、實際聽辨分開紀錄；整體正面回饋不自動關閉個別待核對專名或音訊問題。

開發驗證：`.github/workflows/skills.yml` 列出測試命令。安裝測試在暫存目錄實際執行 `--codex-only --skills-only`，驗證九個Skill、備份與完整工具快照；不修改實際使用者安裝。私有影片回歸未分發，公開測試使用合成媒體。

### Native Windows: update the same nine Skills

With an existing Python 3.11+ environment, use native PowerShell from this checkout:

```powershell
.\install-skills.ps1
# Optional isolated destination / explicit interpreter:
.\install-skills.ps1 -SkillsRoot 'C:\My Projects\Codex skills' -StateDir 'C:\My Projects\Skill snapshots' -Python 'C:\Python311\python.exe'
```

This is a **Skills-only** updater, not a full Windows workstation bootstrap. It uses
`skills-manifest.json`, the same nine Skills and independent runtime snapshot as the
Mac installer, backing up replaced Skills under the new snapshot's `backups`.
Restore custom rules selectively; do not copy old bundled tools over new ones.
Open a new Codex conversation after updating. Python, FFmpeg/ffprobe and the Python
dependencies must already be available. The separate Windows workstation installer
has its own release lifecycle; it is not evidence that its bundled Skills match main.
For native Python commands use `python -X utf8` to read Unicode project data consistently.

Preview preparation now accepts required `--project-root PATH`: `--output-dir` must
resolve to a new descendant of that project, including through symlinks/junctions.
No existing output directory is overwritten. Use a user project outside the installed
runtime snapshot. Existing prepared jobs must be prepared again after updating tools.

CI runs the test suites on standard Ubuntu, native Windows and macOS runners. It uses
public generated test patterns and tones, installs into paths containing spaces and
Chinese text, and records runtime versions, H264/AAC 480p specifications, full decode,
A/V timing, size and caption formatting in the job summary. This does not certify
human lip-sync/listening, private footage, every friend's PC, or the full HyperFrames stack.
