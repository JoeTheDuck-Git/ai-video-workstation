# 本地剪輯契約：成片目標 → 內容取捨 → 單一時間映射 → 粗剪 QC

## 讀取路由

來源均在 ../../vendor/editing-rules/：
- student-kit/.claude/skills/edit-video/SKILL.md：流程入口。
- student-kit/.claude/skills/cut-silences/SKILL.md：停頓候選，不是語義或 VAD 真值。
- student-kit/.claude/skills/cut-mistakes/SKILL.md：重複／重錄候選與上下文。
- student-kit/.claude/skills/short-form-edit/SKILL.md 及 references/：參考分析、敘事、品質檢查。
- hyperframes-official/skills/general-video/SKILL.md；hyperframes-core/SKILL.md、references/tracks-and-clips.md、creator-editing-recipes.md、data-attributes.md：實際 source trim/splice/reorder 契約。
按當前階段讀取，不一次執行所有上游步驟。相依文件缺失時列明阻擋；封存腳本僅供閱讀。版本差異見 INTEGRATION.md。

## 三分鐘口播模式（2026-10-13 使用者確認）

2026-10-14 更新：每個新任務在內容選段前先詢問 3 分鐘內／5 分鐘內／8 分鐘內／自訂片長；以本次明確選擇為準，取代自動套用三分鐘的預設。完整規則及聊天問話框流程見 WORKSTATION_PROMPTS.md。未回答時可完成轉錄與盤點，但內容預算只作暫定，不開始渲染。以下 170–178 秒／180 秒規則只適用於已選三分鐘的任務；其他時長另訂內容預算，不把較短來源補長。

2026-10-14 增加可選文字審閱：渲染前按 WORKSTATION_PROMPTS.md 的「可選逐字稿預覽」提供聊天選項框，讓使用者選先看預計保留逐字稿與來源／成片時間軸，或直接渲染。已有本任務明確選擇就沿用。文字審閱路徑先交具體草稿，使用者要求繼續後才渲染；直接渲染路徑仍依下列原則授權，不重問一般切點。文字草稿與渲染共用同一 source map，時間標為預估，改稿後更新版本；文字通過不是音畫品質通過。

本使用者的科技新聞口播試剪，預設目標 170–178 秒（2:50–2:58），硬上限 180 秒，包含片頭、片尾與停留時間。使用者另指定片長或任務時，以新指令為準；不把本模式套用到所有影片。

先建立核心敘事與各段時間預算，再選實際 source segment IDs；不要先把原稿全部保留、只清口誤，最後才嘗試壓長度。Polymarket 範例主線為「平台做什麼 → 爭議 → 雙方立場 → 使用者差別」，其他主題依內容另訂主線，不套用該事實或次序。

刪除優先順序：口誤／未完成重錄／無意義長停頓 → 不同句子重複同一意思 → 重複鋪陳及過場 → 次要個人補述 → 多次訂閱或分享 CTA。保留核心結論、必要例子與推理連接。保護否定、數字口徑、單位、型號、資格、條件與歸因。若一項數據的限定太長，保留精簡且有原聲證據的限定，或整段連同數據刪除；不能只留容易誤解的數字，不能憑空拼出未說過的話。

結尾優先保留一句有觀點的結論或問題，CTA 視時間保留一次；若改變原意才詢問。先做內容精簡，再縮自然停頓；必要時才適度調速，記錄實際倍率、變速區間與可懂度檢查，不預設全片 1.5 倍，也不能把長度差全部當刪除量。輸出前以實際媒體時長驗證 ≤180 秒；超時先再刪次要內容，不靠截斷尾句達標。無法在保留必要條件下達標時，提出具體取捨再詢問。

參考 https://www.youtube.com/shorts/80QdjHoi1cw 的精簡程度；對照證據見 ../../productions/dji-0043-pilot/final-reference/EDIT-COMPARISON.md。現有證據是原片 ASR、final 畫面及英文自動字幕，未完成逐幀來源映射或變速量測，不能宣稱已還原成片 EDL。不複製該片未保留數字口徑的取捨。本輪只更新 prompt，不因此啟動影片渲染。

