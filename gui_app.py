from pathlib import Path
import os
import queue
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import messagebox, ttk

import yaml


BASE_DIR = Path(__file__).resolve().parent


class PinterestAutomationGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Pinterest Automation")
        self.root.geometry("1100x760")
        self.root.minsize(900, 650)

        self.process = None
        self.output_queue = queue.Queue()
        self._closing = False

        self.affiliate_categories = []
        self.tip_categories = []
        self.content_slot_vars = []
        self._load_categories()

        self._build_ui()
        self._poll_output()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _load_categories(self):
        try:
            with open(BASE_DIR / "config.yaml", "r", encoding="utf-8") as f:
                cfg = yaml.safe_load(f) or {}
            self.affiliate_categories = [
                item.get("name", "")
                for item in cfg.get("categories", [])
                if item.get("enabled", True) and item.get("name")
            ]
        except Exception:
            self.affiliate_categories = []

        try:
            with open(BASE_DIR / "tip_config.yaml", "r", encoding="utf-8") as f:
                cfg = yaml.safe_load(f) or {}
            self.tip_categories = [
                item
                for item in cfg.get("tip_categories", [])
                if item.get("name")
            ]
        except Exception:
            self.tip_categories = []

    def _build_ui(self):
        style = ttk.Style()
        try:
            style.theme_use("vista")
        except Exception:
            pass

        outer = ttk.Frame(self.root, padding=14)
        outer.pack(fill="both", expand=True)

        header = ttk.Frame(outer)
        header.pack(fill="x")

        ttk.Label(
            header,
            text="Pinterest Automation",
            font=("Segoe UI", 20, "bold"),
        ).pack(side="left")

        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(
            header,
            textvariable=self.status_var,
            font=("Segoe UI", 10),
        ).pack(side="right")

        controls = ttk.Frame(outer)
        controls.pack(fill="x", pady=(12, 8))

        self.dry_run_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            controls,
            text="Dry run (do not publish)",
            variable=self.dry_run_var,
        ).pack(side="left")

        ttk.Button(
            controls,
            text="Pinterest Login",
            command=self.run_login,
        ).pack(side="left", padx=(12, 0))

        ttk.Button(
            controls,
            text="Open Output Folder",
            command=self.open_output_folder,
        ).pack(side="left", padx=(8, 0))

        ttk.Button(
            controls,
            text="Open README",
            command=self.open_readme,
        ).pack(side="left", padx=(8, 0))

        notebook = ttk.Notebook(outer)
        notebook.pack(fill="x", pady=(4, 12))

        affiliate_tab = ttk.Frame(notebook, padding=14)
        content_tab = ttk.Frame(notebook, padding=14)
        notebook.add(affiliate_tab, text="Affiliate Pins")
        notebook.add(content_tab, text="Non-Affiliate / AI Content")

        self._build_affiliate_tab(affiliate_tab)
        self._build_content_tab(content_tab)

        action_bar = ttk.Frame(outer)
        action_bar.pack(fill="x", pady=(0, 8))

        self.continue_button = ttk.Button(
            action_bar,
            text="Continue / Close Dry-Run Browser",
            command=self.send_enter,
        )
        self.continue_button.pack(side="left")

        self.stop_button = ttk.Button(
            action_bar,
            text="Stop Current Run",
            command=self.stop_process,
        )
        self.stop_button.pack(side="left", padx=(8, 0))

        ttk.Button(
            action_bar,
            text="Clear Log",
            command=self.clear_log,
        ).pack(side="right")

        log_frame = ttk.LabelFrame(outer, text="Live Output", padding=8)
        log_frame.pack(fill="both", expand=True)

        self.log = tk.Text(
            log_frame,
            wrap="word",
            font=("Consolas", 10),
            state="disabled",
        )
        scrollbar = ttk.Scrollbar(
            log_frame,
            orient="vertical",
            command=self.log.yview,
        )
        self.log.configure(yscrollcommand=scrollbar.set)

        self.log.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self._append_log(
            "Ready. Choose an action above.\n"
            "Dry run is ON by default for safety.\n\n"
        )

    def _build_affiliate_tab(self, parent):
        grid = ttk.Frame(parent)
        grid.pack(fill="x")

        ttk.Label(grid, text="Vertical:").grid(
            row=0, column=0, sticky="w", padx=(0, 8), pady=6
        )
        self.affiliate_vertical = tk.StringVar(value="3d")
        vertical_box = ttk.Combobox(
            grid,
            textvariable=self.affiliate_vertical,
            values=["3d", "honda"],
            state="readonly",
            width=18,
        )
        vertical_box.grid(row=0, column=1, sticky="w", pady=6)
        vertical_box.bind("<<ComboboxSelected>>", lambda _e: self._refresh_affiliate_categories())

        ttk.Label(grid, text="Specific category:").grid(
            row=1, column=0, sticky="w", padx=(0, 8), pady=6
        )
        self.affiliate_category = tk.StringVar(value="All categories in vertical")
        self.affiliate_category_box = ttk.Combobox(
            grid,
            textvariable=self.affiliate_category,
            state="readonly",
            width=46,
        )
        self.affiliate_category_box.grid(
            row=1, column=1, columnspan=2, sticky="w", pady=6
        )

        ttk.Label(grid, text="Number of Pins:").grid(
            row=2, column=0, sticky="w", padx=(0, 8), pady=6
        )
        self.affiliate_count = tk.IntVar(value=1)
        ttk.Spinbox(
            grid,
            from_=1,
            to=20,
            textvariable=self.affiliate_count,
            width=8,
        ).grid(row=2, column=1, sticky="w", pady=6)

        ttk.Button(
            grid,
            text="Run Affiliate Pins",
            command=self.run_affiliate,
        ).grid(row=3, column=0, columnspan=2, sticky="w", pady=(14, 4))

        ttk.Label(
            grid,
            text=(
                "Uses the existing eBay ranking, affiliate-link, image, board, "
                "cooldown, and Pinterest publishing pipeline."
            ),
            wraplength=780,
        ).grid(row=4, column=0, columnspan=4, sticky="w", pady=(4, 0))

        self._refresh_affiliate_categories()

    def _build_content_tab(self, parent):
        grid = ttk.Frame(parent)
        grid.pack(fill="x")

        ttk.Label(grid, text="Vertical:").grid(
            row=0, column=0, sticky="w", padx=(0, 8), pady=6
        )
        self.content_vertical = tk.StringVar(value="3d")
        vertical_box = ttk.Combobox(
            grid,
            textvariable=self.content_vertical,
            values=["3d", "honda"],
            state="readonly",
            width=18,
        )
        vertical_box.grid(row=0, column=1, sticky="w", pady=6)
        vertical_box.bind(
            "<<ComboboxSelected>>",
            lambda _e: self._refresh_content_categories(),
        )

        ttk.Label(grid, text="Specific category:").grid(
            row=1, column=0, sticky="w", padx=(0, 8), pady=6
        )
        self.content_category = tk.StringVar(value="Automatic")
        self.content_category_box = ttk.Combobox(
            grid,
            textvariable=self.content_category,
            state="readonly",
            width=46,
        )
        self.content_category_box.grid(
            row=1, column=1, columnspan=3, sticky="w", pady=6
        )

        ttk.Label(grid, text="Number of Pins:").grid(
            row=2, column=0, sticky="w", padx=(0, 8), pady=6
        )
        self.content_count = tk.IntVar(value=1)
        count_spin = ttk.Spinbox(
            grid,
            from_=1,
            to=20,
            textvariable=self.content_count,
            width=8,
            command=self._rebuild_content_slots,
        )
        count_spin.grid(row=2, column=1, sticky="w", pady=6)
        count_spin.bind("<KeyRelease>", lambda _e: self._rebuild_content_slots())
        count_spin.bind("<FocusOut>", lambda _e: self._rebuild_content_slots())

        ttk.Label(
            grid,
            text="Choose each Pin type. Random picks Tip, Quote, Question, or Quiz.",
        ).grid(row=3, column=0, columnspan=4, sticky="w", pady=(8, 4))

        self.content_slots_frame = ttk.LabelFrame(
            grid,
            text="Pin Plan",
            padding=8,
        )
        self.content_slots_frame.grid(
            row=4,
            column=0,
            columnspan=4,
            sticky="ew",
            pady=(4, 8),
        )

        self.static_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            grid,
            text="Use prewritten static content instead of AI",
            variable=self.static_var,
        ).grid(row=5, column=0, columnspan=3, sticky="w", pady=6)

        ttk.Button(
            grid,
            text="Generate & Run Content Batch",
            command=self.run_content,
        ).grid(row=6, column=0, columnspan=2, sticky="w", pady=(12, 4))

        ttk.Label(
            grid,
            text=(
                "The batch avoids duplicate cards, uses recent history for AI "
                "deduplication, and prefers different matching categories within "
                "the same run when possible."
            ),
            wraplength=780,
        ).grid(row=7, column=0, columnspan=4, sticky="w", pady=(4, 0))

        self._refresh_content_categories()
        self._rebuild_content_slots()

    def _rebuild_content_slots(self):
        try:
            count = max(1, min(int(self.content_count.get()), 20))
        except Exception:
            count = 1

        previous = [var.get() for var in self.content_slot_vars]

        for child in self.content_slots_frame.winfo_children():
            child.destroy()

        self.content_slot_vars = []
        options = ["Random", "Tip", "Quote", "Question", "Quiz"]

        for index in range(count):
            value = previous[index] if index < len(previous) else "Random"
            var = tk.StringVar(value=value)
            self.content_slot_vars.append(var)

            row = index // 4
            column = (index % 4) * 2

            ttk.Label(
                self.content_slots_frame,
                text=f"Pin {index + 1}:",
            ).grid(
                row=row,
                column=column,
                sticky="e",
                padx=(6, 4),
                pady=4,
            )

            ttk.Combobox(
                self.content_slots_frame,
                textvariable=var,
                values=options,
                state="readonly",
                width=11,
            ).grid(
                row=row,
                column=column + 1,
                sticky="w",
                padx=(0, 10),
                pady=4,
            )

    def _refresh_affiliate_categories(self):
        vertical = self.affiliate_vertical.get()
        prefix = "3D Printing" if vertical == "3d" else "Honda"
        matches = [
            name for name in self.affiliate_categories
            if name.startswith(prefix)
        ]
        values = ["All categories in vertical"] + matches
        self.affiliate_category_box["values"] = values
        if self.affiliate_category.get() not in values:
            self.affiliate_category.set(values[0])

    def _refresh_content_categories(self):
        vertical = self.content_vertical.get()

        matches = []
        for category in self.tip_categories:
            if category.get("vertical") != vertical:
                continue
            matches.append(category.get("name"))

        values = ["Automatic"] + matches
        self.content_category_box["values"] = values
        if self.content_category.get() not in values:
            self.content_category.set(values[0])

    def _python_executable(self):
        executable = Path(sys.executable)
        if executable.name.lower() == "pythonw.exe":
            candidate = executable.with_name("python.exe")
            if candidate.exists():
                return str(candidate)
        return str(executable)

    def _child_env(self):
        env = os.environ.copy()
        env["PINTEREST_DRY_RUN"] = (
            "true" if self.dry_run_var.get() else "false"
        )
        env["PYTHONUNBUFFERED"] = "1"
        return env

    def _confirm_live_mode(self):
        if self.dry_run_var.get():
            return True
        return messagebox.askyesno(
            "Live Pinterest Publishing",
            "Dry run is OFF. This run can publish Pins to Pinterest.\n\nContinue?",
            icon="warning",
        )

    def run_affiliate(self):
        if not self._confirm_live_mode():
            return

        try:
            count = int(self.affiliate_count.get())
        except Exception:
            messagebox.showerror("Invalid Pin count", "Pin count must be a whole number.")
            return

        if count < 1:
            messagebox.showerror("Invalid Pin count", "Pin count must be at least 1.")
            return

        command = [
            self._python_executable(),
            "run_best_pin.py",
            "--vertical",
            self.affiliate_vertical.get(),
            "--count",
            str(count),
        ]

        category = self.affiliate_category.get()
        if category and category != "All categories in vertical":
            command.extend(["--category", category])

        self._start_process(command, "Affiliate Pins")

    def run_content(self):
        if not self._confirm_live_mode():
            return

        try:
            count = int(self.content_count.get())
        except Exception:
            messagebox.showerror(
                "Invalid Pin count",
                "Pin count must be a whole number.",
            )
            return

        if count < 1 or count > 20:
            messagebox.showerror(
                "Invalid Pin count",
                "Pin count must be between 1 and 20.",
            )
            return

        self._rebuild_content_slots()

        if len(self.content_slot_vars) != count:
            messagebox.showerror(
                "Pin plan error",
                "Could not build the requested Pin plan.",
            )
            return

        command = [
            self._python_executable(),
            "run_tip_pin.py",
            "--vertical",
            self.content_vertical.get(),
            "--count",
            str(count),
        ]

        type_map = {
            "Random": "random",
            "Tip": "tip",
            "Quote": "quote",
            "Question": "question",
            "Quiz": "quiz",
        }

        for slot_var in self.content_slot_vars:
            command.extend(
                ["--pin-type", type_map.get(slot_var.get(), "random")]
            )

        category = self.content_category.get()
        if category and category != "Automatic":
            command.extend(["--category", category])

        if self.static_var.get():
            command.append("--static")

        self._start_process(command, "Non-Affiliate Content Batch")

    def run_login(self):
        command = [self._python_executable(), "pinterest_login.py"]
        self._start_process(command, "Pinterest Login")

    def _start_process(self, command, label):
        if self.process and self.process.poll() is None:
            messagebox.showwarning(
                "Already running",
                "Another automation process is already running.",
            )
            return

        self._append_log("\n" + "=" * 72 + "\n")
        self._append_log(f"{label}\n")
        self._append_log("Command: " + " ".join(command) + "\n")
        self._append_log(
            "Mode: "
            + ("DRY RUN" if self.dry_run_var.get() else "LIVE PUBLISH")
            + "\n"
        )
        self._append_log("=" * 72 + "\n\n")

        self.status_var.set(f"Running: {label}")

        threading.Thread(
            target=self._run_process_worker,
            args=(command, label),
            daemon=True,
        ).start()

    def _run_process_worker(self, command, label):
        try:
            creationflags = 0
            if os.name == "nt" and hasattr(subprocess, "CREATE_NO_WINDOW"):
                creationflags = subprocess.CREATE_NO_WINDOW

            self.process = subprocess.Popen(
                command,
                cwd=str(BASE_DIR),
                env=self._child_env(),
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
                creationflags=creationflags,
            )

            if self.process.stdout:
                for line in self.process.stdout:
                    self.output_queue.put(("log", line))

            return_code = self.process.wait()
            if return_code == 0:
                self.output_queue.put(
                    ("status", f"Finished: {label}")
                )
                self.output_queue.put(
                    ("log", f"\n{label} finished successfully.\n")
                )
            else:
                self.output_queue.put(
                    ("status", f"Stopped / failed: {label}")
                )
                self.output_queue.put(
                    ("log", f"\nProcess exited with code {return_code}.\n")
                )

        except Exception as exc:
            self.output_queue.put(("status", "Error"))
            self.output_queue.put(
                ("log", f"\nERROR starting process: {exc}\n")
            )
        finally:
            self.process = None

    def send_enter(self):
        process = self.process
        if not process or process.poll() is not None:
            self._append_log("No running process is waiting for input.\n")
            return

        try:
            if process.stdin:
                process.stdin.write("\n")
                process.stdin.flush()
                self._append_log(
                    "Sent ENTER to the running automation.\n"
                )
        except Exception as exc:
            self._append_log(f"Could not send ENTER: {exc}\n")

    def stop_process(self):
        process = self.process
        if not process or process.poll() is not None:
            self._append_log("No automation process is currently running.\n")
            return

        if not messagebox.askyesno(
            "Stop automation",
            "Stop the currently running automation process?",
        ):
            return

        try:
            process.terminate()
            self._append_log("Stop request sent.\n")
            self.status_var.set("Stopping...")
        except Exception as exc:
            self._append_log(f"Could not stop process: {exc}\n")

    def _poll_output(self):
        try:
            while True:
                kind, value = self.output_queue.get_nowait()
                if kind == "log":
                    self._append_log(value)
                elif kind == "status":
                    self.status_var.set(value)
        except queue.Empty:
            pass

        if not self._closing:
            self.root.after(100, self._poll_output)

    def _append_log(self, text):
        self.log.configure(state="normal")
        self.log.insert("end", text)
        self.log.see("end")
        self.log.configure(state="disabled")

    def clear_log(self):
        self.log.configure(state="normal")
        self.log.delete("1.0", "end")
        self.log.configure(state="disabled")

    def open_output_folder(self):
        path = BASE_DIR / "output"
        path.mkdir(parents=True, exist_ok=True)
        try:
            os.startfile(str(path))
        except Exception as exc:
            messagebox.showerror("Could not open folder", str(exc))

    def open_readme(self):
        path = BASE_DIR / "README.md"
        try:
            os.startfile(str(path))
        except Exception as exc:
            messagebox.showerror("Could not open README", str(exc))

    def _on_close(self):
        if self.process and self.process.poll() is None:
            if not messagebox.askyesno(
                "Automation is running",
                "An automation process is still running. Stop it and close the app?",
            ):
                return
            try:
                self.process.terminate()
            except Exception:
                pass

        self._closing = True
        self.root.destroy()


def main():
    root = tk.Tk()
    PinterestAutomationGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
