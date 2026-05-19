<h1 align="center">📋 DesktopTodo</h1>

<p align="center">
  <strong>一款輕巧、跨平台的桌面待辦清單工具</strong><br>
  支援自訂標籤分類 · Telegram 推播通知 · 年度歷史歸檔
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.8+-blue.svg" alt="Python 3.8+">
  <img src="https://img.shields.io/badge/platform-Windows%20%7C%20macOS-lightgrey.svg" alt="Platform">
  <img src="https://img.shields.io/badge/dependencies-none-brightgreen.svg" alt="No Dependencies">
  <img src="https://img.shields.io/badge/license-MIT-green.svg" alt="MIT License">
</p>

---

## ✨ 功能特色

- 🏷️ **自訂 TAG 標籤系統** — 自由定義標籤名稱、前置詞，以及是否推播到 Telegram
- 📡 **Telegram 推播通知** — 總結時自動將重要待辦推送到手機，不遺漏任何事項
- 📁 **年度歷史歸檔** — 已完成任務自動歸檔為 Markdown 檔案，按年份分類保存
- ⏰ **定時提醒** — 為待辦設定預計時間，時間到自動彈出提醒
- 🔒 **隱私安全** — Telegram 金鑰不存在程式碼中，透過 UI 設定，安心分享
- 🍎 **跨平台** — 同時支援 Windows 與 macOS，自動適配字體與路徑
- 📦 **零依賴** — 100% 使用 Python 標準函式庫，無需安裝任何額外套件

---

## 🚀 快速開始

### 方法一：直接執行（推薦）

確認已安裝 [Python 3.8+](https://www.python.org/downloads/)，然後：

```bash
git clone https://github.com/YOUR_USERNAME/DesktopTodo.git
cd DesktopTodo
python DesktopTodo.py
```

### 方法二：下載執行檔

前往 [Releases](https://github.com/YOUR_USERNAME/DesktopTodo/releases) 頁面，下載適合您系統的執行檔：
- Windows → `DesktopTodo.exe`
- macOS → `DesktopTodo.app`

> 💡 執行檔不需要安裝 Python，雙擊即可使用。

---

## 🖥️ 介面預覽

<!-- 請將實際截圖放入 screenshots/ 資料夾後取消下方註解 -->
<!-- ![主畫面](screenshots/main.png) -->
<!-- ![設定頁面](screenshots/settings.png) -->

```
┌──────────────────────────────────┐
│  桌面待辦清單               [⚙️] │
│  ☑ 每日自動總結  [17:00]         │
│──────────────────────────────────│
│  ☐ [TODO-] 完成專案報告          │
│  ☐ [WORK-] 整理會議記錄          │
│  ☑ [IDEAL-] 學一門新技術         │
│──────────────────────────────────│
│  ➕ [#T▼] [輸入待辦...]  [HH:MM] │
│  [       執行手動總結       ]     │
└──────────────────────────────────┘
```

---

## 🏷️ TAG 標籤系統

可透過設定介面（⚙️）自由新增、修改、刪除。

| 預設 TAG | 前置詞 | 推播 | 總結時行為 |
|:---|:---|:---|:---|
| `#T` | `TODO-` | ✅ | 推播 → 備查存檔 → 從清單移除 |
| `#I` | `IDEAL-` | ✅ | 推播 → 備查存檔 → 從清單移除 |
| `#W` | `WORK-` | ❌ | 留在清單繼續追蹤 |

> 您也可以自訂如 `#M → 會議-`、`#Bug → 修復-` 等任意標籤組合。

---

## 📡 設定 Telegram 推播

1. 在 Telegram 搜尋 **@BotFather**，傳送 `/newbot` 建立機器人
2. 複製 BotFather 回覆的 **Token**（格式：`123456789:ABCDEF-xxxxx`）
3. 點擊程式右上角 `⚙️`，貼上 Token
4. 在 Telegram 中對您的 Bot 傳送任意訊息（例如 `hi`）
5. 點擊設定視窗的「🔍 自動取得 Chat ID」按鈕
6. 點擊「💾 儲存並套用設定」

完成！之後按下「執行手動總結」或等待自動總結時間，待辦就會推播到您的 Telegram。

---

## 📂 專案結構

```
DesktopTodo/
├── DesktopTodo.py          # 主程式（單檔即可運行）
├── README.md               # 本說明文件
├── LICENSE                 # MIT 授權
├── .gitignore              # Git 忽略規則
├── docs/
│   ├── USER_GUIDE.md       # 使用者完整操作手冊
│   └── DEV_README.md       # 開發者技術文件
└── screenshots/            # 截圖（歡迎貢獻）
```

### 使用者資料儲存位置

程式執行後，資料會自動儲存在以下位置（不在專案目錄中）：

| 系統 | 路徑 |
|:---|:---|
| Windows | `C:\Users\<user>\.desktoptodo\` |
| macOS | `/Users/<user>/.desktoptodo/` |

| 檔案 | 說明 |
|:---|:---|
| `todo_data.json` | 設定與待辦清單 |
| `history_YYYY.md` | 年度已完成歷史紀錄 |
| `push_record_YYYY.md` | 年度推播備查紀錄 |

---

## 🔨 打包為執行檔

如果您想為不會使用 Python 的使用者提供執行檔：

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name DesktopTodo DesktopTodo.py
```

打包完成後，執行檔位於 `dist/DesktopTodo.exe`（或 `.app`）。

> ⚠️ 必須在目標平台上打包：Windows 上打包的 `.exe` 無法在 macOS 使用，反之亦然。

---

## 📖 詳細文件

- 📘 [使用者操作手冊](docs/USER_GUIDE.md) — 完整功能說明、FAQ
- 📗 [開發者技術文件](docs/DEV_README.md) — 架構設計、資料結構、邏輯流程

---

## 🤝 貢獻

歡迎提交 Issue 或 Pull Request！無論是功能建議、Bug 回報還是翻譯協助，都非常感謝。

---

## 📄 授權

本專案採用 [MIT License](LICENSE) 開源授權。
