# gui/edit_window.py

import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk, ImageDraw, ImageFont
import os
import numpy as np


class EditWindow:

    def __init__(self, master, image, dots, labels, dot_color, font_color,
                 font_path, font_size):
        """
        Initializes the EditWindow.

        Parameters:
        - master: The parent Tkinter widget.
        - image: The original PIL Image (unused in drawing but kept for potential future use).
        - dots: List of tuples containing dot coordinates and a placeholder (e.g., [(x, y), None]).
        - labels: List of tuples containing label text, position, and color (e.g., [(label, [(x, y), anchor], color)]).
        - dot_color: Tuple representing RGBA color for dots.
        - font_color: Tuple representing RGBA color for labels.
        - font_path: Path to the font file.
        - font_size: Font size in pixels.
        """
        self.top = tk.Toplevel(master)
        self.top.title("Edit Dots and Labels")
        self.top.geometry("800x600")
        self.top.minsize(400, 300)  # Prevent extreme resizing

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
        self.image = image
        self.dots = dots  # List of tuples: ((x, y), None)
        self.labels = labels  # List of tuples: (label, [(x, y), anchor], color)
        self.dot_color = self.ensure_opaque(dot_color)  # Ensure opaque
        self.font_color = self.ensure_opaque(font_color)  # Ensure opaque
        self.font_path = font_path
        self.font_size = int(font_size)

        # Store original image dimensions for scaling
        self.original_width, self.original_height = self.image.size

        # Initialize Canvas
        self.canvas = tk.Canvas(self.top, bg="white")
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Load Font
        try:
            self.font = ImageFont.truetype(self.font_path, self.font_size)
        except IOError:
            messagebox.showerror(
                "Error",
                f"Font file '{self.font_path}' not found. Using default font.")
            self.font = ImageFont.load_default()

        # Bind the configure event to handle window resizing
        self.canvas.bind("<Configure>", self.on_resize)

        # Initial draw after the window has been rendered
        self.top.after(100, self.draw_all)

    def ensure_opaque(self, color_tuple):
        """
        Ensures that the color tuple has an alpha value of 255 (fully opaque).

        Parameters:
        - color_tuple: Tuple representing RGBA color.

        Returns:
        - Tuple with alpha set to 255.
        """
        if len(color_tuple) == 4:
            r, g, b, a = color_tuple
            return (r, g, b, 255)  # Override alpha to 255
        elif len(color_tuple) == 3:
            r, g, b = color_tuple
            return (r, g, b, 255)
        else:
            # Default to black if format is incorrect
            return (0, 0, 0, 255)

    def draw_all(self):
        """
        Clears the canvas and redraws all dots and labels.
        Ensures that each label is drawn only once.
        """
        # Get current canvas size
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

        print(f"Canvas size: width={canvas_width}, height={canvas_height}")
        print(f"Number of dots: {len(self.dots)}")
        print(f"Number of labels: {len(self.labels)}")

        if canvas_width < 10 or canvas_height < 10:
            # Canvas size is too small; skip drawing
            print("Canvas size too small. Skipping draw.")
            return

        # Compute scaling factor based on original image size and canvas size
        scale_x = canvas_width / self.original_width
        scale_y = canvas_height / self.original_height
        scale = min(scale_x, scale_y)
        print(
            f"Scaling factors: scale_x={scale_x}, scale_y={scale_y}, used_scale={scale}"
        )

        # Create a new image with white background
        display_image = Image.new("RGBA", (canvas_width, canvas_height),
                                  (255, 255, 255, 255))
        draw = ImageDraw.Draw(display_image)

        # Calculate offset to center the image
        scaled_width = int(self.original_width * scale)
        scaled_height = int(self.original_height * scale)
        offset_x = (canvas_width - scaled_width) // 2
        offset_y = (canvas_height - scaled_height) // 2
        print(
            f"Scaled image size: {scaled_width}x{scaled_height}, Offset: ({offset_x}, {offset_y})"
        )

        # Adjust font size based on scaling
        dynamic_font_size = max(8, int(self.font_size *
                                       scale))  # Minimum font size of 8
        try:
            self.font = ImageFont.truetype(self.font_path, dynamic_font_size)
            print(f"Using dynamic font size: {dynamic_font_size}")
        except IOError:
            print(
                f"Font file '{self.font_path}' not found. Using default font.")
            self.font = ImageFont.load_default()

        # Draw each dot
        for index, (dot, _) in enumerate(self.dots):
            original_x, original_y = dot
            scaled_x = original_x * scale + offset_x
            scaled_y = original_y * scale + offset_y
            r = max(2, int(dynamic_font_size *
                           0.5))  # Radius proportional to font size
            print(
                f"Drawing dot {index}: Original ({original_x}, {original_y}), Scaled ({scaled_x}, {scaled_y}), Radius {r}"
            )
            draw.ellipse(
                (scaled_x - r, scaled_y - r, scaled_x + r, scaled_y + r),
                fill=self.get_color_hex(self.dot_color),
                outline=None)

        # Remove duplicate labels
        unique_labels = self.get_unique_labels()
        print(f"Number of unique labels to draw: {len(unique_labels)}")

        # Draw each label
        for label, positions, color in unique_labels:
            try:
                pos, anchor = positions[0]  # Corrected unpacking
            except ValueError as ve:
                print(f"Error unpacking positions for label '{label}': {ve}")
                continue  # Skip this label

            original_x, original_y = pos
            scaled_x = original_x * scale + offset_x
            scaled_y = original_y * scale + offset_y
            pil_anchor = self.get_pil_anchor(anchor)
            print(
                f"Drawing label '{label}': Original ({original_x}, {original_y}), Scaled ({scaled_x}, {scaled_y}), Anchor '{pil_anchor}'"
            )
            draw.text((scaled_x, scaled_y),
                      label,
                      font=self.font,
                      fill=self.get_color_hex(color),
                      anchor=pil_anchor)

        # Convert PIL image to ImageTk
        try:
            self.tk_image = ImageTk.PhotoImage(display_image)
        except Exception as e:
            messagebox.showerror("Error",
                                 f"Failed to create ImageTk.PhotoImage: {e}")
            return

        # Display the image on the canvas
        self.canvas.create_image(0, 0, anchor="nw", image=self.tk_image)
        self.canvas.image = self.tk_image  # Keep a reference to prevent garbage collection

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

    def get_color_hex(self, rgba_tuple):
        """
        Converts an RGBA or RGB tuple to a hexadecimal color code.
        Ignores the alpha channel.
        """
        try:
            if len(rgba_tuple) == 4:
                r, g, b, a = rgba_tuple
            elif len(rgba_tuple) == 3:
                r, g, b = rgba_tuple
            else:
                # Default to black if format is incorrect
                r, g, b = 0, 0, 0
            color_hex = f'#{r:02x}{g:02x}{b:02x}'
            print(f"Converted RGBA {rgba_tuple} to hex {color_hex}")
            return color_hex
        except Exception as e:
            print(f"Error converting color: {e}")
            return "#000000"  # Default to black

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
        pil_anchor = anchor_map.get(anchor_str.lower(),
                                    "la")  # Default to "la" if not found
        print(f"Converted anchor '{anchor_str}' to PIL anchor '{pil_anchor}'")
        return pil_anchor

    def on_resize(self, event):
        """
        Handles the resizing of the window and updates the displayed image accordingly while preserving aspect ratio.
        """
        print("Canvas resized. Redrawing all elements.")
        self.draw_all()
