import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk

class VideoView(tk.Frame):
    def __init__(self, parent, title: str = "Camera"):
        super().__init__(parent, bg="#000000")
        self._last_frame = None   # PIL.Image
        self._photo = None        # ImageTk.PhotoImage ref to avoid GC
        self._has_new = False     # mark when a worker has provided a new frame

        # Title
        title_lbl = tk.Label(self, text=title, font=("Segoe UI", 11, "bold"))
        title_lbl.pack(anchor="w", padx=6, pady=(6, 0))

        # Video area
        self.canvas = tk.Label(self, text="No Signal", fg="#888", bg="#111",
                               width=40, height=10, bd=1, relief="solid")
        self.canvas.pack(fill="both", expand=True, padx=6, pady=6)

        # Status
        self.status = tk.Label(self, text=" ", fg="#999")
        self.status.pack(anchor="w", padx=6, pady=(0, 6))

        # On resize, re-render only if there's something new to show
        self.canvas.bind("<Configure>", lambda e: self.render_if_new())

    def set_status(self, text: str):
        self.status.config(text=text)

    # Called from worker thread: DO NOT touch Tk objects here
    def update_latest_frame(self, img_pil: Image.Image):
        self._last_frame = img_pil
        self._has_new = True

    # Called on Tk thread by a periodic ticker
    def render_if_new(self):
        if self._has_new:
            self._render()
            self._has_new = False

    def _render(self):
        if self._last_frame is None:
            return
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        if w <= 2 or h <= 2:
            return

        # Keep aspect ratio
        img_w, img_h = self._last_frame.size
        scale = min(w / img_w, h / img_h)
        new_w = max(1, int(img_w * scale))
        new_h = max(1, int(img_h * scale))
        resized = self._last_frame.resize((new_w, new_h), Image.LANCZOS)

        self._photo = ImageTk.PhotoImage(resized)
        self.canvas.config(image=self._photo, text="")  # remove "No Signal" text


class MainWindow:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.configure(bg="#0e0e0e")
        self.root.minsize(800, 450)

        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except Exception:
            pass

        # Container using grid to enforce equal-width columns (no draggable sash)
        self.container = ttk.Frame(self.root)
        self.container.pack(fill="both", expand=True, padx=10, pady=10)

        # Make two columns share space equally at all times
        self.container.grid_columnconfigure(0, weight=1, uniform="cols")
        self.container.grid_columnconfigure(1, weight=1, uniform="cols")
        self.container.grid_rowconfigure(0, weight=1)

        self.front_view = VideoView(self.container,  "Front Camera")
        self.back_view  = VideoView(self.container,  "Back Camera")

        # Place views side-by-side with equal sizing
        self.front_view.grid(row=0, column=0, sticky="nsew")
        self.back_view.grid(row=0, column=1, sticky="nsew")

        # periodic repaint for drop-frame display (no backlog)
        self._frame_interval_ms = 33  # ~30 FPS
        self.root.after(self._frame_interval_ms, self._tick)

        self._fullscreen_initialized = False

    def _tick(self):
        self.front_view.render_if_new()
        self.back_view.render_if_new()
        self.root.after(self._frame_interval_ms, self._tick)

    def bind_streams(self, front_worker, back_worker):
        # For frames: write-only from worker thread (no Tk calls)
        front_worker.on_frame  = self.front_view.update_latest_frame
        back_worker.on_frame   = self.back_view.update_latest_frame

        # For status: schedule on Tk thread
        front_worker.on_status = lambda s: self.root.after(0, self.front_view.set_status, s)
        back_worker.on_status  = lambda s: self.root.after(0, self.back_view.set_status, s)

    def show(self):
        # Fullscreen to mimic the Qt app's behavior
        if not self._fullscreen_initialized:
            try:
                self.root.attributes("-fullscreen", True)
            except Exception:
                # Fallback to maximize if fullscreen not supported
                self.root.state("zoomed")
            self._fullscreen_initialized = True
