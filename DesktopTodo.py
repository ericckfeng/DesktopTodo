import tkinter as tk
from tkinter import ttk, Checkbutton, BooleanVar, messagebox, simpledialog
import json
import os
import platform
from datetime import datetime
import threading
import time
import urllib.request
import urllib.parse

# 跨平台資料儲存路徑
DATA_DIR = os.path.expanduser("~/.desktoptodo")
os.makedirs(DATA_DIR, exist_ok=True)
CONFIG_FILE = os.path.join(DATA_DIR, "todo_data.json")

# 跨平台字體
if platform.system() == "Darwin":
    DEFAULT_FONT = ("PingFang TC", 11)
    BOLD_FONT = ("PingFang TC", 14, "bold")
    SMALL_BOLD_FONT = ("PingFang TC", 11, "bold")
else:
    DEFAULT_FONT = ("微軟正黑體", 10)
    BOLD_FONT = ("微軟正黑體", 14, "bold")
    SMALL_BOLD_FONT = ("微軟正黑體", 11, "bold")

DEFAULT_TIME = "17:00"
ALWAYS_ON_TOP = True
WINDOW_ALPHA = 0.92
WINDOW_WIDTH = 340
WINDOW_HEIGHT = 550

class DesktopTodo:
    def __init__(self, root):
        self.root = root
        self.geometry_data = f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}+20+80"
        self.root.attributes("-alpha", WINDOW_ALPHA)
        self.root.attributes("-topmost", ALWAYS_ON_TOP)
        self.root.resizable(True, True)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        # 預設資料結構
        self.app_title = "桌面待辦清單"
        self.telegram_token = ""
        self.telegram_chat_id = ""
        self.tags_config = [
            {"name": "#T", "prefix": "TODO-", "push": True},
            {"name": "#I", "prefix": "IDEAL-", "push": True},
            {"name": "#W", "prefix": "WORK-", "push": False}
        ]
        self.todo_list = []
        self.auto_summary_enable = tk.BooleanVar(value=True)
        self.summary_time = tk.StringVar(value=DEFAULT_TIME)
        
        self.load_data()
        self.root.geometry(self.geometry_data)
        self.root.title(self.app_title)

        # 載入座右銘
        self.mottos = self.load_motto()
        self.current_motto = ""

        # 构建UI
        self.create_ui()
        self.refresh_todo()
        self.show_random_motto()
        # 启动定时检测线程
        self.start_timer_thread()

    def create_ui(self):
        # 顶部框架
        top_frame = tk.Frame(self.root)
        top_frame.pack(fill="x", padx=10, pady=5)
        
        self.title_label = tk.Label(top_frame, text=self.app_title, font=BOLD_FONT)
        self.title_label.pack(side="left", expand=True)
        
        # 設定按鈕
        set_btn = ttk.Button(top_frame, text="⚙️", width=3, command=self.open_settings)
        set_btn.pack(side="right")

        # 頂部座右銘區域
        self.motto_frame = tk.Frame(self.root, bg="#f9f9f9", bd=1, relief="groove")
        self.motto_frame.pack(fill="x", padx=10, pady=(2, 5))
        
        self.motto_label = tk.Label(
            self.motto_frame, 
            text="", 
            font=(DEFAULT_FONT[0], 9, "italic"), 
            fg="#666666", 
            bg="#f9f9f9",
            wraplength=WINDOW_WIDTH-40, 
            cursor="hand2"
        )
        self.motto_label.pack(fill="x", padx=5, pady=4)
        
        # 綁定點擊事件與懸停效果
        self.motto_label.bind("<Button-1>", lambda e: self.show_random_motto())
        self.motto_label.bind("<Enter>", lambda e: [self.motto_label.config(fg="#0056b3"), self.show_temp_status("💡 點擊可隨機更換座右銘")])
        self.motto_label.bind("<Leave>", lambda e: [self.motto_label.config(fg="#666666"), self.clear_status()])
        
        # 綁定全域視窗 Configure 以自適應折行
        self.root.bind("<Configure>", self.on_window_configure)

        # 定时设置区域
        set_frame = tk.Frame(self.root)
        set_frame.pack(fill="x", padx=10, pady=3)
        tk.Checkbutton(set_frame, text="每日自動總結", variable=self.auto_summary_enable, command=self.save_data, font=DEFAULT_FONT).pack(side="left")
        ttk.Entry(set_frame, textvariable=self.summary_time, width=6, font=DEFAULT_FONT).pack(side="left", padx=5)

        # 分割线
        ttk.Separator(self.root, orient="horizontal").pack(fill="x", padx=10, pady=5)

        # 待办画布+滚动条
        list_frame = tk.Frame(self.root)
        list_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.canvas = tk.Canvas(list_frame, width=WINDOW_WIDTH-30, height=300, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.canvas.yview)
        self.scroll_frame = tk.Frame(self.canvas)
        
        # 記錄 canvas window 的 ID
        self.canvas_window = self.canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")
        
        # 當 scroll_frame 大小改變時，更新 canvas 捲動區域
        self.scroll_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        
        # 當 Canvas 寬度改變時，動態更新 scroll_frame 寬度以實現水平自適應
        self.canvas.bind("<Configure>", lambda event: self.canvas.itemconfig(self.canvas_window, width=event.width))
        
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # 新增待办输入框
        input_frame = tk.Frame(self.root)
        input_frame.pack(fill="x", padx=10, pady=10)
        
        tk.Label(input_frame, text="➕", font=DEFAULT_FONT).pack(side="left")
        
        # TAG 選擇
        self.tag_var = tk.StringVar()
        self.tag_cb = ttk.Combobox(input_frame, textvariable=self.tag_var, width=4, state="readonly", font=DEFAULT_FONT)
        self.tag_cb.pack(side="left", padx=(0, 5))
        self.update_tag_combobox_values()
        
        self.new_entry = ttk.Entry(input_frame, font=DEFAULT_FONT)
        self.new_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        self.new_entry.bind("<Return>", self.add_todo)
        
        # 預計時間輸入
        self.time_entry = ttk.Entry(input_frame, width=5, font=DEFAULT_FONT)
        self.time_entry.insert(0, "HH:MM")
        self.time_entry.bind("<FocusIn>", lambda e: self.time_entry.delete(0, tk.END) if self.time_entry.get() == "HH:MM" else None)
        self.time_entry.bind("<FocusOut>", lambda e: self.time_entry.insert(0, "HH:MM") if not self.time_entry.get() else None)
        self.time_entry.pack(side="left", padx=(0, 5))
        self.time_entry.bind("<Return>", self.add_todo)
        
        add_btn = ttk.Button(input_frame, text="新增", width=4, command=self.add_todo)
        add_btn.pack(side="right")

        # 功能按钮
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(fill="x", padx=10, pady=3)
        ttk.Button(btn_frame, text="執行手動總結", command=self.do_summary).pack(side="left", expand=True, fill="x")

        # 狀態列
        self.status_label = tk.Label(self.root, text="", font=(DEFAULT_FONT[0], 9), fg="#888888", anchor="w")
        self.status_label.pack(side="bottom", fill="x", padx=10, pady=(0, 2))

    def update_tag_combobox_values(self):
        values = [t["name"] for t in self.tags_config]
        values.append("無")
        self.tag_cb["values"] = values
        if self.tag_var.get() not in values and values:
            self.tag_var.set(values[0])

    def add_todo(self, event=None):
        text = self.new_entry.get().strip()
        if not text:
            return
        target_time = self.time_entry.get().strip()
        if target_time == "HH:MM" or not target_time:
            target_time = ""
            
        tag_name = self.tag_var.get()
        tag_prefix = ""
        push_tg = False
        if tag_name != "無":
            for t in self.tags_config:
                if t["name"] == tag_name:
                    tag_prefix = t["prefix"]
                    push_tg = t["push"]
                    break
            
        self.todo_list.append({
            "text": text, 
            "done": False, 
            "target_time": target_time, 
            "alerted": False, 
            "prefix": tag_prefix,
            "push": push_tg
        })
        self.new_entry.delete(0, tk.END)
        self.time_entry.delete(0, tk.END)
        self.time_entry.insert(0, "HH:MM")
        self.save_data()
        self.refresh_todo()

    def refresh_todo(self):
        # 清空旧组件
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        # 渲染待办
        for idx, item in enumerate(self.todo_list):
            var = BooleanVar(value=item.get("done", False))
            row_frame = tk.Frame(self.scroll_frame)
            row_frame.pack(anchor="w", fill="x", padx=5, pady=2)

            cb = Checkbutton(
                row_frame, variable=var,
                command=lambda i=idx, v=var: self.toggle_done(i, v)
            )
            cb.pack(side="left")

            fg_color = "#888888" if item.get("done", False) else "#222222"
            font_style = DEFAULT_FONT if not item.get("done", False) else (DEFAULT_FONT[0], DEFAULT_FONT[1], "overstrike")
            
            disp_text = item["text"]
            
            # 向後相容舊資料結構
            t_prefix = item.get("prefix", "")
            if not t_prefix and "tag" in item:
                old_tag = item["tag"]
                for t in self.tags_config:
                    if t["name"] == old_tag:
                        t_prefix = t["prefix"]
                        item["prefix"] = t_prefix
                        item["push"] = t["push"]
                        break
            
            if t_prefix:
                disp_text = f"[{t_prefix}] {disp_text}"
                
            t_time = item.get("target_time", "")
            if t_time:
                disp_text = f"[{t_time}] {disp_text}"
                
            label = tk.Label(row_frame, text=disp_text, font=font_style, fg=fg_color, anchor="w", justify="left")
            label.pack(side="left", fill="x", expand=True)
            
            # 綁定右鍵選單與雙擊編輯
            self.bind_context_menu(label, idx)

    def toggle_done(self, idx, var):
        is_done = var.get()
        self.todo_list[idx]["done"] = is_done
        if is_done:
            self.todo_list[idx]["finish_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        else:
            self.todo_list[idx].pop("finish_time", None)
        self.save_data()
        self.refresh_todo()

    def send_telegram(self, text):
        if not self.telegram_token or not self.telegram_chat_id:
            return False, "未設定 Token 或 Chat ID"

        url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
        data = urllib.parse.urlencode({'chat_id': self.telegram_chat_id, 'text': text}).encode("utf-8")
        try:
            req = urllib.request.Request(url, data=data)
            urllib.request.urlopen(req)
            return True, ""
        except urllib.error.HTTPError as e:
            err_msg = f"HTTP Error {e.code}: {e.reason}"
            if e.code == 400:
                err_msg += "\n(可能是 Chat ID 格式錯誤，請確認輸入的是純數字 ID，而非 Bot 名稱)"
            elif e.code == 401:
                err_msg += "\n(Token 無效，請檢查 Token 是否正確)"
            print(f"Telegram error: {err_msg}")
            return False, err_msg
        except Exception as e:
            print(f"Telegram error: {e}")
            return False, str(e)

    def archive_done_items(self):
        done_items = [item for item in self.todo_list if item.get("done", False)]
        if not done_items:
            return
            
        year = datetime.now().strftime("%Y")
        history_file = os.path.join(DATA_DIR, f"history_{year}.md")
        
        with open(history_file, "a", encoding="utf-8") as f:
            for item in done_items:
                f_time = item.get("finish_time", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                p_str = f" [{item.get('prefix')}]" if item.get('prefix') else ""
                f.write(f"- [x] {f_time}{p_str} {item['text']}\n")
                
        # 移除已完成項目
        self.todo_list = [item for item in self.todo_list if not item.get("done", False)]

    def do_summary(self):
        # 1. 歸檔一般已完成項目到歷史紀錄
        self.archive_done_items()
        
        # 2. 收集需要推播的未完成項目
        undone = [item for item in self.todo_list if not item.get("done", False)]
        summary_lines = []
        pushed_items = []
        
        needs_push = any(item.get("push", False) for item in undone)
        if needs_push and (not self.telegram_token or not self.telegram_chat_id):
            messagebox.showwarning("推播失敗", "您勾選了需要推播的 TAG，但尚未設定 Telegram 金鑰！\n請點擊右上角設定按鈕填寫。")
            self.save_data()
            self.refresh_todo()
            return

        for item in undone:
            if item.get("push", False):
                prefix = item.get("prefix", "")
                summary_lines.append(f"{prefix}{item['text']}")
                pushed_items.append(item)
                
        # 3. 發送推播
        if summary_lines:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
            summary_lines.insert(0, f"【每日待辦推播 {current_time}】")
            success, err_msg = self.send_telegram("\n".join(summary_lines))
            
            if success:
                # 存入另一個年份 MD 檔備查
                year = datetime.now().strftime("%Y")
                push_file = os.path.join(DATA_DIR, f"push_record_{year}.md")
                with open(push_file, "a", encoding="utf-8") as f:
                    for item in pushed_items:
                        f_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        f.write(f"- [Pushed] {f_time} [{item.get('prefix')}] {item['text']}\n")
                
                # 4. 推播出去視同結案，從清單移除
                self.todo_list = [item for item in self.todo_list if item not in pushed_items]
            else:
                messagebox.showerror("推播錯誤", f"Telegram 推播失敗：\n{err_msg}")
            
        # 儲存與重整畫面
        self.save_data()
        self.refresh_todo()

    def save_data(self):
        try:
            self.geometry_data = self.root.geometry()
        except Exception:
            pass
        data = {
            "app_title": self.app_title,
            "telegram_token": str(self.telegram_token),
            "telegram_chat_id": str(self.telegram_chat_id),
            "tags_config": self.tags_config,
            "todo_list": self.todo_list,
            "auto_summary_enable": self.auto_summary_enable.get(),
            "summary_time": self.summary_time.get(),
            "geometry": self.geometry_data
        }
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load_data(self):
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                    self.app_title = data.get("app_title", self.app_title)
                    self.telegram_token = str(data.get("telegram_token", self.telegram_token))
                    # 強制轉字串，避免 JSON 把純數字 ID 變成 int
                    self.telegram_chat_id = str(data.get("telegram_chat_id", self.telegram_chat_id))
                    self.tags_config = data.get("tags_config", self.tags_config)
                    self.todo_list = data.get("todo_list", [])
                    self.auto_summary_enable.set(data.get("auto_summary_enable", True))
                    self.summary_time.set(data.get("summary_time", DEFAULT_TIME))
                    self.geometry_data = data.get("geometry", f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}+20+80")
                except json.JSONDecodeError:
                    pass

    def open_settings(self):
        set_win = tk.Toplevel(self.root)
        set_win.title("設定")
        set_win.geometry("460x580")
        set_win.attributes("-topmost", True)
        
        # 標題設定
        tk.Label(set_win, text="🔧 基本設定", font=SMALL_BOLD_FONT).pack(pady=(10, 5), anchor="w", padx=10)
        
        f1 = tk.Frame(set_win)
        f1.pack(fill="x", padx=10, pady=2)
        tk.Label(f1, text="視窗標題：", font=DEFAULT_FONT, width=12, anchor="e").pack(side="left")
        title_var = tk.StringVar(value=self.app_title)
        ttk.Entry(f1, textvariable=title_var, font=DEFAULT_FONT).pack(side="left", fill="x", expand=True)

        ttk.Separator(set_win, orient="horizontal").pack(fill="x", padx=10, pady=8)

        # Telegram 設定教學
        tk.Label(set_win, text="📡 Telegram 推播設定", font=SMALL_BOLD_FONT).pack(anchor="w", padx=10)
        help_text = (
            "❶ 在 Telegram 搜尋 @BotFather，傳送 /newbot 建立機器人\n"
            "❷ BotFather 會回覆一段 Token（格式如 123456:ABC-xxx），貼到下方\n"
            "❸ 貼好 Token 後，先對您的 Bot 傳送任意訊息（例如 hi）\n"
            "❹ 點擊下方「自動取得 Chat ID」按鈕，程式會自動填入"
        )
        tk.Label(set_win, text=help_text, font=(DEFAULT_FONT[0], 9), fg="#555", justify="left").pack(anchor="w", padx=15, pady=(2, 5))

        # Token 欄位
        f2 = tk.Frame(set_win)
        f2.pack(fill="x", padx=10, pady=2)
        tk.Label(f2, text="TG Token：", font=DEFAULT_FONT, width=12, anchor="e").pack(side="left")
        token_var = tk.StringVar(value=self.telegram_token)
        ttk.Entry(f2, textvariable=token_var, font=DEFAULT_FONT).pack(side="left", fill="x", expand=True)

        # Chat ID 欄位 + 自動取得按鈕
        f3 = tk.Frame(set_win)
        f3.pack(fill="x", padx=10, pady=2)
        tk.Label(f3, text="TG Chat ID：", font=DEFAULT_FONT, width=12, anchor="e").pack(side="left")
        chat_id_var = tk.StringVar(value=self.telegram_chat_id)
        ttk.Entry(f3, textvariable=chat_id_var, font=DEFAULT_FONT).pack(side="left", fill="x", expand=True)
        
        def auto_get_chat_id():
            token = token_var.get().strip()
            if not token:
                messagebox.showerror("錯誤", "請先填入 TG Token！")
                return
            try:
                url = f"https://api.telegram.org/bot{token}/getUpdates"
                req = urllib.request.Request(url)
                resp = urllib.request.urlopen(req)
                result = json.loads(resp.read().decode())
                if result.get("ok") and result.get("result"):
                    chat_id = str(result["result"][-1]["message"]["chat"]["id"])
                    chat_id_var.set(chat_id)
                    messagebox.showinfo("成功", f"已自動取得 Chat ID：{chat_id}")
                else:
                    messagebox.showwarning("找不到", "請先對您的 Bot 傳送任意訊息（例如 hi），\n然後再按此按鈕。")
            except urllib.error.HTTPError as e:
                if e.code == 404:
                    messagebox.showerror("Token 無效", "Token 格式不正確，請確認貼上完整的 Token\n（格式如 123456789:ABCDEF....）")
                else:
                    messagebox.showerror("錯誤", f"網路錯誤：{e}")
            except Exception as e:
                messagebox.showerror("錯誤", f"無法取得：{e}")
        
        f4 = tk.Frame(set_win)
        f4.pack(fill="x", padx=10, pady=2)
        ttk.Button(f4, text="🔍 自動取得 Chat ID", command=auto_get_chat_id).pack(side="left", padx=(80, 0))
        tk.Label(f4, text="← 請先對 Bot 傳訊息再按", font=(DEFAULT_FONT[0], 8), fg="#999").pack(side="left", padx=5)
        
        ttk.Separator(set_win, orient="horizontal").pack(fill="x", padx=10, pady=10)
        
        # TAG 設定
        tk.Label(set_win, text="🏷️ 自訂 TAG 設定", font=SMALL_BOLD_FONT).pack(anchor="w", padx=10)
        tk.Label(set_win, text="格式: 名稱 | 前置詞 | 推播", font=("微軟正黑體", 8), fg="gray").pack(anchor="w", padx=10)
        
        tag_frame = tk.Frame(set_win)
        tag_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # 暫存編輯中的 tags
        temp_tags = list(self.tags_config)
        
        listbox = tk.Listbox(tag_frame, font=DEFAULT_FONT, height=6)
        listbox.pack(side="left", fill="both", expand=True)
        
        def render_list():
            listbox.delete(0, tk.END)
            for t in temp_tags:
                push_str = "推播" if t["push"] else "不推"
                listbox.insert(tk.END, f"{t['name']} | {t['prefix']} | {push_str}")
        render_list()

        btn_f = tk.Frame(tag_frame)
        btn_f.pack(side="right", fill="y", padx=5)
        
        def add_tag():
            add_w = tk.Toplevel(set_win)
            add_w.title("新增 TAG")
            add_w.geometry("250x150")
            add_w.attributes("-topmost", True)
            
            tk.Label(add_w, text="名稱 (例:#X):", font=DEFAULT_FONT).grid(row=0, column=0, pady=5, padx=5)
            n_var = tk.StringVar()
            ttk.Entry(add_w, textvariable=n_var, width=10).grid(row=0, column=1)
            
            tk.Label(add_w, text="前置詞:", font=DEFAULT_FONT).grid(row=1, column=0, pady=5, padx=5)
            p_var = tk.StringVar()
            ttk.Entry(add_w, textvariable=p_var, width=10).grid(row=1, column=1)
            
            push_var = tk.BooleanVar(value=False)
            tk.Checkbutton(add_w, text="推播到 Telegram", variable=push_var, font=DEFAULT_FONT).grid(row=2, column=0, columnspan=2, pady=5)
            
            def save_t():
                if n_var.get():
                    temp_tags.append({"name": n_var.get(), "prefix": p_var.get(), "push": push_var.get()})
                    render_list()
                    add_w.destroy()
            ttk.Button(add_w, text="確定", command=save_t).grid(row=3, column=0, columnspan=2, pady=5)

        def del_tag():
            sel = listbox.curselection()
            if sel:
                temp_tags.pop(sel[0])
                render_list()

        ttk.Button(btn_f, text="新增規則", command=add_tag).pack(pady=2)
        ttk.Button(btn_f, text="刪除選取", command=del_tag).pack(pady=2)

        def save_all():
            # 防咆驗證 Chat ID 格式
            chat_id_input = chat_id_var.get().strip()
            if chat_id_input and not chat_id_input.lstrip("-").isdigit():
                messagebox.showerror("格式錯誤", 
                    f"「Chat ID」格式不正確！\n"
                    f"您輸入的是：{chat_id_input}\n\n"
                    f"請填入純數字 (e.g. 950973637)，\n"
                    f"可對 @userinfobot 傳消息查詢自己的 ID")
                return
            
            self.app_title = title_var.get()
            self.telegram_token = token_var.get().strip()
            self.telegram_chat_id = chat_id_input
            self.tags_config = temp_tags
            
            self.title_label.config(text=self.app_title)
            self.root.title(self.app_title)
            self.update_tag_combobox_values()
            
            self.save_data()
            set_win.destroy()
            messagebox.showinfo("成功", "設定已儲存！新規則將套用於下次新增的待辦事項。")

        ttk.Button(set_win, text="💾 儲存並套用設定", command=save_all).pack(pady=10)


    def start_timer_thread(self):
        # 后台线程定时检测时间
        def timer_loop():
            last_day = ""
            while True:
                time.sleep(10)
                now = datetime.now()
                now_time = now.strftime("%H:%M")
                now_day = now.strftime("%Y-%m-%d")
                
                # 檢查待辦時間提示
                needs_save = False
                for item in self.todo_list:
                    if not item.get("done", False) and item.get("target_time") and not item.get("alerted", False):
                        if now_time >= item["target_time"]:
                            item["alerted"] = True
                            needs_save = True
                            self.root.after(0, lambda text=item["text"]: messagebox.showinfo("時間到！", f"待辦事項：\n{text}"))
                if needs_save:
                    self.save_data()
                    self.root.after(0, self.refresh_todo)
                    
                # 到设定时间且当天只执行一次
                if self.auto_summary_enable.get() and now_time == self.summary_time.get() and last_day != now_day:
                    last_day = now_day
                    self.root.after(0, self.do_summary)
        t = threading.Thread(target=timer_loop, daemon=True)
        t.start()

    def bind_context_menu(self, widget, idx):
        widget.bind("<Button-3>", lambda event, i=idx: self.show_context_menu(event, i))
        widget.bind("<Button-2>", lambda event, i=idx: self.show_context_menu(event, i))
        widget.bind("<Double-Button-1>", lambda event, i=idx: self.edit_todo_item(i))

    def show_context_menu(self, event, idx):
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label="📋 複製內容", command=lambda i=idx: self.copy_todo_item(i))
        menu.add_command(label="✏️ 編輯內容", command=lambda i=idx: self.edit_todo_item(i))
        menu.add_separator()
        menu.add_command(label="❌ 刪除事項", command=lambda i=idx: self.delete_todo_item(i))
        menu.post(event.x_root, event.y_root)

    def copy_todo_item(self, idx):
        if 0 <= idx < len(self.todo_list):
            item = self.todo_list[idx]
            text_to_copy = item["text"]
            t_prefix = item.get("prefix", "")
            t_time = item.get("target_time", "")
            full_text = text_to_copy
            if t_prefix:
                full_text = f"[{t_prefix}] {full_text}"
            if t_time:
                full_text = f"[{t_time}] {full_text}"
                
            self.root.clipboard_clear()
            self.root.clipboard_append(full_text)
            self.root.update()
            self.show_temp_status(f"📋 已複製：{full_text}")

    def edit_todo_item(self, idx):
        if 0 <= idx < len(self.todo_list):
            item = self.todo_list[idx]
            new_text = simpledialog.askstring("修改待辦事項", "請輸入新的待辦內容：", initialvalue=item["text"], parent=self.root)
            if new_text is not None:
                new_text = new_text.strip()
                if new_text:
                    item["text"] = new_text
                    self.save_data()
                    self.refresh_todo()
                    self.show_temp_status("✏️ 已修改待辦事項")

    def delete_todo_item(self, idx):
        if 0 <= idx < len(self.todo_list):
            item = self.todo_list[idx]
            if messagebox.askyesno("確認刪除", f"確定要刪除此待辦事項嗎？\n\n「{item['text']}」", parent=self.root):
                self.todo_list.pop(idx)
                self.save_data()
                self.refresh_todo()
                self.show_temp_status("❌ 已刪除待辦事項")

    def load_motto(self):
        motto_file = os.path.join(DATA_DIR, "motto.md")
        default_mottos = [
            "每一天都是新的開始，專注於當下。",
            "萬事起頭難，堅持就是勝利。",
            "卓越不是一個單一的行為，而是一個習慣。",
            "簡單就是美，少即是多。",
            "不怕慢，只怕站。持續前進就是力量。",
            "相信自己，你比想像中更強大。"
        ]
        
        if not os.path.exists(motto_file):
            try:
                with open(motto_file, "w", encoding="utf-8") as f:
                    f.write("# 💡 座右銘與金句清單\n\n")
                    f.write("<!-- 這裡可以放你喜歡的座右銘、名言或金句，程式會隨機選取顯示在視窗頂部。 -->\n")
                    f.write("<!-- 格式支援 Markdown 項目符號（- 或 *）或直接換行。 -->\n\n")
                    for m in default_mottos:
                        f.write(f"- {m}\n")
            except Exception as e:
                print(f"無法建立 motto.md: {e}")
                
        mottos = []
        if os.path.exists(motto_file):
            try:
                with open(motto_file, "r", encoding="utf-8") as f:
                    for line in f:
                        line_str = line.strip()
                        if not line_str or line_str.startswith("#") or line_str.startswith("<!--"):
                            continue
                        if line_str.startswith("- ") or line_str.startswith("* "):
                            line_str = line_str[2:].strip()
                        elif line_str.startswith("-") or line_str.startswith("*"):
                            line_str = line_str[1:].strip()
                        elif len(line_str) > 0:
                            import re
                            line_str = re.sub(r'^\d+\.\s*', '', line_str).strip()
                        
                        if line_str:
                            mottos.append(line_str)
            except Exception as e:
                print(f"無法讀取 motto.md: {e}")
                
        if not mottos:
            mottos = default_mottos
        return mottos

    def show_random_motto(self):
        if not hasattr(self, "mottos") or not self.mottos:
            self.mottos = self.load_motto()
        
        if self.mottos:
            import random
            new_motto = random.choice(self.mottos)
            if len(self.mottos) > 1:
                while new_motto == self.current_motto:
                    new_motto = random.choice(self.mottos)
            self.current_motto = new_motto
            if hasattr(self, "motto_label"):
                self.motto_label.config(text=f"💡 {self.current_motto}")

    def on_window_configure(self, event):
        if event.widget == self.root:
            new_wrap = event.width - 40
            if new_wrap > 50:
                self.motto_label.config(wraplength=new_wrap)

    def on_close(self):
        self.save_data()
        self.root.destroy()

    def show_temp_status(self, text, delay=3000):
        self.status_label.config(text=text)
        if hasattr(self, "_status_timer") and self._status_timer:
            self.root.after_cancel(self._status_timer)
        self._status_timer = self.root.after(delay, self.clear_status)

    def clear_status(self):
        if hasattr(self, "_status_timer") and self._status_timer:
            self.root.after_cancel(self._status_timer)
            self._status_timer = None
        self.status_label.config(text="")

if __name__ == "__main__":
    root = tk.Tk()
    app = DesktopTodo(root)
    root.mainloop()