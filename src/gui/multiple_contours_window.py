# gui/multiple_contours_window.py

import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import numpy as np
import cv2
from image_discretization import ImageDiscretization
import random
import utils


class MultipleContoursWindow:

    def __init__(self, master, image_path, contours):
        self.master = master
        self.image_path = image_path
        self.contours = contours
        self.selected_contour = None

        self.window = tk.Toplevel(master)
        self.window.title("Warning ! Multiple Contours Found")
        self.window.geometry("800x600")  # Set a default size

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
                                scrollregion=(0, 0, 800, 600),
                                xscrollcommand=self.h_scroll.set,
                                yscrollcommand=self.v_scroll.set)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Configure scrollbars
        self.v_scroll.config(command=self.canvas.yview)
        self.h_scroll.config(command=self.canvas.xview)

        # Load and process the image
        self.image_discretization = ImageDiscretization(
            image_path, 'contour', [100, 255], False)

        # Retrieve contours and grayscale image
        contours, grays = self.image_discretization.retrieve_contours_all_contours(
        )

        # Display the contours on the canvas
        self.display_contours(contours)

    def display_contours(self, contours):
        """
        Displays the image with all contours drawn in different colors on the canvas.
        Each contour is drawn with a unique color for easy differentiation.
        """
        # Load the original image using OpenCV
        image = cv2.imread(self.image_path)
        if image is None:
            messagebox.showerror("Error",
                                 f"Failed to load image: {self.image_path}")
            self.window.destroy()
            return

        # Create a copy of the image to draw contours
        image_with_contours = image.copy()

        # Generate unique colors for each contour
        colors = self.generate_unique_colors(len(contours))

        # Draw each contour with a unique color
        for idx, contour in enumerate(contours):
            cv2.drawContours(
                image_with_contours,
                [contour],
                -1,  # Draw all contours
                colors[idx],
                2  # Thickness of contour lines
            )

        # Convert the image from BGR (OpenCV format) to RGB (PIL format)
        image_rgb = cv2.cvtColor(image_with_contours, cv2.COLOR_BGR2RGB)

        # Convert the NumPy array to a PIL Image
        pil_image = Image.fromarray(image_rgb)

        # Optionally, resize the image if it's too large
        max_width, max_height = 1600, 1200  # Maximum display size
        # pil_image = self.resize_image(pil_image, max_width, max_height)
        target_size = (max_width, max_height)
        pil_image = utils.resize_image(pil_image, target_size)

        # Convert the PIL Image to an ImageTk PhotoImage
        self.photo_image = ImageTk.PhotoImage(pil_image)

        # Update the scroll region based on image size
        self.canvas.config(scrollregion=(0, 0, pil_image.width,
                                         pil_image.height))

        # Display the image on the canvas
        self.canvas.create_image(0, 0, image=self.photo_image, anchor='nw')

    def generate_unique_colors(self, num_colors):
        """
        Generates a list of unique colors.

        Parameters:
        - num_colors: Number of unique colors to generate.

        Returns:
        - List of BGR tuples.
        """
        random.seed(42)  # For reproducibility
        colors = []
        for _ in range(num_colors):
            color = (random.randint(0, 255), random.randint(0, 255),
                     random.randint(0, 255))
            colors.append(color)
        return colors
