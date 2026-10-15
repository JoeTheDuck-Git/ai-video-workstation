# 0034 加強版：使用者確認案例

2026-10-15（Asia/Shanghai），使用者在23秒ABC試聽後明確回覆：「我覺得加強版本的很好，把skill 更新成加強版」。這是聲音處理偏好及該試聽版本的確認，沒有聲稱每個字均經逐字檢查。

檔案：DJI0034-stronger-mouth-cleanup-ABC.wav；Library `[private Library artifact]`，version 0；SHA256 `2e78e43107786c2015f23202a0c766dec94c857d8e5b216cac2099a4ca161011`。

|事件（0034成片秒）|原處理最大衰減|確認的加強版|平滑進出|ABC位置|
|---|---|---|---|---|
|G05：24.015–24.075|12dB|24dB，60ms窗|各10ms raised cosine|原音0–3；舊版4–7；加強8–11秒|
|G39：168.275–168.325|15dB|27dB，50ms窗|各8ms raised cosine|原音12–15；舊版16–19；加強20–23秒|

衰減數值是包絡最深處，不是整段或整句降低量。所有片段保持原始音量基準，48kHz、雙聲道、16bit PCM，無全片正規化。技術及獨立審查確認窗外樣本相同、峰值未增加、否定詞「不」169.06–169.24秒未改。agent actual_audio_review=false；使用者確認來自上述原話，不能冒充agent聽辨。

相對專案根目錄證據：`productions/dji-0034-pilot/mouth-repair-v2/stronger-trial/` 的 build.py、report.json、independent-review.json、library-delivery.json、human-review.json。既有待審報告保持原樣，新確認追加保存。其餘38處仍未確認，整片MP4尚未套用本加強版本。未來新素材以此力度作偏好參考，重新決定安全範圍；不以本例推定通用處理參數或零誤剪。
