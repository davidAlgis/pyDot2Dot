# gui/edit_window.py

import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import cv2


class EditWindow:

    def __init__(self, master, image, dots, labels):
        self.top = tk.Toplevel(master)
        self.top.title("Edit Dots and Labels")
        self.top.geometry("800x600")

        # Canvas to display the image
        self.canvas = tk.Canvas(self.top, bg="white")
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Load the image
        self.image = image.copy()  # Make a copy to draw on
        if self.image.shape[2] == 4:
            pil_image = Image.fromarray(
                cv2.cvtColor(self.image, cv2.COLOR_BGRA2RGBA))
        else:
            pil_image = Image.fromarray(
                cv2.cvtColor(self.image, cv2.COLOR_BGR2RGB))
        self.pil_image = pil_image
        self.tk_image = ImageTk.PhotoImage(pil_image)
        self.canvas_image = self.canvas.create_image(0,
                                                     0,
                                                     anchor="nw",
                                                     image=self.tk_image)

        # Store dots and labels
        self.dots = dots
        self.labels = labels

        # Bind the configure event to resize the image on window resize
        self.canvas.bind("<Configure>", self.resize_image)

        # Initially draw dots and labels
        self.draw_dots_and_labels()

    def resize_image(self, event):
        # Get the new size of the canvas
        canvas_width = event.width
        canvas_height = event.height

        # Resize the PIL image to fit the canvas
        try:
            resized_pil = self.pil_image.resize((canvas_width, canvas_height),
                                                Image.Resampling.LANCZOS)
        except AttributeError:
            # For older Pillow versions
            resized_pil = self.pil_image.resize((canvas_width, canvas_height),
                                                Image.ANTIALIAS)
        self.tk_image = ImageTk.PhotoImage(resized_pil)
        self.canvas.itemconfig(self.canvas_image, image=self.tk_image)

        # Clear existing dots and labels
        self.canvas.delete("dot")
        self.canvas.delete("label")

        # Draw dots and labels on the resized image
        self.draw_dots_and_labels(resized_pil.size)

    def draw_dots_and_labels(self, resized_size=None):
        if resized_size is None:
            resized_size = self.pil_image.size

        # Calculate scaling factors
        original_size = self.pil_image.size
        scale_x = resized_size[0] / original_size[0]
        scale_y = resized_size[1] / original_size[1]

        for idx, ((x, y), dot_box) in enumerate(self.dots):
            # Scale coordinates
            x_scaled = x * scale_x
            y_scaled = y * scale_y
            r = 5  # Radius for display purposes

            # Draw the dot
            self.canvas.create_oval(x_scaled - r,
                                    y_scaled - r,
                                    x_scaled + r,
                                    y_scaled + r,
                                    fill='red',
                                    tags="dot")

        for idx, (label, positions, color) in enumerate(self.labels):
            # Assuming positions is a list with one tuple (position, anchor)
            pos, anchor = positions[0]
            x_scaled = pos[0] * scale_x
            y_scaled = pos[1] * scale_y

            # Determine color
            if color == (255, 0, 0):
                text_color = "red"
            else:
                text_color = "black"

            # Draw the label
            self.canvas.create_text(x_scaled,
                                    y_scaled,
                                    text=label,
                                    fill=text_color,
                                    anchor=self.get_tk_anchor(anchor),
                                    tags="label")

    def get_tk_anchor(self, anchor_str):
        anchor_map = {
            "ls": "sw",  # left side
            "rs": "se",  # right side
            "ms": "n"  # middle side (top)
        }
        return anchor_map.get(anchor_str, "center")
