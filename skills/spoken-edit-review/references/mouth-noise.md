# Mouth-noise candidate review

Use the user's exact current export and its source map. Hash original, export, map, transcript and analysis implementation. Keep analysis outputs in a new directory; never overwrite media or a bound review. Updating these rules invalidates old rule-bound approvals for future reuse, not the existence of previously delivered files.

Ask for one or two approximate audible examples when unavailable; continue non-destructive analysis while waiting. User reports remain open even if the detector finds nothing. Timestamp examples calibrate navigation, not an automatic denoise/delete policy.

## Available local helper

`python scripts/mouth_noise_candidates.py --export FILE --map MAP --asr OUTPUT_WORD_JSON --out NEW_DIRECTORY`

Uses installed FFmpeg, NumPy and Matplotlib only. No downloads, model calls or uploads. It decodes the default audio stream to analysis mono at 24 kHz, measures 20 ms windows every 10 ms, compares local RMS to nearby quiet-frame energy, and records crest factor and low/high-band spectral ratios. Thresholds are engineering navigation defaults, not a validated swallowing classifier. Mono analysis may miss channel-specific or phase-cancelled noise; full-band original context WAVs remain necessary. No detections does not imply no audible defect.

Every event within 80 ms of a recognized word is protected for speech review. Events outside word intervals are only ASR-gap candidates: omitted or mistimed speech, quiet consonants, aspiration, breaths, microphone handling and codec artifacts remain possible. Low volume or short duration alone never permits removal. Missing ASR coverage is protected as unknown; recognized word intervals from overlapping ASR windows are conservatively unioned. The helper writes no EDL or filter to modify audio.

Reports retain all detected events, reasons, uncertainty and source interval pieces. At most 12 prioritized examples receive original/export context WAVs and waveform/spectrogram plots; this is explicitly sampled evidence, not full listening coverage. Mapping splits context at edits and labels discontinuous source pieces; never concatenate them and call that uninterrupted original audio. WAV snippets preserve native rate/channels without loudness normalization; separately label any deliberately amplified listening aid. Candidate bounds are analysis windows, not precise phoneme or editing boundaries.

## Independent review and decision

A fresh independent reviewer checks actual file/map hashes, feature/time calculations, ASR uncertainty, protected counterexamples (quiet plosive, aspiration, word tail, breath), joins and source correspondence. Distinguish numerical inspection, transcript review and actual audio listening. Reading PCM, spectrograms or transcripts is not listening. Save real dispatch and completion receipts; keep actual_audio_review=false and content_status=needs_review without supported listening. Report analyzed range and sampled ranges separately from listening coverage (zero when unavailable).

After user timestamp calibration and actual listening evidence, classify each event as confirmed distracting non-speech, normal speech/breath, or unresolved. In this diagnostic task do not repair or render before that calibration. Never promise future films error-free. An independently confirmed distracting event may be locally attenuated or repaired using verified adjacent room tone when authorized; retain speech, natural gap and A/V duration. Do not blanket gate, globally denoise, replace with digital silence, overlap speech, or remove normal breath by threshold. Cutting is a last option when source handles and motion remain natural and the owning source map is updated. Compare unchanged and repaired context at matched playback level, then verify rendered audio and sync; unresolved listening remains needs_review.

## 使用者回報校準：口腔雜音（mouth noise）

用「口腔雜音」作總稱，包含吞嚥聲、咂嘴聲與唾液黏連聲等可能類型；沒有實際聽辨證據時只記使用者描述或未確認事件，不靠波形替聲音命名。波形瞬態、頻譜、局部相對音量、語音邊界與上下文要一起考慮；不能用單一分貝、短時長或 ASR 空白直接刪除。