使用者已授權：在上述規則內直接製作第一版可播放粗剪，不逐切點詢問；先不加特效、B-roll 或音樂。權限適用於使用者實際指定的試剪素材，並非自行處理其他影片的授權。只有可能改變原意、辨識／切點證據不清、重要資訊矛盾或必要內容與時長衝突時才詢問；可確定部分持續完成。

## 證據門檻

先取得實際素材、checksum／版本、ffprobe metadata、音軌、原始逐字稿與 word timing 的來源／工具版本／語言／時間基準／信心與抽查紀錄。語音剪輯缺逐字或時間證據時，只可盤點、提出補證清單，不可輸出可執行刪字切點。純無聲畫面可依幀證據規劃，但不能假稱有 speech evidence。ASR、VAD、forced alignment 是不同證據；silencedetect 不是 VAD，字數比例 reflow 不是逐字對齊。沒有跑過就不得標為已完成或已驗證。

每段指定 stable segment ID、source ID/hash/version、原始 half-open [in,out) tick 或 PTS、逐字文字、前後語境與證據連結。可提出人工輔助草案，不能把 synthetic fixture 當真素材。

## 語義選段與授權紀錄

AI 以 segment IDs 記錄 keep/delete/reorder、理由、替代段與風險；不能自由發明時間戳或直接剪原素材。保護否定詞、条件、數字、單位、產品型號和因果次序。重錄需比較各 take 的完整語義與前後語境，不一律保留最後一遍；刻意強調的重複不等於口吃。吞字、尾音、呼吸與中文斷句不確定時保留並標待審。無需刪除也是有效結論；不設硬性刪除比例。

三分鐘口播模式採使用者已確認的原則授權：一般剪輯不再要求逐項 keep/change/reject；AI 決策記為 policy-authorized，記錄授權來源「2026-10-13 對話確認三分鐘 prompt」、適用範圍、source/profile/plan 版本及理由，不虛構人類看過每一切點。明確要求先看計畫、或其他尚未授權的模式，才走逐項人審。素材、逐字稿、切點或規則改版會使受影響預覽與驗證失效，應重新驗證；仍在既有原則授權內不需重問，超出範圍才詢問。不將 fixture approval 當人審。

## 確定性 source → timeline map

符合已記錄原則授權的選段，或經逐項人審的選段，才交確定性 adapter 編譯；本次尚未實作 adapter。原則授權不是媒體驗證通過：現有 schema 若只容納逐項人審，不偽造 approval 欄位，以 draft 計畫加獨立授權紀錄保存；轉接器仍需驗證後才能執行。保持一份原始來源到成片的映射，所有字幕、效果、音訊引用同一 map version/hash。若先去停頓再去失誤，必須把兩階段映射合成回原始 source；不得把 silence-retimed 秒數誤套原片，也不得另維護字幕時間軸。

CFR 保存 rational FPS（例如 30000/1001）及整數 frame index；VFR 保存實際 PTS/timebase，不能 frame ÷ rounded FPS。統一 half-open 範圍，記錄非整幀換算策略，不用浮點四捨五入重複累積。data-start 是目的時間；data-media-start 是來源 offset；data-duration 是時間軸時長；source consumed = timeline duration × playback rate。自然時長 = remaining source / rate。按已安裝版本核對 data-playback-rate，不能臆造 source-end 欄位。

每次驗證 source bounds、負／零長度、重複 clip IDs、timeline bounds、意外 gaps/overlaps、來源重用及理由、逐字完整性、音畫連續與同步。來源重用須有記錄，人審例外可以允許；本地中立 validator 目前拒絕同軌 overlap，比 HyperFrames 更窄。跨軌 transition 不能用此限制冒充 framework 不支援。現有 JSON validator 不代表已驗證媒體、VFR 或轉接器。

