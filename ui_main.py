import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk

class VideoView(tk.Frame):
    def __init__(self, parent, title: str = "Camera"):
        super().__init__(parent, bg="#000000")
        self._last_frame = None   # PIL.Image
        self._photo = None        # ImageTk.PhotoImage ref to avoid GC

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

        # Re-render the last frame on resize to keep aspect ratio
        self.canvas.bind("<Configure>", lambda e: self._render())

    def set_status(self, text: str):
        self.status.config(text=text)

    def show_frame(self, img_pil: Image.Image):
        self._last_frame = img_pil
        self._render()

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

        # Horizontal splitter
        self.split = ttk.Panedwindow(self.root, orient=tk.HORIZONTAL)
        self.split.pack(fill="both", expand=True, padx=10, pady=10)

        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except Exception:
            pass

        self.left_frame  = ttk.Frame(self.split)
        self.right_frame = ttk.Frame(self.split)

        self.split.add(self.left_frame, weight=1)
        self.split.add(self.right_frame, weight=1)

        self.front_view = VideoView(self.left_frame,  "Front Camera")
        self.back_view  = VideoView(self.right_frame, "Back Camera")

        self.front_view.pack(fill="both", expand=True)
        self.back_view.pack(fill="both", expand=True)

        self._fullscreen_initialized = False

    def bind_streams(self, front_worker, back_worker):
        # Ensure UI updates run on the Tk thread
        def safe_call(fn):
            return lambda *a, **k: self.root.after(0, fn, *a, **k)

        front_worker.on_frame  = safe_call(self.front_view.show_frame)
        front_worker.on_status = safe_call(self.front_view.set_status)

        back_worker.on_frame   = safe_call(self.back_view.show_frame)
        back_worker.on_status  = safe_call(self.back_view.set_status)

    def show(self):
        # Fullscreen to mimic the Qt app's behavior
        if not self._fullscreen_initialized:
            try:
                self.root.attributes("-fullscreen", True)
            except Exception:
                # Fallback to maximize if fullscreen not supported
                self.root.state("zoomed")
            self._fullscreen_initialized = True
