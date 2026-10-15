> GitHub package note: this directory retains historical integration notes. Local media, transcripts, review receipts, environment/runtime installations and `vendor/hyperframes-skills` are not distributed. Only the upstream source index in `vendor/editing-rules/README.md` is distributed; the vendor archive itself is omitted. It does not authorize installation or execution.

# 整合、衝突與版本相容性

> 2026-10-13：使用者確認三分鐘口播原則授權。EDITING_PROMPT.md 中的三分鐘模式取代先前「每切點一律人審」要求；一般剪輯直接做第一版，只對語義或證據等例外詢問。下列歷史整合描述不覆蓋這次授權。runtime／schema／adapter 未因此更新。

此次只修改 prompt/docs/routing/tests。上游封存逐檔 SHA256 見 ../../vendor/editing-rules/manifest.json；原文未改。既有 vendor/hyperframes-skills 不被新版本覆蓋。

| 上游 | Commit | 授權／版本 |
|---|---|---|
| [Student Kit](https://github.com/nateherkai/hyperframes-student-kit/tree/0d30152a82b9ceb93cfdd9bdbf46f0d5ab3cde86) | 0d30152a82b9ceb93cfdd9bdbf46f0d5ab3cde86 | MIT；package 2.0.0，依賴 HyperFrames 0.7.109；另保留 THIRD_PARTY_NOTICES 與 licenses |
| [官方 HyperFrames](https://github.com/heygen-com/hyperframes/tree/86521b94f592bcf0ca86aba63068893cf658af16) | 86521b94f592bcf0ca86aba63068893cf658af16 | Apache-2.0；CLI 0.8.149 |
| 本機 runtime | runtime/hyperframes/package.json 與現有 node_modules | 0.8.146，未升級 |

## 去重與覆蓋順序

使用者授權範圍 → 本地 EDITING_PROMPT → 已安裝版本契約 → 相容的上游參考。Student canonical .claude/skills 與 generated .agents/skills 重複，只保留前者；新上游文字在 vendor/editing-rules，原本安裝對應規則在 vendor/hyperframes-skills，二者是版本對照而非同時註冊兩套 Skill。沒有移植上游 AGENTS、配置或 install 流程。

## 衝突處理

| 差異 | 本地採用 |
|---|---|
| 官方 freshness/usage/auth/init/update；Student Scribe/API 預設 | 此輪不執行；缺依賴明確報阻擋，不呼叫 API、不取金鑰 |
| Student 多階段 ffmpeg 去停頓→去失誤，各自 retime | 僅借候選判斷，合成回原始素材的單一 map；人審後再交待實作 adapter |
| talking-head-recut 名稱容易被誤解為剪接 | 保持原片只加 overlay 才使用；trim/splice/reorder → general-video + core |
| Student 分離音軌；官方 clip 自帶音訊 | 擇一且共用 map；保留附帶聲音或明確 muted+獨立 audio，不能雙重播放 |
| 官方容許同軌 CSS 次序 overlap | 本地中立 validator 第一版拒絕同軌 overlap；非 framework 限制 |
| Student B-roll 不重複、開場三秒、剪除比例、節奏 | 作為有例外的創作建議；來源重用記錄理由，不轉為普遍硬規則或流量保證 |
| Student synthetic smoke tests | 只可證明腳本示例／契約，不證明中文吞字、重錄語義或成片品質 |
| footage-sifter FCPXML 分數／混合 FPS | prompt 阻擋未驗證 exporter；此次不修匯出器 |

## 0.8.146 相容性界線

已讀本機既有 core/references/data-attributes.md：data-start、data-media-start、duration 自然推導、half-open 可見區間及 linked media 同步契約已有文件支援。新官方 creator-editing-recipes 明確示範 source consumed = timeline duration × rate，來源 offset 不等於目的時間，不能虛構 source-end。

這是文件層級比對，不是對 0.8.149 全功能的 runtime 驗證。未跑本次新來源 trim／retime／J-L／VFR 渲染。採用每一 recipe 前仍需以本機 0.8.146 做最小實測（分數 FPS、source offset、rate、音畫同步、邊界）。未知功能留 unresolved；禁止為符合新文件而自動升級。Student 0.7.109 腳本亦未宣告可直接跨版運行。

## 審查與未執行

逐檔原文封存與雜湊驗證；人工重點閱讀四個剪輯 Skill、quality gates、general-video、core recipes、時間欄位與相關路由。這不是所有第三方腳本的安全認證。封存的 scripts 為參考，沒有執行。官方 clone checkout 因缺 Git LFS 未完成，文字以 pinned Git blobs 擷取，未安裝 LFS，未取大型媒體。

未安裝／升級 runtime 或套件、未執行第三方 bootstrap／腳本、未配置 key／ASR／VAD／alignment、未外部生成、未 push／部署、未改 UI／原服務、未加入 CapCut。Library 僅保存本次明確授權交付文件包。

## 交付檔案

根目錄 AGENTS.md、WORKSTATION_PROMPTS.md、README.md 路由；三個 skills/reference-*/ 與 editing-style-profile/SKILL.md；本資料夾 EDITING_PROMPT.md、INTEGRATION.md、TONIGHT.md、README.md、tests/test_upstream_archive.py；vendor/editing-rules 原文、授權、manifest。

保護檢查、測試結果見 integration-verification.json 與 integration-tests.txt。240 檔 baseline 保持原值，原專案另以既有 100 檔 hash verifier 檢查。新入口是專案 agent 路由，不代表全域 Skill 安裝或 UI 功能上線。
