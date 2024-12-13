# gui/multiple_contours_window.py

from dot2dot.gui.display_window_base import DisplayWindowBase
from PIL import Image, ImageTk
import cv2
import numpy as np


class MultipleContoursWindow(DisplayWindowBase):

    def __init__(self, master, image_path, contours):
        super().__init__(master, title="Warning! Multiple Contours Found")
        self.image_path = image_path
        self.contours = contours
        self.original_image = None

        self.load_image()
        self.display_contours()

    def load_image(self):
        """Load the original image."""
        image = cv2.imread(self.image_path)
        if image is None:
            raise FileNotFoundError(f"Image not found: {self.image_path}")

        self.original_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        self.update_scrollregion(image.shape[1], image.shape[0])

    def display_contours(self):
        """Display contours on the canvas."""
        image_with_contours = self.original_image.copy()
        for contour in self.contours:
            cv2.drawContours(image_with_contours, [contour], -1, (0, 255, 0),
                             2)

        self.redraw_canvas(image_with_contours)

    def redraw_canvas(self, image=None):
        """Redraw the image on the canvas."""
        self.canvas.delete("all")
        if image is None:
            image = self.original_image

        height, width = image.shape[:2]
        photo_image = ImageTk.PhotoImage(Image.fromarray(image))
        self.canvas.create_image(0, 0, image=photo_image, anchor='nw')
        self.photo_image = photo_image  # Keep a reference to avoid garbage collection
