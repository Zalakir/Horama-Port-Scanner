import csv
import os
import queue
import socket
import threading
import time
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

try:
    import yaml
except ImportError:
    yaml = None

THEME_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "theme.yaml")

# Used for any value missing from theme.yaml, or when the file/PyYAML is unavailable.
DEFAULT_THEME = {
    "colors": {
        "background": "#0f172a",
        "surface": "#1e293b",
        "border": "#334155",
        "text": "#e2e8f0",
        "muted_text": "#94a3b8",
        "accent": "#38bdf8",
        "accent_text": "#0f172a",
        "accent_hover": "#7dd3fc",
        "disabled": "#475569",
        "results_background": "#020617",
        "results_text": "#4ade80",
    },
    "fonts": {
        "family": "Segoe UI",
        "size": 10,
        "title_size": 20,
        "results_family": "Consolas",
        "results_size": 10,
    },
}


def load_theme():
    # Merge theme.yaml over the defaults so a partial file still works.
    theme = {section: dict(values) for section, values in DEFAULT_THEME.items()}
    if yaml is None or not os.path.exists(THEME_FILE):
        return theme
    try:
        with open(THEME_FILE, encoding="utf-8") as theme_file:
            custom = yaml.safe_load(theme_file) or {}
        for section in theme:
            if isinstance(custom.get(section), dict):
                theme[section].update(custom[section])
    except (OSError, yaml.YAMLError):
        pass
    return theme


class PortScannerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Horama Port Scanner")
        self.root.geometry("760x560")
        self.root.minsize(620, 440)
        self.theme = load_theme()
        self._apply_theme()

        # Worker threads report results through a queue so only the GUI thread
        # updates Tkinter widgets.
        self.events = queue.Queue()
        # This event lets every worker stop promptly when the user cancels.
        self.cancel_event = threading.Event()
        self.is_scanning = False
        self.total_ports = 0
        self.completed_ports = 0
        self.open_ports = []
        # Details of the last finished scan, used when exporting to CSV.
        self.scan_host = ""
        self.scan_target = ""

        # Build the window and periodically check for messages from scan workers.
        self._build_ui()
        self.root.after(100, self._process_events)

    def _apply_theme(self):
        # The "clam" theme is the most customizable built-in ttk theme.
        colors, fonts = self.theme["colors"], self.theme["fonts"]
        base_font = (fonts["family"], fonts["size"])
        style = ttk.Style(self.root)
        style.theme_use("clam")
        self.root.configure(background=colors["background"])

        style.configure(
            ".",
            background=colors["background"],
            foreground=colors["text"],
            font=base_font,
            bordercolor=colors["border"],
            lightcolor=colors["border"],
            darkcolor=colors["border"],
            troughcolor=colors["surface"],
        )
        style.configure("TLabelframe", background=colors["background"])
        style.configure(
            "TLabelframe.Label",
            background=colors["background"],
            foreground=colors["accent"],
            font=(fonts["family"], fonts["size"], "bold"),
        )
        style.configure(
            "Title.TLabel",
            foreground=colors["accent"],
            font=(fonts["family"], fonts["title_size"], "bold"),
        )
        style.configure("Subtitle.TLabel", foreground=colors["muted_text"])
        for widget in ("TEntry", "TSpinbox"):
            style.configure(
                widget,
                fieldbackground=colors["surface"],
                foreground=colors["text"],
                insertcolor=colors["text"],
                arrowcolor=colors["text"],
            )
        style.map("TEntry", fieldbackground=[("disabled", colors["background"])])
        style.configure(
            "TButton",
            background=colors["surface"],
            foreground=colors["text"],
            padding=(14, 6),
            borderwidth=1,
        )
        style.map(
            "TButton",
            background=[("disabled", colors["background"]), ("active", colors["border"])],
            foreground=[("disabled", colors["disabled"])],
        )
        style.configure(
            "Accent.TButton",
            background=colors["accent"],
            foreground=colors["accent_text"],
            font=(fonts["family"], fonts["size"], "bold"),
        )
        style.map(
            "Accent.TButton",
            background=[
                ("disabled", colors["disabled"]),
                ("active", colors["accent_hover"]),
            ],
            foreground=[("disabled", colors["background"])],
        )
        style.configure(
            "Horizontal.TProgressbar",
            background=colors["accent"],
            troughcolor=colors["surface"],
        )
        style.configure(
            "Vertical.TScrollbar",
            background=colors["border"],
            troughcolor=colors["results_background"],
            arrowcolor=colors["text"],
        )

    def _build_ui(self):
        # The settings, results, and progress bar expand with the window.
        container = ttk.Frame(self.root, padding=20)
        container.pack(fill=tk.BOTH, expand=True)
        container.columnconfigure(0, weight=1)
        container.rowconfigure(4, weight=1)

        ttk.Label(
            container, text="HORAMA PORT SCANNER", style="Title.TLabel"
        ).grid(row=0, column=0, sticky="w")
        ttk.Label(
            container,
            text="Scan a host for reachable TCP ports.",
            style="Subtitle.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(2, 16))

        settings = ttk.LabelFrame(container, text="Scan settings", padding=12)
        settings.grid(row=2, column=0, sticky="ew")
        settings.columnconfigure(1, weight=1)

        ttk.Label(settings, text="Host or IPv4 address").grid(
            row=0, column=0, sticky="w", padx=(0, 10), pady=4
        )
        self.host_entry = ttk.Entry(settings)
        self.host_entry.grid(row=0, column=1, columnspan=5, sticky="ew", pady=4)
        self.host_entry.insert(0, "127.0.0.1")

        ttk.Label(settings, text="Port range").grid(
            row=1, column=0, sticky="w", padx=(0, 10), pady=4
        )
        self.start_port = tk.StringVar(value="1")
        self.end_port = tk.StringVar(value="65535")
        ttk.Spinbox(
            settings, from_=1, to=65535, textvariable=self.start_port, width=9
        ).grid(row=1, column=1, sticky="w", pady=4)
        ttk.Label(settings, text="to").grid(row=1, column=2, padx=8)
        ttk.Spinbox(
            settings, from_=1, to=65535, textvariable=self.end_port, width=9
        ).grid(row=1, column=3, sticky="w", pady=4)

        ttk.Label(settings, text="Workers").grid(
            row=1, column=4, sticky="e", padx=(20, 8), pady=4
        )
        self.worker_count = tk.StringVar(value="2000")
        ttk.Spinbox(
            settings, from_=1, to=2000, textvariable=self.worker_count, width=7
        ).grid(row=1, column=5, sticky="w", pady=4)

        buttons = ttk.Frame(container)
        buttons.grid(row=3, column=0, sticky="ew", pady=(14, 8))
        self.scan_button = ttk.Button(
            buttons, text="Start scan", command=self.start_scan, style="Accent.TButton"
        )
        self.scan_button.pack(side=tk.LEFT)
        self.cancel_button = ttk.Button(
            buttons, text="Cancel", command=self.cancel_scan, state=tk.DISABLED
        )
        self.cancel_button.pack(side=tk.LEFT, padx=(8, 0))
        ttk.Button(buttons, text="Clear results", command=self.clear_results).pack(
            side=tk.RIGHT
        )
        self.export_button = ttk.Button(
            buttons, text="Export CSV", command=self.export_csv, state=tk.DISABLED
        )
        self.export_button.pack(side=tk.RIGHT, padx=(0, 8))

        output = ttk.LabelFrame(container, text="Results", padding=10)
        output.grid(row=4, column=0, sticky="nsew")
        output.columnconfigure(0, weight=1)
        output.rowconfigure(1, weight=1)
        self.status = tk.StringVar(value="Ready")
        ttk.Label(output, textvariable=self.status).grid(
            row=0, column=0, sticky="w", pady=(0, 6)
        )

        text_frame = ttk.Frame(output)
        text_frame.grid(row=1, column=0, sticky="nsew")
        text_frame.columnconfigure(0, weight=1)
        text_frame.rowconfigure(0, weight=1)
        self.results = tk.Text(
            text_frame,
            height=12,
            wrap=tk.NONE,
            state=tk.DISABLED,
            font=(
                self.theme["fonts"]["results_family"],
                self.theme["fonts"]["results_size"],
            ),
            background=self.theme["colors"]["results_background"],
            foreground=self.theme["colors"]["results_text"],
            insertbackground=self.theme["colors"]["results_text"],
            relief=tk.FLAT,
            padx=8,
            pady=6,
        )
        self.results.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(
            text_frame, orient=tk.VERTICAL, command=self.results.yview
        )
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.results.configure(yscrollcommand=scrollbar.set)

        self.progress = ttk.Progressbar(container, mode="determinate")
        self.progress.grid(row=5, column=0, sticky="ew", pady=(10, 0))

    def start_scan(self):
        # Read and validate settings before starting any background work.
        host = self.host_entry.get().strip()
        try:
            first_port = int(self.start_port.get())
            last_port = int(self.end_port.get())
            workers = int(self.worker_count.get())
        except ValueError:
            messagebox.showerror(
                "Invalid scan settings",
                "Ports and worker count must be whole numbers.",
                parent=self.root,
            )
            return

        if not host:
            messagebox.showerror(
                "Invalid scan settings", "Enter a host or IPv4 address.", parent=self.root
            )
            return
        if not (1 <= first_port <= last_port <= 65535):
            messagebox.showerror(
                "Invalid scan settings",
                "Enter a port range between 1 and 65535, with the start no greater "
                "than the end.",
                parent=self.root,
            )
            return
        if not 1 <= workers <= 2000:
            messagebox.showerror(
                "Invalid scan settings",
                "Worker count must be between 1 and 2000.",
                parent=self.root,
            )
            return

        self.is_scanning = True
        self.cancel_event.clear()
        self.total_ports = last_port - first_port + 1
        self.completed_ports = 0
        self.open_ports = []
        self.scan_host = host
        self.scan_target = ""
        self.progress.configure(maximum=self.total_ports, value=0)
        self.scan_button.configure(state=tk.DISABLED)
        self.export_button.configure(state=tk.DISABLED)
        self.cancel_button.configure(state=tk.NORMAL)
        self.host_entry.configure(state=tk.DISABLED)
        self.status.set("Resolving host and starting scan...")
        self._set_results("")

        # Keep network operations off Tkinter's main thread so the window stays
        # responsive while ports are being checked.
        scan_thread = threading.Thread(
            target=self._run_scan,
            args=(host, first_port, last_port, workers),
            daemon=True,
        )
        scan_thread.start()

    def _run_scan(self, host, first_port, last_port, workers):
        # Resolve names such as localhost once, then connect to the resolved IPv4.
        started = time.monotonic()
        try:
            target = socket.gethostbyname(host)
        except (socket.gaierror, UnicodeError) as error:
            self.events.put(("finished", (None, 0, False, str(error))))
            return

        next_port = first_port
        # Workers share the next port and completed count, so protect updates
        # with a lock to ensure each port is assigned once.
        state_lock = threading.Lock()
        progress_interval = max(1, self.total_ports // 100)

        def scan_worker():
            nonlocal next_port
            # Each worker claims one port at a time until the range is exhausted
            # or cancellation is requested.
            while not self.cancel_event.is_set():
                with state_lock:
                    if next_port > last_port:
                        return
                    port = next_port
                    next_port += 1

                try:
                    # A successful TCP connection means this port is accepting
                    # connections; closed or filtered ports time out or fail.
                    with socket.create_connection((target, port), timeout=0.5):
                        self.events.put(("open", port))
                except OSError:
                    pass

                # Send occasional progress updates rather than queuing one for
                # every attempted port.
                with state_lock:
                    self.completed_ports += 1
                    completed = self.completed_ports
                if completed % progress_interval == 0 or completed == self.total_ports:
                    self.events.put(("progress", completed))

        # Start a bounded pool of workers, then wait for all of them to finish.
        workers_list = [
            threading.Thread(target=scan_worker, daemon=True) for _ in range(workers)
        ]
        for worker in workers_list:
            worker.start()
        for worker in workers_list:
            worker.join()

        elapsed = time.monotonic() - started
        self.events.put(
            (
                "finished",
                (target, elapsed, self.cancel_event.is_set(), None),
            )
        )

    def cancel_scan(self):
        # Workers check this flag between connection attempts and stop scanning.
        self.cancel_event.set()
        self.cancel_button.configure(state=tk.DISABLED)
        self.status.set("Cancelling scan...")

    def clear_results(self):
        if not self.is_scanning:
            self.open_ports = []
            self._set_results("")
            self.progress.configure(value=0)
            self.export_button.configure(state=tk.DISABLED)
            self.status.set("Ready")

    def export_csv(self):
        # Ask where to save, then write one row per open port.
        if not self.open_ports:
            return
        path = filedialog.asksaveasfilename(
            parent=self.root,
            title="Export results",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialfile=f"horama_scan_{self.scan_host}.csv".replace(":", "_"),
        )
        if not path:
            return
        try:
            # newline="" prevents blank lines between rows on Windows.
            with open(path, "w", newline="", encoding="utf-8") as csv_file:
                writer = csv.writer(csv_file)
                writer.writerow(["host", "ip_address", "port", "state"])
                for port in sorted(self.open_ports):
                    writer.writerow([self.scan_host, self.scan_target, port, "open"])
        except OSError as error:
            messagebox.showerror("Export failed", str(error), parent=self.root)
            return
        self.status.set(f"Exported {len(self.open_ports)} open port(s) to {path}")

    def _process_events(self):
        # Tkinter widgets must only be touched from the GUI thread; drain the
        # worker queue here and apply each result safely.
        try:
            while True:
                event, value = self.events.get_nowait()
                if event == "open":
                    self.open_ports.append(value)
                    self.results.configure(state=tk.NORMAL)
                    self.results.insert(tk.END, f"Port {value} is open\n")
                    self.results.see(tk.END)
                    self.results.configure(state=tk.DISABLED)
                elif event == "progress":
                    self.progress.configure(value=value)
                    self.status.set(
                        f"Scanning... {value:,} of {self.total_ports:,} ports checked"
                    )
                elif event == "finished":
                    self._finish_scan(*value)
        except queue.Empty:
            pass
        self.root.after(100, self._process_events)

    def _finish_scan(self, target, elapsed, cancelled, error):
        # Restore controls and show a final summary once the background scan ends.
        self.is_scanning = False
        self.scan_button.configure(state=tk.NORMAL)
        self.cancel_button.configure(state=tk.DISABLED)
        self.host_entry.configure(state=tk.NORMAL)
        if error:
            self.status.set(f"Could not resolve host: {error}")
            messagebox.showerror("Host lookup failed", error, parent=self.root)
            return

        self.scan_target = target
        if self.open_ports:
            self.export_button.configure(state=tk.NORMAL)
        self._set_results(
            "\n".join(f"Port {port} is open" for port in sorted(self.open_ports))
            or "No open ports found."
        )
        summary = (
            f"{target}: {len(self.open_ports)} open port(s), "
            f"{self.completed_ports:,} checked in {elapsed:.1f}s"
        )
        self.status.set(f"Cancelled. {summary}" if cancelled else f"Complete. {summary}")
        if not cancelled:
            self.progress.configure(value=self.total_ports)

    def _set_results(self, text):
        self.results.configure(state=tk.NORMAL)
        self.results.delete("1.0", tk.END)
        self.results.insert("1.0", text)
        self.results.configure(state=tk.DISABLED)


def main():
    # Create the Tkinter window and hand control to its event loop.
    root = tk.Tk()
    PortScannerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
