import tkinter as tk
from tkinter import messagebox
import winsound
import threading


class PomodoroTimer:
    MODES = {
        "work":        {"label": "专注",   "minutes": 25, "color": "#E74C3C"},
        "short_break": {"label": "短休息", "minutes": 5,  "color": "#27AE60"},
        "long_break":  {"label": "长休息", "minutes": 15, "color": "#2980B9"},
    }
    LONG_BREAK_INTERVAL = 4  # every N pomodoros → long break

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🍅 番茄钟")
        self.root.geometry("400x540")
        self.root.resizable(False, False)
        self.root.configure(bg="#1E1E2E")

        self.current_mode = "work"
        self.is_running = False
        self.after_id = None
        self.pomodoro_count = 0
        self._reset_time()

        self._build_ui()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.root.mainloop()

    # ── UI ──────────────────────────────────────────────────────────────────

    def _build_ui(self):
        C = self.MODES[self.current_mode]["color"]

        # ── 标题
        tk.Label(self.root, text="🍅 番茄钟",
                 font=("Microsoft YaHei UI", 18, "bold"),
                 bg="#1E1E2E", fg="#CDD6F4").pack(pady=(22, 8))

        # ── 模式切换按钮
        tab_frame = tk.Frame(self.root, bg="#313244", bd=0)
        tab_frame.pack(padx=40, pady=4, fill="x")

        self._mode_btns = {}
        for mode, cfg in self.MODES.items():
            btn = tk.Button(
                tab_frame, text=cfg["label"],
                font=("Microsoft YaHei UI", 10),
                relief="flat", cursor="hand2", bd=0,
                padx=14, pady=6,
                command=lambda m=mode: self._switch_mode(m),
            )
            btn.pack(side="left", expand=True, fill="x", padx=2, pady=2)
            self._mode_btns[mode] = btn
        self._refresh_tab_styles()

        # ── 圆形倒计时画布
        self.canvas = tk.Canvas(self.root, width=300, height=300,
                                bg="#1E1E2E", highlightthickness=0)
        self.canvas.pack(pady=16)

        r = 130
        cx, cy = 150, 150
        self._arc_bg = self.canvas.create_oval(
            cx - r, cy - r, cx + r, cy + r,
            outline="#313244", width=12, fill="#181825"
        )
        self._arc = self.canvas.create_arc(
            cx - r, cy - r, cx + r, cy + r,
            start=90, extent=-360,
            outline=C, width=12, style="arc"
        )
        self._timer_txt = self.canvas.create_text(
            cx, cy - 16, text="25:00",
            font=("Courier New", 46, "bold"), fill="#CDD6F4"
        )
        self._mode_txt = self.canvas.create_text(
            cx, cy + 38, text="专注时间",
            font=("Microsoft YaHei UI", 13), fill="#6C7086"
        )

        # ── 控制按钮
        ctrl = tk.Frame(self.root, bg="#1E1E2E")
        ctrl.pack(pady=6)

        self._start_btn = tk.Button(
            ctrl, text="▶  开始",
            font=("Microsoft YaHei UI", 13, "bold"),
            bg=C, fg="white", activebackground=C,
            relief="flat", cursor="hand2",
            padx=28, pady=10, bd=0,
            command=self._toggle,
        )
        self._start_btn.pack(side="left", padx=10)

        self._reset_btn = tk.Button(
            ctrl, text="↺  重置",
            font=("Microsoft YaHei UI", 13),
            bg="#313244", fg="#CDD6F4", activebackground="#45475A",
            relief="flat", cursor="hand2",
            padx=18, pady=10, bd=0,
            command=self._reset,
        )
        self._reset_btn.pack(side="left", padx=10)

        # ── 番茄计数
        bottom = tk.Frame(self.root, bg="#1E1E2E")
        bottom.pack(pady=14)

        tk.Label(bottom, text="今日完成：",
                 font=("Microsoft YaHei UI", 11),
                 bg="#1E1E2E", fg="#6C7086").pack(side="left")

        self._count_lbl = tk.Label(bottom, text="0 个番茄",
                                   font=("Microsoft YaHei UI", 11, "bold"),
                                   bg="#1E1E2E", fg="#CDD6F4")
        self._count_lbl.pack(side="left")

        self._dots_lbl = tk.Label(bottom, text="",
                                  font=("", 14),
                                  bg="#1E1E2E", fg="#E74C3C")
        self._dots_lbl.pack(side="left", padx=6)

        self._refresh_display()

    # ── 核心逻辑 ─────────────────────────────────────────────────────────────

    def _reset_time(self):
        self.time_left = self.MODES[self.current_mode]["minutes"] * 60

    def _switch_mode(self, mode, auto=False):
        self._cancel_tick()
        self.is_running = False
        self.current_mode = mode
        self._reset_time()
        color = self.MODES[mode]["color"]
        self._start_btn.config(text="▶  开始", bg=color, activebackground=color)
        self.canvas.itemconfig(self._arc, outline=color)
        self._refresh_tab_styles()
        self._refresh_display()

    def _toggle(self):
        if self.is_running:
            self._cancel_tick()
            self.is_running = False
            self._start_btn.config(text="▶  开始")
        else:
            self.is_running = True
            self._start_btn.config(text="⏸  暂停")
            self._tick()

    def _reset(self):
        self._cancel_tick()
        self.is_running = False
        self._reset_time()
        self._start_btn.config(text="▶  开始")
        self._refresh_display()

    def _tick(self):
        if not self.is_running:
            return
        if self.time_left > 0:
            self.time_left -= 1
            self._refresh_display()
            self.after_id = self.root.after(1000, self._tick)
        else:
            self._finish()

    def _cancel_tick(self):
        if self.after_id:
            self.root.after_cancel(self.after_id)
            self.after_id = None

    def _finish(self):
        self.is_running = False
        self._start_btn.config(text="▶  开始")

        if self.current_mode == "work":
            self.pomodoro_count += 1
            self._count_lbl.config(text=f"{self.pomodoro_count} 个番茄")
            dots = "🍅" * (self.pomodoro_count % self.LONG_BREAK_INTERVAL or self.LONG_BREAK_INTERVAL)
            self._dots_lbl.config(text=dots)
            self._beep_async(finish=True)

            if self.pomodoro_count % self.LONG_BREAK_INTERVAL == 0:
                next_mode = "long_break"
                msg = f"完成了 {self.LONG_BREAK_INTERVAL} 个番茄！\n休息 15 分钟吧 ☕"
            else:
                next_mode = "short_break"
                msg = "专注结束！\n休息 5 分钟吧 😊"
        else:
            next_mode = "work"
            msg = "休息结束，继续加油！💪"
            self._beep_async(finish=False)

        self._switch_mode(next_mode, auto=True)
        self._notify(msg)

    # ── 刷新 UI ──────────────────────────────────────────────────────────────

    def _refresh_display(self):
        m, s = divmod(self.time_left, 60)
        self.canvas.itemconfig(self._timer_txt, text=f"{m:02d}:{s:02d}")

        total = self.MODES[self.current_mode]["minutes"] * 60
        fraction = self.time_left / total if total else 0
        self.canvas.itemconfig(self._arc, extent=-(fraction * 360))

        labels = {"work": "专注时间", "short_break": "短休息", "long_break": "长休息"}
        self.canvas.itemconfig(self._mode_txt, text=labels[self.current_mode])

    def _refresh_tab_styles(self):
        for mode, btn in self._mode_btns.items():
            if mode == self.current_mode:
                c = self.MODES[mode]["color"]
                btn.config(bg=c, fg="white", activebackground=c)
            else:
                btn.config(bg="#313244", fg="#6C7086", activebackground="#45475A")

    # ── 通知 & 提示音 ─────────────────────────────────────────────────────────

    def _notify(self, msg):
        popup = tk.Toplevel(self.root)
        popup.title("番茄钟提醒")
        popup.geometry("300x150")
        popup.configure(bg="#1E1E2E")
        popup.resizable(False, False)
        popup.grab_set()
        popup.update_idletasks()
        x = self.root.winfo_x() + self.root.winfo_width() // 2 - 150
        y = self.root.winfo_y() + self.root.winfo_height() // 2 - 75
        popup.geometry(f"+{x}+{y}")

        tk.Label(popup, text=msg, font=("Microsoft YaHei UI", 12),
                 bg="#1E1E2E", fg="#CDD6F4",
                 justify="center", wraplength=260).pack(pady=30)
        tk.Button(popup, text="好的", font=("Microsoft YaHei UI", 11),
                  bg=self.MODES[self.current_mode]["color"], fg="white",
                  relief="flat", cursor="hand2", padx=24, pady=6, bd=0,
                  command=popup.destroy).pack()

    def _beep_async(self, finish: bool):
        freq, dur = (1000, 400) if finish else (700, 300)
        threading.Thread(
            target=lambda: winsound.Beep(freq, dur),
            daemon=True
        ).start()

    def _on_close(self):
        self._cancel_tick()
        self.root.destroy()


if __name__ == "__main__":
    PomodoroTimer()
