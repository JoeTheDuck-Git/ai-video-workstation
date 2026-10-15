# AI Video Workstation — 剪輯入口

先讀 docs/reference-editing-lab/EDITING_PROMPT.md。所有設定以本次任務及使用者自己的專案 profile 為準，沒有預設講者、片長、固定口號或付費服務授權。

- 剪輯：skills/reference-guided-cut-planner/SKILL.md；輸出前 skills/spoken-edit-review/SKILL.md。
- 字幕：skills/caption-doctor/SKILL.md → references/edited-preview-captions.md。短語意、優先單行最多兩行；依實際詞錨點換張。科技字幕模式把語句逗號轉為兩個 U+0020，保留千分位。
- 匯出：skills/video-delivery-qc/references/export-choices.md；手機附件另見 references/mobile-share.md。
- 參考片分析與風格：skills/reference-edit-analyzer、skills/editing-style-profile。

## 任務問話框

新任務缺少設定時，先詢問目標片長（3／5／8分鐘內或自訂）與「先看逐字稿＋時間軸／直接渲染」。先看稿的使用者確認草稿後才渲染；直接渲染的授權不需逐切點重問。已有明確回答就沿用，預選不是回答。

提示使用者可指定必留開場、口頭禪、CTA與結尾。保留清單放在使用者專案中，不寫入安裝的 Skill；按原聲與語意匹配，不合成不存在的句子。沒有個人清單時不套用別人的口號。

渲染前展示原片解析度、比例、幀率／CFR或VFR、codec、色彩／bit depth、各音軌與碼率，確認仍未回答的選項。解析度選項包含可點選的 **480p (草稿)**、720p、1080p、4K、原始解析度；fps、codec、音訊及視訊碼率另行記錄。草稿可用合適的小碼率，不自動套55Mbps。

## 可執行入口

scripts/lab/plan-spoken-cut.py、render-spoken-preview.py、deliver-spoken-cut.py共用綁定原始素材的EDL與審查證據。每個入口以 --help 查看介面；render prepare須提供 --export-settings JSON，不能直接修改已綁定的job。原始畫質從原片回套EDL，不放大代理片。

句間優先嘗試0.12–0.18秒自然空隙，以完整語音、動作與同講者自然節奏為先；不凍住人臉補秒、不讓兩句人聲重疊。尾句另留完整尾音及素材允許的自然動作，不套句間空隙硬切結尾。

## 驗收

獨立來源／成片審查按 spoken-edit-review 的證據流程執行。技術、字幕視覺、實際聽辨分開回報；無聽辨只交標示清楚的待審預覽。候選口水音不等於已確認缺陷，不為清空計數而削掉子音。使用者對整體結果的肯定不自動關閉未逐項確認的專名、日期或音訊候選。

字幕與音畫都用最後輸出時間軸；保存作者詞錨點、套用lead/tail後實際SRT／ASS時間及不確定清單。成片、字幕包及手機分享副本分別標示；每次新編碼驗證實測大小、解碼及字幕清晰度，音訊copy時核對封包與時間戳。

安裝後的完整工具快照位置記在各 Skill 的 runtime-root.json；在該快照根目錄讀此入口並執行 scripts/lab。使用者素材與任務輸出放在自己的可寫專案，不放在安裝快照內。
