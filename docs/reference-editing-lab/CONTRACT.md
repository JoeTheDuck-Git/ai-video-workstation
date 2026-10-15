# v0.1-draft 資料契約

以 `schemas/bundle.schema.json` 的 `$defs` 查看 Media、Evidence、Annotation、Profile、Rule、Plan、Clip、Effect 定義。`contracts.py` 為唯一模型來源；修改後用 `--schema` 重新產生 schema。這版採單一 bundle 方便小型試驗；正式資料儲存／migration 尚未實作。

## 時間與來源

每個 media 以 `timebase = numerator / denominator` 秒／tick 記錄來源時間；interval 一律為 `[start_tick,end_tick)`。fps 是另一個有理數，不等於 timebase。例：30000/1001 fps 的素材、timebase=1/30000 秒時，一幀是1001 ticks，60幀是60060 ticks=2.002秒。

timeline 有自己的 timebase。常速 clip 必須滿足：
`(source_out-source_in) × media_timebase / speed = timeline_duration × timeline_timebase`。
使用 Fraction 精確驗證，不把29.97當30，不混用 render elapsed。可變幀率須從 ffprobe/frame PTS 對應來源 ticks；此驗證器不產生／驗證完整 VFR frame map，也不執行採樣或補幀。跨幀率轉接、speed ramp、freeze、reverse 目前不在可執行合約內；列為 manual/unresolved。音訊使用同樣明確 timebase 的區間，不能把音訊樣本號當影片幀號。

Media 必含實測來源紀錄、版本、SHA256、尺寸、fps、codec、音軌、權利與隱私狀態。正式資料 `provenance=probed` 要能回查原 ffprobe JSON；驗證器只檢查結構，不會讀檔核實 checksum 或 probe 真偽。模擬資料必用 synthetic URI/provenance，不能當作實際模型結果或素材存在的證明。

## 證據與知識狀態

Annotation category 包含 shot、narrative-role、caption、transition、speed、crop、sound、effect；每項有描述、來源區間、evidence IDs、confidence、approval。

- observed：能從列出的畫面／聲音直接支持；例如文字位置、可見推近、可聽鼓點。
- inferred：例如「這個插入鏡頭可能承接前句論點」、看似速度改變。數值是主觀置信分數，不是已校準機率。
- unknown：沒證據或無法辨認；confidence=null。

MP4 是平面輸出，無法可靠還原原始外掛名、圖層、關鍵幀、原始速度、遮罩與調色節點。不要把視覺相似當作內部實作證據。程式可檢查引用與區間是否相交，不能判斷一張圖是否真的支持一句結論；仍需人審。

## 審核與風格版本

approval 帶狀態、reviewer、reviewed_at；生產資料須記真實人審者與 ISO8601 時间，不得由 agent 冒填。rules 連回 annotation，列 scope/exceptions；profile pin version/parent_version。敘事 brief 與風格規則分開，不能把「這支片在3秒切鏡」推廣成所有影片硬規則。profiles 變更需建立新版本、重新審查受影響 plans。

`draft` 可帶待決內容；`approved` 僅在 profile、用到的 rules、plan 已審核、權利已解決且無 unresolved 時有效。這是資料一致性，不代表執行／上傳授權。任何 synthetic bundle 永遠不進真實渲染。此套件沒有執行器。

## 中立剪輯計畫與不支援能力

Clip 包含來源 ticks、目標 ticks、track、常速比例、敘事角色、配對理由、來源證據、規則引用與特效要求。同一 track 不允許重疊；不同 track 可重疊，但混音／轉場仍需已驗證 adapter 支持。空段、J/L cut、音訊連結、巢狀片段與跨鏡轉場需要下一版明確契約，不能靠隱含 editor 行為補足。

Effect support 分 verified/candidate/manual/unsupported。verified 需 implementation/version 與 validation_evidence；沒有實作時即使叫作「淡入」也不自動認定可渲染。fallback 需人審，不得靜默忽略。parameters 是草案開放物件，現有驗證器不驗證各引擎參數；不執行其中代碼或路徑。

暫不輸出剪映工程。Resolve、OTIO 只列待驗候選。任何實際轉接均需以原片 FPS/timebase、trim、音畫同步、字型／特效缺漏與重連素材測試後才宣稱支援。
