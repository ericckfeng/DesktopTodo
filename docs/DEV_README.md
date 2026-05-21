# DesktopTodo — 開發者說明文件 (Developer Guide)

## 概覽

DesktopTodo 是一款跨平台（Windows / macOS）的桌面待辦事項管理工具，以 Python + Tkinter 開發。  
核心特色為可自訂的 TAG 分類系統、Telegram Bot 推播整合，以及本地化的歷史紀錄歸檔功能。

## 技術棧

| 項目 | 說明 |
|:---|:---|
| 語言 | Python 3.8+ |
| GUI 框架 | Tkinter（Python 標準函式庫） |
| 網路請求 | `urllib.request`（標準函式庫） |
| 資料格式 | JSON（設定與待辦）/ Markdown（歷史紀錄與推播備查） |
| 外部套件 | **無** — 100% 使用 Python 標準函式庫，無需 `pip install` |

## 檔案結構

```
DesktopTodo.py                   # 主程式（單檔）
~/.desktoptodo/                  # 使用者資料目錄（自動建立）
├── todo_data.json               # 設定 + 待辦清單資料 (含幾何尺寸)
├── motto.md                     # 隨機座右銘與金句 Markdown 檔
├── history_YYYY.md              # 年度已完成歷史紀錄
└── push_record_YYYY.md          # 年度 Telegram 推播備查紀錄
```

## 資料結構 (`todo_data.json`)

```json
{
  "app_title": "桌面待辦清單",
  "telegram_token": "123456:ABC-xxx",
  "telegram_chat_id": "950973637",
  "tags_config": [
    {"name": "#T", "prefix": "TODO-", "push": true},
    {"name": "#I", "prefix": "IDEAL-", "push": true},
    {"name": "#W", "prefix": "WORK-", "push": false}
  ],
  "todo_list": [
    {
      "text": "待辦事項文字",
      "done": false,
      "target_time": "15:00",
      "alerted": false,
      "prefix": "TODO-",
      "push": true,
      "finish_time": "2026-05-19 15:30:00"
    }
  ],
  "auto_summary_enable": true,
  "summary_time": "17:00",
  "geometry": "340x550+20+80"
}
```

### 欄位說明

| 欄位 | 型別 | 說明 |
|:---|:---|:---|
| `app_title` | string | 視窗標題，使用者可自訂 |
| `telegram_token` | string | Telegram Bot API Token |
| `telegram_chat_id` | string | 推播目標的 Chat ID（**必須為字串**） |
| `tags_config` | array | 自訂 TAG 規則列表 |
| `tags_config[].name` | string | 下拉選單中的簡稱（如 `#T`） |
| `tags_config[].prefix` | string | 推播與畫面顯示時轉換的前置詞（如 `TODO-`） |
| `tags_config[].push` | boolean | 總結時是否推播到 Telegram |
| `todo_list[].text` | string | 待辦事項文字 |
| `todo_list[].done` | boolean | 是否已完成 |
| `todo_list[].target_time` | string | 預計時間（`HH:MM` 格式，空字串代表無） |
| `todo_list[].alerted` | boolean | 是否已觸發時間提醒 |
| `todo_list[].prefix` | string | 此項目對應的前置詞 |
| `todo_list[].push` | boolean | 此項目是否需要推播 |
| `todo_list[].finish_time` | string | 完成時間戳（勾選完成時自動記錄） |
| `geometry` | string | 視窗的大小與位置（如 `寬x高+X+Y` 格式） |

## 核心邏輯流程

### 新增待辦 (`add_todo`)
```
使用者輸入文字 → 選擇 TAG → 查找 tags_config 取得 prefix 與 push → 存入 todo_list → 儲存 JSON
```

### 手動/自動總結 (`do_summary`)
```
1. archive_done_items()：把已勾選完成的項目寫入 history_YYYY.md，從 todo_list 移除
2. 遍歷未完成項目，篩選 push=True 的項目
3. 組成推播字串（prefix + text），送出 Telegram
4. 成功後，寫入 push_record_YYYY.md 備查
5. 推播成功的項目視同結案，從 todo_list 移除
6. 儲存 JSON 並刷新畫面
```

