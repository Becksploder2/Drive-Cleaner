import os
import queue
import shutil
import threading
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox
import subprocess

ROOT = Path("C:/")
PROTECTED = {"Windows", "Program Files", "Program Files (x86)", "ProgramData", "Recovery", "System Volume Information", "$Recycle.Bin"}

def human(n):
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024 or unit == "TB":
            return f"{n:,.1f} {unit}"
        n /= 1024

class DriveDetective:
    def __init__(self, root):
        self.root = root
        root.title("Drive Detective — C: Drive Analyzer")
        root.geometry("1120x700")
        self.messages = queue.Queue()
        self.cancel = threading.Event()
        self.running = False
        self.rows = {}
        header = ttk.Frame(root, padding=16)
        header.pack(fill="x")
        ttk.Label(header, text="Drive Detective", font=("Segoe UI", 23, "bold")).pack(anchor="w")
        ttk.Label(header, text="Find your largest folders. Read-only: nothing is deleted.").pack(anchor="w")
        controls = ttk.Frame(root, padding=(16, 4))
        controls.pack(fill="x")
        self.scan_button = ttk.Button(controls, text="Scan C: Drive", command=self.start)
        self.scan_button.pack(side="left", padx=(0, 8))
        ttk.Button(controls, text="Stop Scan", command=self.cancel.set).pack(side="left", padx=(0, 8))
        ttk.Button(controls, text="Show in Explorer", command=self.explore).pack(side="left", padx=(0, 8))
        ttk.Button(controls, text="Uninstall Apps", command=self.uninstall).pack(side="left")
        self.status = tk.StringVar(value="Ready to scan C:. Some protected folders cannot be measured without administrator access.")
        ttk.Label(root, textvariable=self.status, padding=(16, 10)).pack(anchor="w")
        pane = ttk.Frame(root, padding=(16, 0, 16, 8))
        pane.pack(fill="both", expand=True)
        columns = ("size", "folder", "recommendation")
        self.table = ttk.Treeview(pane, columns=columns, show="headings")
        for col, label, width in (("size", "Size", 110), ("folder", "Path", 620), ("recommendation", "Advice", 300)):
            self.table.heading(col, text=label)
            self.table.column(col, width=width, stretch=(col != "size"))
        scroll = ttk.Scrollbar(pane, orient="vertical", command=self.table.yview)
        self.table.configure(yscrollcommand=scroll.set)
        self.table.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        ttk.Label(root, text="Safety: Use Windows Settings to uninstall installed software and games. Never manually remove Windows or Program Files folders.", padding=16).pack(anchor="w")
        self.root.after(120, self.poll)

    def start(self):
        if self.running:
            return
        self.running = True
        self.cancel.clear()
        self.scan_button.configure(state="disabled")
        self.table.delete(*self.table.get_children())
        threading.Thread(target=self.scan, daemon=True).start()

    def scan(self):
        sizes = {}
        errors = 0
        folders = 0
        def onerror(error):
            nonlocal errors
            errors += 1
        try:
            for current, dirs, files in os.walk(ROOT, topdown=True, followlinks=False, onerror=onerror):
                if self.cancel.is_set():
                    break
                dirs[:] = [d for d in dirs if not os.path.islink(os.path.join(current, d))]
                relative = Path(current).relative_to(ROOT).parts
                if relative and relative[0].lower() in ("system volume information", "$recycle.bin"):
                    dirs[:] = []
                    continue
                total = 0
                for filename in files:
                    try:
                        full = os.path.join(current, filename)
                        if not os.path.islink(full):
                            total += os.stat(full, follow_symlinks=False).st_size
                    except OSError:
                        errors += 1
                folder = ROOT
                sizes[str(folder)] = sizes.get(str(folder), 0) + total
                for part in relative:
                    folder /= part
                    key = str(folder)
                    sizes[key] = sizes.get(key, 0) + total
                folders += 1
                if folders % 350 == 0:
                    self.messages.put(("progress", folders))
            results = []
            for path, size in sizes.items():
                parts = Path(path).relative_to(ROOT).parts
                if not parts or len(parts) > 3 or size < 100 * 1024 * 1024:
                    continue
                protected = parts[0].lower() in {name.lower() for name in PROTECTED}
                note = "Protected — use Windows uninstall/storage tools" if protected else "Review files before deleting"
                results.append((size, path, note))
            results.sort(reverse=True)
            self.messages.put(("done", results[:600], errors, self.cancel.is_set()))
        except Exception as exc:
            self.messages.put(("error", str(exc)))

    def poll(self):
        try:
            while True:
                msg = self.messages.get_nowait()
                if msg[0] == "progress":
                    self.status.set(f"Scanning... {msg[1]:,} folders checked")
                elif msg[0] == "done":
                    _, results, errors, stopped = msg
                    for size, path, advice in results:
                        self.table.insert("", "end", values=(human(size), path, advice))
                    self.status.set(f"{'Stopped' if stopped else 'Complete'}: {len(results)} large folders found; {errors} inaccessible entries (sizes may be undercounted).")
                    self.running = False
                    self.scan_button.configure(state="normal")
                elif msg[0] == "error":
                    self.status.set("Scan failed: " + msg[1])
                    self.running = False
                    self.scan_button.configure(state="normal")
        except queue.Empty:
            pass
        self.root.after(120, self.poll)

    def explore(self):
        selection = self.table.selection()
        if not selection:
            messagebox.showinfo("Select a folder", "Choose a folder from the results first.")
            return
        path = self.table.item(selection[0], "values")[1]
        try:
            os.startfile(path)
        except OSError as exc:
            messagebox.showerror("Cannot open folder", str(exc))

    def uninstall(self):
        try:
            os.startfile("ms-settings:appsfeatures")
        except OSError as exc:
            messagebox.showerror("Cannot open Settings", str(exc))

if __name__ == "__main__":
    root = tk.Tk()
    DriveDetective(root)
    root.mainloop()
