# gui/edit_window.py

import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk, ImageDraw, ImageFont
import cv2
import numpy as np


class EditWindow:

    def __init__(self, master, image, dots, labels, dot_color, font_color,
                 font_path, font_size):
        self.top = tk.Toplevel(master)
        self.top.title("Edit Dots and Labels")
        self.top.geometry("800x600")

        # Verify that the image is a PIL Image
        if isinstance(image, np.ndarray):
            messagebox.showerror(
                "Error",
                "Received image is a NumPy array. Expected a PIL Image.")
            self.top.destroy()
            return
        elif not isinstance(image, Image.Image):
            messagebox.showerror("Error",
                                 "Received image is not a valid PIL Image.")
            self.top.destroy()
            return

        # Store parameters
        self.original_image = image.copy()
        self.dots = dots  # List of tuples: ((x, y), box)
        self.labels = labels  # List of tuples: (label, positions, color)
        self.dot_color = dot_color  # Tuple (R, G, B, A)
        self.font_color = font_color  # Tuple (R, G, B, A)
        self.font_path = font_path  # String path to font file
        self.font_size = int(font_size)  # Font size in pixels

        # Canvas to display the image
        self.canvas = tk.Canvas(self.top, bg="white")
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Load the image into PIL and draw dots and labels
        self.pil_image = self.original_image.convert("RGBA")
        self.draw_dots_and_labels()

        # Convert PIL image to ImageTk
        self.tk_image = ImageTk.PhotoImage(self.pil_image)
        self.canvas_image = self.canvas.create_image(0,
                                                     0,
                                                     anchor="nw",
                                                     image=self.tk_image)

        # Bind the configure event to handle window resizing
        self.canvas.bind("<Configure>", self.resize_image)

        # Optionally, add UI controls for editing (e.g., buttons to add/remove dots/labels)
        # For simplicity, these are not implemented here.

    def draw_dots_and_labels(self):
        """
        Draws dots and labels on the PIL image.
        """
        draw = ImageDraw.Draw(self.pil_image)
        try:
            font = ImageFont.truetype(self.font_path, self.font_size)
        except IOError:
            messagebox.showerror("Error",
                                 f"Font file '{self.font_path}' not found.")
            font = ImageFont.load_default()

        # Draw dots
        for dot, box in self.dots:
            x, y = dot
            r = self.calculate_radius()
            # Draw ellipse for dot
            draw.ellipse((x - r, y - r, x + r, y + r),
                         fill=self.dot_color,
                         outline=None)

        # Draw labels
        for label, positions, color in self.labels:
            # Assuming positions is a list with one tuple (position, anchor)
            pos, anchor = positions[0]
            x, y = pos
            # Convert RGBA to RGB for PIL
            rgb_color = color[:3]
            # Draw text
            draw.text((x, y),
                      label,
                      font=font,
                      fill=rgb_color,
                      anchor=self.get_pil_anchor(anchor))

    def calculate_radius(self):
        """
        Calculates the radius for dots based on the current image size.
        """
        # Example: Radius is proportional to image size
        width, height = self.pil_image.size
        return max(2, int(min(width, height) * 0.005))  # Adjust as needed

    def get_pil_anchor(self, anchor_str):
        """
        Converts custom anchor strings to PIL-compatible anchor values.
        """
        anchor_map = {
            "ls": "la",  # Left Baseline
            "rs": "ra",  # Right Baseline
            "ms": "ma"  # Middle Baseline
        }
        return anchor_map.get(anchor_str, "la")  # Default to "la" if not found

    def resize_image(self, event):
        """
        Handles the resizing of the window and updates the displayed image accordingly.
        """
        # Get the size of the canvas
        canvas_width = event.width
        canvas_height = event.height

        # Resize the PIL image to fit the canvas
        resized_pil = self.pil_image.resize((canvas_width, canvas_height),
                                            Image.LANCZOS)

        # Update the ImageTk photo
        self.tk_image = ImageTk.PhotoImage(resized_pil)
        self.canvas.itemconfig(self.canvas_image, image=self.tk_image)

    def update_image(self):
        """
        Refreshes the image on the canvas after modifications.
        """
        self.pil_image = self.original_image.convert("RGBA")
        self.draw_dots_and_labels()
        self.tk_image = ImageTk.PhotoImage(self.pil_image)
        self.canvas.itemconfig(self.canvas_image, image=self.tk_image)

    def add_dot(self, x, y):
        """
        Adds a new dot at the specified (x, y) coordinates.
        """
        self.dots.append(((x, y), None))  # Assuming box is not used
        self.draw_dots_and_labels()
        self.update_image()

    def remove_dot(self, index):
        """
        Removes the dot at the specified index.
        """
        if 0 <= index < len(self.dots):
            del self.dots[index]
            self.draw_dots_and_labels()
            self.update_image()

    def add_label(self, label, x, y, anchor="ls"):
        """
        Adds a new label at the specified (x, y) coordinates.
        """
        self.labels.append((label, [(x, y), anchor], self.font_color))
        self.draw_dots_and_labels()
        self.update_image()

    def remove_label(self, index):
        """
        Removes the label at the specified index.
        """
        if 0 <= index < len(self.labels):
            del self.labels[index]
            self.draw_dots_and_labels()
            self.update_image()