收到時間點時，以指定成片版本的約略定位處理，每點預設前後 2 秒，依同一來源 map 對照原片。使用 `review_user_audio_marks.py --prior-report REPORT --marks MARKS_JSON --out NEW_DIRECTORY`；MARKS_JSON 包含 reported_seconds 陣列和可選 radius_seconds。每個使用者標記都要輸出，不能因未達閾值、與字詞重疊、不是 top-N 或沒有機器候選而忽略。將 user_report 與 machine_event 分開保存；「保護不修」不等於「不列出問題」。正常呼吸、輕輔音／送氣與尾音作反例；否定詞與重要條件有辨識分歧時擴大保護，不能以雜音清理之名消除。

逐點記錄漏列原因：是否真的未達瞬態門檻、是否群聚後超過長度上限、是否 ASR 將句間涵蓋為字詞、是否排序或展示名額造成。廣泛時間窗內有機器事件不能視為成功找到使用者所指聲音。門檻只作本片導航校準，不以七個時間點硬編碼通用模型、不報準確率。使用者回報優先導航，但不是精確切點或音節邊界證據。

對已授權的局部 A/B 試聽，可在多項證據支持的間隙內，另存非常輕微、保留樣本數與聲道、平滑進出的試驗性減弱。只作未確認候選的聽感比較，不稱已修好或確診。先檢查完整上下文與 ASR 保護區；重疊語音、不明邊界或否定詞分歧處先不動。不要自動對每個使用者秒數套濾鏡。A/B 相同來源與音量基準，不以整段變小製造改善錯覺；先檢查未修改區樣本一致、時長一致、沒有新增峰值，再交獨立 reviewer。無實際聽審時仍需使用者確認，不能自動套用整片。手機試聽上傳僅限使用者已授權的片段，未授權不外傳。

可選的保時長局部處理方式：口腔雜音優先保持時間長度，不刪時間、不改畫面。於證據支持的局部聲音起止，以實際音訊 sample 定位並作溫和衰減及平滑進出；合適時才使用同場景、確認無語音的底噪修補。避免硬切零靜音造成 click 或底噪斷層。實驗中的 40 ms 視窗只是該事件的局部選擇，不能當其他位置的固定模板。維持總 sample 數、聲道、取樣率與同步；與語音重疊或邊界不明則保留待修，不能整段消音。此偏好不擴張為全片自動處理授權。

## 人類確認的局部回歸案例

### 加強版處理偏好（2026-10-15）

歷史個案的使用者曾偏好加強版本。這不是新使用者的批准；新任務依當次授權及力度偏好，對證據支持、能與字音分離的短促事件，優先採用**明顯減弱的局部加強版**，不必把「非常輕微」當成固定上限，但不要自動套用歷史個案力度；語音保護、時間不變、證據與交付規則仍適用。

先依當次原音定位事件與語音邊界，以平滑包絡降低事件，保留窗外PCM、樣本數、聲道及底噪連續性。0034 的24／27dB最大衰減、60／50ms處理窗、10／8ms進出僅作已確認參考，不固定套用其他素材；按事件音量和邊界調整，不為追求更乾淨而擴大到字音。已知同檔同窗可沿用確認的加強參數；新位置仍須檢查上下文、修前修後及獨立審查，不必為一般已授權清理重問力度。若字音重疊、邊界不明或加強後可能傷語音，保留待審並提供局部對照，不能把38個未確認候選全部套上強衰減。

詳見 [0034 加強版人類確認](mouth-noise-0034-stronger-case.md)。這次確認只表示使用者喜歡兩處加強試聽效果，不等於逐字無損、全片已清乾淨或已授權本輪重渲染。

見 [0044 第一處詞間案例](mouth-noise-first-gap-case.md)。人類對指定試聽檔的明確回饋，可解除**該檔、該位置、該確認項目**的不確定性；必須保留原話、來源訊息、時間、Library版本與檔案hash。不可據此宣稱agent聽過、其他位置已安全、完整成片final_pass，或自動取得重渲染／批次處理授權。變更素材或處理窗後，不沿用舊聽感確認。參數是案例資料，不是通用預設。
