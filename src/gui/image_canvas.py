# gui/image_canvas.py

import tkinter as tk
from PIL import Image, ImageTk
import cv2
import numpy as np
import platform
import utils
import matplotlib.pyplot as plt


class ImageCanvas:

    def __init__(self, parent, bg="gray", double_click_callback=None):
        self.canvas = tk.Canvas(parent, bg=bg, cursor="hand2")
        self.canvas.pack(fill="both", expand=True)
        # Flag to indicate if an image is loaded
        self.image_loaded = False
        self.double_click_callback = double_click_callback
        # Bind mouse events for zooming and panning
        if platform.system() == 'Windows':
            self.canvas.bind("<MouseWheel>", self.on_zoom)  # Windows
        else:
            self.canvas.bind("<Button-4>", self.on_zoom)  # Linux scroll up
            self.canvas.bind("<Button-5>", self.on_zoom)  # Linux scroll down

        # Panning bindings
        self.canvas.bind("<ButtonPress-1>", self.on_pan_start)
        self.canvas.bind("<B1-Motion>", self.on_pan_move)
        self.canvas.bind("<Double-1>", self.on_double_click)
        # Initialize image-related attributes
        self.image = None  # Original PIL Image
        self.photo_image = None  # ImageTk.PhotoImage for Tkinter
        self.scale = 1.0  # Current scale factor
        self.min_scale = 0.1  # Minimum zoom level
        self.max_scale = 5.0  # Maximum zoom level
        self._drag_data = {"x": 0, "y": 0}  # For panning

        self.bind_resize()

    def bind_resize(self):
        """
        Binds the canvas resize event to reposition the placeholder text dynamically.
        """
        self.canvas.bind("<Configure>", self.on_resize)

    def on_resize(self, event):
        """
        Repositions the placeholder text to keep it centered on the canvas.
        """
        placeholder_text = self.canvas.find_withtag("placeholder_text")
        if placeholder_text:
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()
            self.canvas.coords(placeholder_text, canvas_width / 2,
                               canvas_height / 2)

    def load_image(self, pil_image):
        """
        Loads a PIL Image into the canvas and resets zoom and pan.
        """
        self.image = pil_image
        self.scale = 1.0
        self.image_loaded = True
        self.canvas.delete("all")
        self.display_image()
        image_width, image_height = pil_image.size  # Assuming processed_image is a PIL Image

        return image_width, image_height

    def display_image(self):
        """
        Displays the current image on the canvas with the current scale and pan offsets.
        """
        if self.image is None:
            return

        # Get current canvas size
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

        # Resize the image based on the current scale
        resized_pil_image = utils.resize_image(
            self.image,
            (int(canvas_width * self.scale), int(canvas_height * self.scale)))
        self.photo_image = ImageTk.PhotoImage(resized_pil_image)

        # Center the image
        self.canvas.delete("all")
        self.canvas.create_image(canvas_width / 2,
                                 canvas_height / 2,
                                 image=self.photo_image,
                                 anchor="center")

    def on_zoom(self, event):
        """
        Handles zooming in and out with the mouse wheel.
        """
        if not self.image_loaded:
            return
        if platform.system() == 'Windows':
            if event.delta > 0:
                zoom_in = True
            elif event.delta < 0:
                zoom_in = False
            else:
                zoom_in = None
        else:
            if event.num == 4:
                zoom_in = True
            elif event.num == 5:
                zoom_in = False
            else:
                zoom_in = None

        if zoom_in is not None:
            # Adjust the scale factor
            if zoom_in:
                new_scale = self.scale * 1.1
            else:
                new_scale = self.scale / 1.1

            # Clamp the scale factor
            new_scale = max(self.min_scale, min(self.max_scale, new_scale))

            if new_scale != self.scale:
                self.scale = new_scale
                self.display_image()

    def on_pan_start(self, event):
        """
        Records the starting position for panning.
        """
        if not self.image_loaded:
            return

        self._drag_data["x"] = event.x
        self._drag_data["y"] = event.y

    def on_pan_move(self, event):
        """
        Handles the panning motion.
        """
        if not self.image_loaded:
            return

        dx = event.x - self._drag_data["x"]
        dy = event.y - self._drag_data["y"]
        self._drag_data["x"] = event.x
        self._drag_data["y"] = event.y

        # Move the image by the deltas
        self.canvas.move("all", dx, dy)

    def on_double_click(self, event):
        """
        Handles double-click events on the canvas.
        """
        if self.double_click_callback:
            self.double_click_callback()

    def display_centered_text(self,
                              text,
                              font=("Helvetica", 14, "italic"),
                              color="gray"):
        """
        Displays centered text on the canvas.
        Parameters:
        - text: The text to display.
        - font: Font for the text.
        - color: Text color.
        """
        self.canvas.delete(
            "placeholder_text")  # Remove any existing placeholder text
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        self.image_loaded = False
        # Create the placeholder text at the center
        self.canvas.create_text(canvas_width / 2,
                                canvas_height / 2,
                                text=text,
                                font=font,
                                fill=color,
                                tags="placeholder_text",
                                anchor="center")

        # Ensure placeholder text remains static (not affected by pan/zoom)
        self.canvas.tag_lower("placeholder_text")
