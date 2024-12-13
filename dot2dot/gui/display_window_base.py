# gui/display_window_base.py

import tkinter as tk
from tkinter import ttk
import platform
from PIL import Image, ImageTk
from dot2dot.gui.utilities_gui import set_icon


class DisplayWindowBase:

    def __init__(self, master, title="Base Window", width=800, height=600):
        self.master = master

        # Create the top-level window
        self.window = tk.Toplevel(master)
        self.window.title(title)
        self.window.geometry(f"{width}x{height}")
        set_icon(self.window)

        # Maximize the window based on the operating system
        self.maximize_window()

        # Create a scrollable canvas
        self.canvas_frame = ttk.Frame(self.window)
        self.canvas_frame.pack(fill=tk.BOTH, expand=True)

        # Add scrollbars
        self.v_scroll = ttk.Scrollbar(self.canvas_frame, orient=tk.VERTICAL)
        self.v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.h_scroll = ttk.Scrollbar(self.canvas_frame, orient=tk.HORIZONTAL)
        self.h_scroll.pack(side=tk.BOTTOM, fill=tk.X)

        # Create the canvas
        self.canvas = tk.Canvas(self.canvas_frame,
                                bg='white',
                                scrollregion=(0, 0, width, height),
                                xscrollcommand=self.h_scroll.set,
                                yscrollcommand=self.v_scroll.set)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Configure scrollbars
        self.v_scroll.config(command=self.canvas.yview)
        self.h_scroll.config(command=self.canvas.xview)

        # Initialize scaling factors
        self.scale = 1.0
        self.min_scale = 0.1
        self.max_scale = 5.0

        # Determine the available resampling method
        try:
            self.resample_method = Image.Resampling.LANCZOS
        except AttributeError:
            self.resample_method = Image.ANTIALIAS  # For older Pillow versions

        # Bind mouse events for zooming and panning
        self.bind_zoom_events()
        self.bind_panning_events()

    def maximize_window(self):
        """
        Maximizes the window based on the operating system.
        """
        os_name = platform.system()
        if os_name == 'Windows':
            self.window.state('zoomed')
        elif os_name == 'Darwin':  # macOS
            self.window.attributes('-zoomed', True)
        else:  # Linux and others
            screen_width = self.window.winfo_screenwidth()
            screen_height = self.window.winfo_screenheight()
            self.window.geometry(f"{screen_width}x{screen_height}+0+0")

    def bind_zoom_events(self):
        """Bind mouse events for zooming."""
        if platform.system() == 'Windows':
            self.canvas.bind("<MouseWheel>", self.on_zoom)  # Windows
        elif platform.system() == 'Darwin':
            self.canvas.bind("<MouseWheel>", self.on_zoom_mac)  # macOS
        else:
            self.canvas.bind("<Button-4>", self.on_zoom)  # Linux scroll up
            self.canvas.bind("<Button-5>", self.on_zoom)  # Linux scroll down

    def bind_panning_events(self):
        """Bind mouse events for panning."""
        if platform.system(
        ) == 'Darwin':  # macOS uses Button-2 for right-click
            self.canvas.bind('<ButtonPress-2>', self.on_pan_start)
            self.canvas.bind('<B2-Motion>', self.on_pan_move)
        else:
            self.canvas.bind('<ButtonPress-3>', self.on_pan_start)
            self.canvas.bind('<B3-Motion>', self.on_pan_move)

    def on_pan_start(self, event):
        """Record the starting position for panning."""
        self.canvas.scan_mark(event.x, event.y)

    def on_pan_move(self, event):
        """Handle the panning motion."""
        self.canvas.scan_dragto(event.x, event.y, gain=1)

    def on_zoom(self, event):
        """Handle zooming for Windows and Linux."""
        if platform.system() == 'Windows':
            scale_factor = 1.1 if event.delta > 0 else 1 / 1.1
        else:
            scale_factor = 1.1 if event.num == 4 else 1 / 1.1
        self.apply_zoom(scale_factor, event.x, event.y)

    def on_zoom_mac(self, event):
        """Handle zooming for macOS."""
        scale_factor = 1.1 if event.delta > 0 else 1 / 1.1
        self.apply_zoom(scale_factor, event.x, event.y)

    def apply_zoom(self, scale_factor, x, y):
        """Apply zooming based on the scale factor."""
        new_scale = self.scale * scale_factor
        new_scale = max(self.min_scale, min(self.max_scale, new_scale))

        if new_scale == self.scale:
            return  # No change in scale

        self.scale = new_scale
        self.redraw_canvas()

    def redraw_canvas(self):
        """Clear and redraw the canvas (to be implemented in subclasses)."""
        self.canvas.delete("all")
        # To be implemented by subclasses

    def update_scrollregion(self, width, height):
        """Update the scroll region based on the current scale."""
        self.canvas.config(scrollregion=(0, 0, width * self.scale,
                                         height * self.scale))
