# 自架 AI 影片工作室 PRD（草稿 v0.1）

狀態：草稿，待討論。標「假設」的項目尚未與使用者確認。
參考對象：phasyn/phasyn-studio（僅讀過 README 與安裝文件，未讀原始碼，細節為推測）。
路線：A（本地 GPU 自架）。

## 1. 目標

在使用者自己的 GPU 機器上，提供「鏡頭生成 → 多版挑選 → 時間軸剪輯 → 匯出」的一站式短片工具，並與本專案既有的剪輯與交付品質檢查流程（EDL、字幕、export-choices）銜接。

不是目標：雲端服務、多人協作、帳號系統、商用 SaaS。

## 2. 使用者與情境（假設）

- 主要使用者：單一創作者，在自己的電腦或區網內使用。
- 典型任務：產出 15–60 秒短片，內容包含 AI 生成鏡頭、程式化動畫（資訊圖表、字卡、轉場）、既有素材。
- 安全模型：只綁 127.0.0.1，無登入。

## 3. 核心概念

| 概念 | 說明 |
|---|---|
| Project | 一支片，含設定（比例、fps、解析度） |
| Shot | 一個鏡頭，有型別與參數 |
| Take | Shot 的一次產出（可有多版，擇一採用） |
| Clip | 時間軸上的片段，引用某個 Take 或匯入素材 |
| Job | 非同步工作（生成、渲染、匯出），有進度、取消、重試 |

### Shot 型別

1. **generative**：提示詞加參考圖／聲音，由 GPU 上的擴散模型生成。
2. **programmatic**：由 LLM 撰寫的程式碼動畫（HTML/CSS/SVG/Canvas 或 React 動畫），以無頭瀏覽器逐幀擷取後交給 FFmpeg。
3. **imported**：使用者自己的影片、圖片、音訊。

> programmatic 型別對應「用 LLM 寫動畫」的用法：文字、版面、數據圖表精確可控，可重複渲染、可局部修改，並且不佔用 GPU。generative 負責擴散模型擅長的寫實或風格化畫面。兩者並存是本設計的重點。

## 4. 功能需求

### MVP（M1–M3）
- FR1 專案與鏡頭管理（CRUD、排序）。
- FR2 Render Shot：產生多個 Take 並排比較，選定一版。
- FR3 Job 佇列：進度、取消、失敗重試、日誌。
- FR4 時間軸：排列、修剪、基本轉場、文字、音樂軌。
- FR5 匯出：選解析度（含 480p 草稿）、fps、編碼、音訊；沿用 `skills/video-delivery-qc/references/export-choices.md`。
- FR6 programmatic Shot：以提示詞請 LLM 產生動畫原始碼，預覽、編輯、重新渲染。
- FR7 Node 設定檢查（類似 doctor）：GPU、驅動、FFmpeg、模型路徑。

### 之後
- 字幕整合（沿用 caption-doctor 的標點選項與詞錨點規則）。
- 口語剪輯整合（EDL 綁定原片）。
- 剪映／CapCut 草稿包（目前兩者 exporter 均未支援，不在 MVP）。
- 多 GPU／多 Node。

## 5. 架構

```
瀏覽器 ── Controller（API、專案資料庫、Job 佇列）
              │
              ├── Node（GPU）：generative 元件（TE → DiT → Decode）
              ├── Renderer（CPU）：programmatic 動畫，無頭瀏覽器逐幀擷取
              └── Media：FFmpeg／ffprobe（轉碼、時間軸合成、匯出）
```

- 儲存：SQLite 加專案目錄（媒體檔不進資料庫）。
- Provider 介面：`generate(params) -> media`，Node 以此抽象實作；之後可換模型或接雲端，上層不變。
- 輸出位置：遵守 `.local/output-location.json` 與 `scripts/lab/output-location.py` 的既有規則。
- 原始素材不修改；匯出由原檔回套，不放大代理片。

## 6. 模型與授權風險

- 影片與圖片模型各有授權，可能限制地區或商用。參考專案提到的限制（MiniMax-H3 的地區限制、Qwen-Image 的非商業）僅來自其 README 摘要，**使用前須讀原文**。
- 模型選型是待決問題，取決於 GPU 與用途（見第 9 節）。
- 程式碼可參考架構，但不複製；若引用須遵守 Apache-2.0。

## 7. 非功能需求

- 單機單 GPU 可跑完整流程。
- 長工作可中斷與續跑。
- 每個 Take 記錄：提示詞、種子、模型版本、參數，可重現。
- 診斷資訊足夠定位失敗（GPU 記憶體不足、模型缺失）。

## 8. 里程碑

| 階段 | 內容 | 驗收 |
|---|---|---|
| M0 | 確認 GPU 與模型，單鏡頭手動跑通 | 命令列生成一段影片 |
| M1 | Controller、資料模型、Job 佇列、imported Shot | 能匯入素材並匯出 |
| M2 | programmatic Shot（LLM → 程式碼 → 渲染） | 一句話生成 5 秒動畫並可改 |
| M3 | generative Shot 接 Node，多 Take 比較 | 同鏡頭 3 個 Take 可選 |
| M4 | 時間軸與匯出選項 | 完整短片從提示詞到成檔 |

## 9. 待決問題

1. GPU 型號與 VRAM？決定能用哪些模型與解析度。
2. 主要用途：短影音、說明動畫、還是配合現有口語剪輯的 B-roll？
3. LLM 從哪裡來：呼叫雲端 API，還是本地模型？（影響 programmatic Shot 的品質與離線需求。）
4. 是否需要生成音訊（配音、音效）？
5. 作業系統：Linux 或 Windows／macOS？（macOS 沒有 CUDA，路線 A 不適用。）
