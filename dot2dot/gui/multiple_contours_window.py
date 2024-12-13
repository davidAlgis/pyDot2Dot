# gui/multiple_contours_window.py

import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import numpy as np
import cv2
import random
import platform

from dot2dot.image_discretization import ImageDiscretization
from dot2dot.gui.tooltip import Tooltip
from dot2dot.gui.utilities_gui import set_icon
from dot2dot.gui.display_window_base import DisplayWindowBase  # Updated import


class MultipleContoursWindow(DisplayWindowBase):

    def __init__(self, master, image_path):
        """
        Initializes the MultipleContoursWindow to display multiple contours found in an image.

        Parameters:
        - master: The parent Tkinter window.
        - image_path: Path to the input image.
        """
        # Initialize the base class with appropriate title and default size
        super().__init__(master,
                         title="Warning ! Multiple Contours Found",
                         width=800,
                         height=600)

        self.image_path = image_path
        self.dot_items = []

        # Load and process the image
        self.load_and_process_image()

    def load_and_process_image(self):
        """
        Loads the image, processes contours, and prepares the image with drawn contours.
        """
        # Initialize ImageDiscretization and retrieve all contours
        self.image_discretization = ImageDiscretization(
            self.image_path, 'contour', [100, 255], False)
        all_contours, _ = self.image_discretization.retrieve_contours_all_contours(
        )

        if not all_contours:
            messagebox.showerror("Error", "No contours found in the image.")
            self.window.destroy()
            return

        # Generate unique colors for each contour
        colors = self.generate_unique_colors(len(all_contours))

        # Load the original image using OpenCV
        image = cv2.imread(self.image_path)
        if image is None:
            messagebox.showerror("Error",
                                 f"Failed to load image: {self.image_path}")
            self.window.destroy()
            return

        # Resize the image to fit within 800x600 while maintaining aspect ratio
        max_width, max_height = 800, 600
        original_height, original_width = image.shape[:2]
        scale_factor = min(max_width / original_width,
                           max_height / original_height)
        new_width = int(original_width * scale_factor)
        new_height = int(original_height * scale_factor)
        resized_image = cv2.resize(image, (new_width, new_height),
                                   interpolation=cv2.INTER_AREA)

        # Create a copy to draw contours
        image_with_contours = resized_image.copy()

        # Adjust contours to match the resized image dimensions
        resized_contours = [contour * scale_factor for contour in all_contours]
        resized_contours = [
            contour.astype(np.int32) for contour in resized_contours
        ]

        # Draw each contour with a unique color and label
        for idx, contour in enumerate(resized_contours):
            # Fill the contour
            cv2.drawContours(image_with_contours, [contour], -1, colors[idx],
                             cv2.FILLED)

            # Calculate the center of the contour for labeling
            moments = cv2.moments(contour)
            if moments["m00"] != 0:
                center_x = int(moments["m10"] / moments["m00"])
                center_y = int(moments["m01"] / moments["m00"])
            else:
                # Fallback to the first point if contour area is zero
                center_x, center_y = contour[0][0]

            # Draw the contour index label
            cv2.putText(
                image_with_contours,
                f"#{idx}",
                (center_x, center_y),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.5,
                (125, 125, 125),  # Gray color for contrast
                thickness=3,
                lineType=cv2.LINE_AA)

        # Convert the image from BGR (OpenCV) to RGB (PIL)
        image_rgb = cv2.cvtColor(image_with_contours, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(image_rgb)

        # Store the original PIL image for scaling
        self.original_pil_image = pil_image

        # Update canvas dimensions based on the image size
        self.canvas_width, self.canvas_height = pil_image.size
        self.update_scrollregion(self.canvas_width, self.canvas_height)

        # Convert the PIL Image to a PhotoImage
        self.photo_image = ImageTk.PhotoImage(pil_image)

        # Draw the image on the canvas
        self.canvas.create_image(0, 0, image=self.photo_image, anchor='nw')

    def redraw_canvas(self):
        """
        Overrides the base class's redraw_canvas method to redraw the image with current scaling.
        """
        self.canvas.delete("all")
        # Scale the original image according to the current scale
        scaled_width = int(self.original_pil_image.width * self.scale)
        scaled_height = int(self.original_pil_image.height * self.scale)
        scaled_image = self.original_pil_image.resize(
            (scaled_width, scaled_height), self.resample_method)

        # Convert the scaled image to a PhotoImage
        self.photo_image = ImageTk.PhotoImage(scaled_image)

        # Draw the scaled image on the canvas
        self.canvas.create_image(0, 0, image=self.photo_image, anchor='nw')

    def generate_unique_colors(self, num_colors):
        """
        Generates a list of unique BGR colors.

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

    def on_close(self):
        """
        Handles the closing of the MultipleContoursWindow.
        """
        self.window.destroy()
