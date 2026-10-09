# Third-party components

本倉庫提供安裝協調腳本、自製的 `canvas-video` runtime、`canvas-video-pipeline` Skill 與 `video-delivery-qc` Skill；不重新散布下列第三方二進位檔或 Skill 原始碼。

| 元件 | 來源 | 安裝方式 | 授權／條款 |
|---|---|---|---|
| Node.js 22 | `nodejs.org` | 官方發行檔＋SHA-256 驗證 | Node.js 專案授權條款 |
| FFmpeg | 系統套件管理器／Homebrew | `brew`、`apt-get`、`dnf` 或 `pacman` | 依安裝版本與建置選項而定 |
| HyperFrames | `npm`／`heygen-com/hyperframes` | `npm install -g hyperframes@latest`、官方 Skill 指令 | Apache-2.0（請以官方倉庫為準） |
| 即夢畫布 CLI／Skill | `jimeng.jianying.com` | 官方安裝器 | 即夢官方條款 |
| Playwright 1.56 | npm／Microsoft | `npm ci` 安裝至獨立 Canvas runtime | Apache-2.0（請以套件內授權為準） |
| Three.js 0.170 | npm／mrdoob/three.js | `npm ci` 安裝至獨立 Canvas runtime | MIT（請以套件內授權為準） |

商標與服務名稱分屬其權利人。本專案不表示獲得上述專案或服務背書。
