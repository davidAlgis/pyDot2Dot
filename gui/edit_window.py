# gui/edit_window.py

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageTk, ImageDraw, ImageFont
import cv2
import numpy as np


class EditWindow:

    def __init__(self, master, image, dots, labels, dot_color, font_color,
                 font_path, font_size):
        self.top = tk.Toplevel(master)
        self.top.title("Edit Dots and Labels")
        self.top.geometry("800x600")
        self.top.minsize(400,
                         300)  # Set a minimum size to prevent extreme resizing

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

    def draw_dots_and_labels(self):
        """
        Draws dots and labels on the PIL image.
        Ensures that each label is drawn only once by removing duplicates.
        """
        draw = ImageDraw.Draw(self.pil_image)
        try:
            font = ImageFont.truetype(self.font_path, self.font_size)
        except IOError:
            messagebox.showerror(
                "Error",
                f"Font file '{self.font_path}' not found. Using default font.")
            font = ImageFont.load_default()

        # Remove duplicate labels
        unique_labels = self.get_unique_labels()

        # Debugging: Print the number of unique labels
        print(f"Drawing {len(unique_labels)} unique labels.")

        # Draw dots
        for dot, box in self.dots:
            x, y = dot
            r = self.calculate_radius()
            # Draw ellipse for dot
            draw.ellipse((x - r, y - r, x + r, y + r),
                         fill=self.dot_color,
                         outline=None)

        # Draw labels
        for label, positions, color in unique_labels:
            # Assuming positions is a list with one tuple (position, anchor)
            pos, anchor = positions[0]
            x, y = pos
            # Convert RGBA to RGB for PIL
            rgb_color = color[:3]
            # Draw text
            pil_anchor = self.get_pil_anchor(anchor)
            if pil_anchor is None:
                pil_anchor = "la"  # Default anchor
            draw.text((x, y),
                      label,
                      font=font,
                      fill=rgb_color,
                      anchor=pil_anchor)

    def get_unique_labels(self):
        """
        Returns a list of unique labels based on label text and position.
        Removes duplicates from self.labels.
        """
        seen = set()
        unique_labels = []
        for label, positions, color in self.labels:
            # Create a unique key based on label text and position
            pos_key = tuple(positions[0][0])  # (x, y)
            key = (label, pos_key)
            if key not in seen:
                seen.add(key)
                unique_labels.append((label, positions, color))
        return unique_labels

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
        Handles both custom ('ls', 'rs', 'ms') and standard ('left', 'right', 'middle') anchors.
        """
        anchor_map = {
            "ls": "la",  # Left Baseline
            "rs": "ra",  # Right Baseline
            "ms": "ma",  # Middle Baseline
            "left": "la",  # Left Baseline
            "right": "ra",  # Right Baseline
            "middle": "ma"  # Middle Baseline
        }
        return anchor_map.get(anchor_str.lower(),
                              "la")  # Default to "la" if not found

    def resize_image(self, event):
        """
        Handles the resizing of the window and updates the displayed image accordingly while preserving aspect ratio.
        """
        # Get the size of the canvas
        canvas_width = event.width
        canvas_height = event.height

        # Get the original image size
        original_width, original_height = self.pil_image.size

        # Compute scaling factor to preserve aspect ratio
        scale = min(canvas_width / original_width,
                    canvas_height / original_height)

        # Compute new image size
        new_width = int(original_width * scale)
        new_height = int(original_height * scale)

        # Resize the image with high-quality resampling
        resized_pil = self.pil_image.resize((new_width, new_height),
                                            Image.LANCZOS)

        # Convert to ImageTk
        self.tk_image = ImageTk.PhotoImage(resized_pil)

        # Clear the canvas
        self.canvas.delete("all")

        # Compute position to center the image
        x = (canvas_width - new_width) // 2
        y = (canvas_height - new_height) // 2

        # Add the image to the canvas
        self.canvas_image = self.canvas.create_image(x,
                                                     y,
                                                     anchor="nw",
                                                     image=self.tk_image)

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