## 粗剪先行，效果後置

先做無裝飾 rough cut，對每一切點提供原片／輸出前後的 frame、PTS、音訊時間窗與實際聽辨紀錄；檢查缺字、多字、吞音、音畫偏移、黑幀／重幀與敘事連續。至少記錄預期與實測 source in/out、目的 frame、偏差及 pass/fail。沒有量測或無法聽音就記未驗證，不能宣稱通過。語音語義與視覺證據缺失時阻擋最終通過。

粗剪人審通過後才加入字幕、B-roll、動效、音樂。效果支援須附 adapter/runtime 版本與測試證據；未知效果列人工處理或明確替代，不能默默省略。特效音／音樂呼叫不在本次授權內。

附帶音訊用 data-has-audio=true；若採分離音訊（J/L cut、替換、混音）則視頻 muted 並共用 map，避免雙重播放。輸出全片解碼、逐切點視聽驗證與規格核對後才可宣告剪輯驗證通過。

## 邊界

實際剪接走 general-video + hyperframes-core；talking-head-recut 僅連續原片加 overlay。footage-sifter 的 FCPXML 匯出因分數 FPS／混合 FPS 精度尚未驗證而停用此路由；不執行 exporter、不宣稱 Resolve/FCP/OTIO 已可用。可用其唯讀盤點，但稀疏 contact sheet 不是精準切點。

不更動 runtime、金鑰、API、既有 UI；不執行上游腳本、安裝／更新命令、登入、下載模型、付費生成或發佈。需要這些能力時報出具體缺項，完成其餘有證據的準備工作。本版沒有 ASR/VAD/forced-align 服務、auto editor、語音品質保證或 CapCut plugin。

## 獨立 sub-agent 與交付門檻

口播輸出後必須實際啟動不同的 review sub-agent，依[可執行審查流程](../../skills/spoken-edit-review/references/independent-review.md)交付綁定素材、成片、EDL 與規則版本的證據包、候選問題清單及審查紀錄。審查包含所有保留片段內部、接點與片尾；不是只重讀 ASR。必須保存真正的派工與完成回覆，再執行 review_gate.py。技術通過不能替代內容通過；無音訊理解、覆蓋不足或問題未解只准標為待審草稿。正常強調／換氣不得按閾值自動刪除。改剪後舊審查失效。沒有 sub-agent 能力時明確回報，不能由剪輯者假扮獨立 reviewer。

## 原片初剪前重講複查

產生可執行剪點前，必跑 source_review.py prepare → 新獨立 sub-agent 先盲審原片、後對照候選 → source_review.py authorize → plan-spoken-cut.py。完整規範見 skills/spoken-edit-review/references/source-review.md（自專案根目錄）。相似度 >=0.90 僅文字優先標記，不是錯誤機率，不自動刪除；低分與空候選不代表通過。原始逐字稿保留口誤、半句、詞級時間與可信度；正式模式無聽辨仍 needs_review，不能生成正式批准剪點；使用者授權的 preview 模式可依獨立 Codex 證據審查產生待審候選 map。剪後交付 gate 重新核對前置複查綁定。

## 待審預覽與正式成片分流

使用者授權 Codex 輔助審查的預覽時，依 [preview 模式規範](../../skills/spoken-edit-review/references/preview-mode.md) 執行 source authorization、planner 與 delivery 的 `--mode preview`。獨立 reviewer 全段核對轉錄、波形與候選變更，不假稱聽過音訊；輸出固定標示 `actual_audio_review=false`、`content_status=needs_review`、`final_pass=false`，保留未解項目與前後剪點證據。輸出後仍須技術 QC 和獨立證據複查。正式模式保留實際聽辨及完整雜湊綁定，不能使用 preview map 通過 final。暫不渲染的指示優先；解析度待定時只準備時間軸與證據。
