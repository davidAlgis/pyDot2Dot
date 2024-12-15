"""
Base class to defined simple window with a main canvas to display image
"""

import tkinter as tk
from tkinter import ttk
import platform
from PIL import Image, ImageTk
from dot2dot.gui.utilities_gui import set_icon


class DisplayWindowBase:
    """
    Base class to defined simple window with a main canvas to display image
    """

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
        self.canvas_width = 1240
        self.canvas_height = 1754

        # Configure scrollbars
        self.v_scroll.config(command=self.canvas.yview)
        self.h_scroll.config(command=self.canvas.xview)

        # Initialize scaling factors
        self.scale = 1.0
        self.min_scale = 0.1
        self.max_scale = 5.0

        # Determine the available resampling method
        self.resample_method = Image.Resampling.LANCZOS

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
        self.apply_zoom(scale_factor)

    def on_zoom_mac(self, event):
        """Handle zooming for macOS."""
        scale_factor = 1.1 if event.delta > 0 else 1 / 1.1
        self.apply_zoom(scale_factor)

    def apply_zoom(self, scale_factor):
        """Apply zooming based on the scale factor."""
        new_scale = self.scale * scale_factor
        new_scale = max(self.min_scale, min(self.max_scale, new_scale))

        if new_scale == self.scale:
            return  # No change in scale

        self.scale = new_scale
        self.redraw_canvas()

    def fit_canvas_to_content(self):
        """
        Adjusts the initial zoom level so that the entire image fits within the canvas and centers the image.
        """
        # Ensure the window still exists
        if not self.window.winfo_exists():
            return  # Exit early if the window is invalid
        # Ensure all pending geometry changes are processed
        self.window.update_idletasks()
        # Get the current window size
        window_width = self.window.winfo_width()
        window_height = self.window.winfo_height()

        # Calculate the scale factor to fit the image within the window
        scale_x = window_width / self.canvas_width
        scale_y = window_height / self.canvas_height
        scale_factor = min(scale_x, scale_y) * 0.9  # 90% to add padding

        # Clamp the scale factor within the allowed range
        scale_factor = max(self.min_scale, min(self.max_scale, scale_factor))
        self.scale = scale_factor

        # Update the scroll region based on the new scale
        # (This includes extra space around the image)
        self.update_scrollregion(self.canvas_width, self.canvas_height)

        # Redraw the canvas with the new scale
        self.redraw_canvas()

        # Calculate total width and height of the scrollable area
        total_width = (self.canvas_width * self.scale) + (
            max(self.canvas_width, self.canvas_height) * self.scale * 2)
        total_height = (self.canvas_height * self.scale) + (
            max(self.canvas_width, self.canvas_height) * self.scale * 2)

        # The image center (including the extra space) will be at:
        # extra_space = max(width, height) * scale
        extra_space = max(self.canvas_width, self.canvas_height) * self.scale
        image_center_x = (self.canvas_width * self.scale / 2) + extra_space
        image_center_y = (self.canvas_height * self.scale / 2) + extra_space

        # Calculate the scroll fractions to center the image
        # Move the view so that image_center_x/y appear in the center of the viewport
        x_fraction = (image_center_x - window_width / 2) / total_width
        y_fraction = (image_center_y - window_height / 2) / total_height

        # Clamp fractions between 0 and 1
        x_fraction = max(0, min(1, x_fraction))
        y_fraction = max(0, min(1, y_fraction))

        # Set the view
        self.canvas.xview_moveto(x_fraction)
        self.canvas.yview_moveto(y_fraction)

    def on_opacity_change(self, value):
        """
        Callback function for the opacity slider.
        Updates the background opacity and redraws the canvas.
        """
        self.bg_opacity = float(value)
        self.opacity_display.config(text=f"{self.bg_opacity:.2f}")
        self.redraw_canvas()

    def draw_background(self):
        """
        Draws the background image on the canvas with the current opacity.
        """
        # Apply opacity to the original image for display purposes
        if self.bg_opacity < 1.0:
            # Create a copy with adjusted opacity
            bg_image = self.background_image.copy()
            alpha = bg_image.split()[3]
            alpha = alpha.point(lambda p: p * self.bg_opacity)
            bg_image.putalpha(alpha)
        else:
            bg_image = self.background_image

        # Scale the image according to the current scale
        scaled_width = int(bg_image.width * self.scale)
        scaled_height = int(bg_image.height * self.scale)
        scaled_image = bg_image.resize((scaled_width, scaled_height),
                                       self.resample_method)

        # Convert the scaled image to a PhotoImage
        self.background_photo = ImageTk.PhotoImage(scaled_image)

        # Draw the image on the canvas
        self.canvas.create_image(0,
                                 0,
                                 image=self.background_photo,
                                 anchor='nw')

    def redraw_canvas(self):
        """Clear and redraw the canvas (to be implemented in subclasses)."""
        pass

    def update_scrollregion(self, width, height):
        """Update the scroll region to allow extra panning beyond the image size."""
        # Let's allow extra space equal to the image size on each side
        extra_space = max(width, height) * self.scale

        # Adjust the scrollregion to extend beyond the actual image dimensions
        self.canvas.config(scrollregion=(-extra_space, -extra_space,
                                         (width * self.scale) + extra_space,
                                         (height * self.scale) + extra_space))
