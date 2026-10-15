# 參考成片導引粗剪：今晚討論草案

狀態：2026-10-12，僅準備包。沒有分析使用者影片、訓練模型、建立批次剪輯服務或更動既有 UI。全部 fixtures 都是 synthetic，沒有真影片與假稱的 AI 分析成果。

要驗證的流程：**自有參考成片 → 可回查拆解表 → 人審風格規則 → 新素材配對 → 中立粗剪計畫 → 經核准的轉接與渲染 → QC／人工修改時間評估**。

## 這次準備了什麼

- `../../skills/reference-edit-analyzer/SKILL.md`：拆解可見／可聽證據，不還原不存在的工程資訊。
- `../../skills/editing-style-profile/SKILL.md`：把可重用規則與單片敘事分開，人審、版本化。
- `../../skills/reference-guided-cut-planner/SKILL.md`：配對留出新素材，輸出可審核的中立剪輯計畫。
- `CONTRACT.md`、`contracts.py`、`schemas/bundle.schema.json`：Pydantic 2 草案模型、JSON Schema，以及跨欄位語義驗證。
- `fixtures/synthetic-bundle.json`、`tests/test_contracts.py`：不讀取任何真影片的模擬案例與負面測試。
- `REUSE.md`：既有 Skill 邊界與 QC 擴充方式。
- `TONIGHT.md`：今晚實驗輸入、檢查表、評估指標。
- `platform-guidelines/`：官方推薦資格、自然流量建議、廣告案例、實驗假設分開保存；已整合主線查核的6份官方來源，區分自然流量、推薦資格與廣告案例；沒有算法保證。

## 可直接執行的範圍

從新副本根目錄執行：
```sh
.venv/bin/python docs/reference-editing-lab/contracts.py docs/reference-editing-lab/fixtures/synthetic-bundle.json
.venv/bin/python -m unittest discover -s docs/reference-editing-lab/tests -v
```
它只驗證 JSON，沒有影片分析、剪輯、上傳或檔案搬移。使用現有 Pydantic，不安裝新依賴。JSON Schema 本身只描述結構；引用、時長換算與審核條件由 Python 驗證器執行。

三個 Skill 放在此專案的 `skills/`，未全域安裝，未保證 Codex 的自動探索已註冊；可在本專案直接指定 SKILL.md 試用。它們是操作規格，不是已連上模型的功能按鈕。

## 尚未實作

鏡頭切分／OCR／ASR／音效辨識服務、視覺模型評估、批次工作佇列、審核 UI、可渲染 timeline adapter、Resolve／OTIO 匯入驗證與剪映匯出均未實作。使用者提供素材後，第一輪先人工輔助拆解和驗證契約，才決定值得自動化的部分。

## Student Kit + 官方剪輯規則更新

新入口：[WORKSTATION_PROMPTS.md](../../WORKSTATION_PROMPTS.md)。版本、授權與衝突：[INTEGRATION.md](INTEGRATION.md)。實際剪輯前讀 [EDITING_PROMPT.md](EDITING_PROMPT.md)；本包仍未實作渲染 adapter，未證明中文口播剪輯品質。