### 時間提醒 (`timer_loop`)
```
後台執行緒每 10 秒檢查一次：
  - 若待辦項目的 target_time ≤ 當前時間 且尚未 alerted → 彈出 messagebox 提醒
  - 若到達自動總結時間 且當天尚未執行 → 觸發 do_summary
```

### 待辦事項快捷操作與狀態列
- **右鍵選單 (Context Menu)**：對待辦事項 Label 綁定滑鼠右鍵點擊（Windows 綁定 `<Button-3>`，macOS 綁定 `<Button-2>`），彈出快顯選單提供「📋 複製內容」、「✏️ 編輯內容」、「❌ 刪除事項」。
- **雙擊編輯**：對待辦事項 Label 雙擊左鍵（`<Double-Button-1>`），呼叫 `simpledialog.askstring` 彈出對話方塊修改文字。
- **非干擾狀態列 (Status Bar)**：在主畫面最下方建立 `self.status_label`，當使用者複製、編輯或刪除成功時，呼叫 `show_temp_status(text, delay)` 顯示操作成功文字，並在預設 3 秒後自動呼叫 `clear_status` 隱藏，避免頻繁彈窗干擾。

### 視窗大小自適應與記憶
- **自適應寬度**：移除固定大小 `resizable(False, False)` 並改為 `True, True`。建立 Canvas 內部的 Window ID 關聯。當 Canvas 的寬度觸發 `<Configure>` 事件時，透過 `self.canvas.itemconfig(self.canvas_window, width=event.width)` 動態同步更新內部 `scroll_frame` 的寬度，使待辦行的 Label 寬度能水平拉伸。
- **視窗尺寸記憶**：程式初始化時設定預設 geometry。在 `load_data` 時從 JSON 讀取 `geometry`，若存在則在 `__init__` 中使用 `self.root.geometry()` 套用。同時監聽視窗關閉事件 `WM_DELETE_WINDOW` 呼叫 `on_close`，在 `save_data` 中讀取當前最新 `self.root.geometry()` 寫入 JSON 設定檔，達成大小與位置的完美復原。

### 隨機座右銘載入與自適應
- **金句載入**：在 `~/.desktoptodo/motto.md` 檔案不存在時自動建立預設內容。讀取檔案時逐行解析，利用正則表達式清除 Markdown 標記，並過濾掉以 `#` 或 `<!--` 開頭的標題與註解，保留純文字列表。
- **座右銘自適應折行**：為防止視窗拉小時文字溢出，綁定 `self.root` 的 `<Configure>` 事件（限制僅在 `event.widget == self.root` 時觸發），動態計算 `event.width - 40` 設定為金句 Label 的 `wraplength`。
- **點擊隨機切換**：金句 Label 綁定 `<Button-1>`。點擊時隨機從 `self.mottos` 陣列中抽取出新金句，如果有多條金句，則自動迴圈篩選，避免連續抽取到重複內容。

## 跨平台適配

| 項目 | Windows | macOS |
|:---|:---|:---|
| 字體 | 微軟正黑體 | PingFang TC |
| 資料路徑 | `C:\Users\<user>\.desktoptodo\` | `/Users/<user>/.desktoptodo/` |
| 判斷方式 | `platform.system() == "Windows"` | `platform.system() == "Darwin"` |

## 打包發布

### Windows
```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name DesktopTodo DesktopTodo.py
```

### macOS
```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name DesktopTodo DesktopTodo.py
```

> ⚠️ **重要**：必須在目標平台上執行打包。Windows 上打包的 `.exe` 無法在 Mac 上使用，反之亦然。

## 注意事項與已知限制

1. **Telegram Token/Chat ID 必須以字串儲存**：JSON 序列化時若型別為 `int`，會導致 API 請求失敗。程式中 `save_data` 與 `load_data` 均已加入 `str()` 強制轉型保護。
2. **向後相容**：`refresh_todo` 中有針對舊版資料結構（使用 `tag` 欄位而非 `prefix`）的自動遷移邏輯。
3. **執行緒安全**：`timer_loop` 使用 `self.root.after()` 將 UI 操作排入主執行緒，避免 Tkinter 非主執行緒操作問題。
4. **歷史紀錄以年分檔**：`history_YYYY.md` 與 `push_record_YYYY.md` 會隨年份自動產生新檔案，不需手動管理。
