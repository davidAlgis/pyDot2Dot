# gui/multiple_contours_window.py

import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import numpy as np
import cv2
from image_discretization import ImageDiscretization
import random
import utils
import platform


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

        # Initialize scaling factors for zooming
        self.scale = 1.0
        self.min_scale = 0.1
        self.max_scale = 5.0

        # Bind mouse events for zooming (similar logic to test_values_window)
        if platform.system() == 'Windows':
            self.canvas.bind("<MouseWheel>", self.on_zoom)  # Windows
        elif platform.system() == 'Darwin':
            self.canvas.bind("<MouseWheel>", self.on_zoom_mac)  # macOS
        else:
            self.canvas.bind("<Button-4>", self.on_zoom)  # Linux scroll up
            self.canvas.bind("<Button-5>", self.on_zoom)  # Linux scroll down

        # Bind mouse events for panning with right-click press
        self.bind_panning_events()

        # Load and process the image
        self.image_discretization = ImageDiscretization(
            image_path, 'contour', [100, 255], False)

        # Retrieve contours and grayscale image (Not actually used `grays` here but for completeness)
        all_contours, grays = self.image_discretization.retrieve_contours_all_contours(
        )

        # Display the contours on the canvas
        self.display_contours(all_contours)

    def bind_panning_events(self):
        """
        Binds mouse events for panning with right-click press.
        """
        if platform.system(
        ) == 'Darwin':  # macOS might use Button-2 for right-click
            self.canvas.bind('<ButtonPress-2>', self.on_pan_start)
            self.canvas.bind('<B2-Motion>', self.on_pan_move)
        else:
            self.canvas.bind('<ButtonPress-3>', self.on_pan_start)
            self.canvas.bind('<B3-Motion>', self.on_pan_move)

    def on_pan_start(self, event):
        """
        Records the starting position for panning.
        """
        self.canvas.scan_mark(event.x, event.y)

    def on_pan_move(self, event):
        """
        Handles the panning motion.
        """
        self.canvas.scan_dragto(event.x, event.y, gain=1)

    def on_zoom(self, event):
        """
        Handles zooming in and out with the mouse wheel.
        """
        # Get the mouse position in canvas coordinates
        canvas = self.canvas
        x = canvas.canvasx(event.x)
        y = canvas.canvasy(event.y)

        if platform.system() == 'Windows':
            # Windows uses event.delta
            if event.delta > 0:
                scale_factor = 1.1
            elif event.delta < 0:
                scale_factor = 1 / 1.1
            else:
                return
        else:
            # Linux
            if event.num == 4:  # Scroll up
                scale_factor = 1.1
            elif event.num == 5:  # Scroll down
                scale_factor = 1 / 1.1
            else:
                return

        # Update the scale factor
        new_scale = self.scale * scale_factor
        new_scale = max(self.min_scale, min(self.max_scale, new_scale))
        scale_factor = new_scale / self.scale
        if scale_factor == 1:
            return  # No change in scale

        self.scale = new_scale

        # Redraw with new scale
        self.redraw_canvas()

        # Update the scroll region
        self.update_scrollregion()

    def on_zoom_mac(self, event):
        """
        Handles zooming for macOS which uses a different event handling for the mouse wheel.
        """
        # On macOS, event.delta may need a different approach, but similar logic:
        if event.delta > 0:
            scale_factor = 1.1
        elif event.delta < 0:
            scale_factor = 1 / 1.1
        else:
            return

        new_scale = self.scale * scale_factor
        new_scale = max(self.min_scale, min(self.max_scale, new_scale))
        if new_scale == self.scale:
            return

        self.scale = new_scale
        self.redraw_canvas()
        self.update_scrollregion()

    def update_scrollregion(self):
        """
        Updates the scroll region of the canvas based on the current scale.
        """
        if hasattr(self, 'original_pil_image'):
            scaled_width = int(self.original_pil_image.width * self.scale)
            scaled_height = int(self.original_pil_image.height * self.scale)
            self.canvas.config(scrollregion=(0, 0, scaled_width,
                                             scaled_height))
        else:
            # If for some reason original_pil_image not defined yet, fallback
            self.canvas.config(scrollregion=(0, 0, 800 * self.scale,
                                             600 * self.scale))

    def redraw_canvas(self):
        """
        Clears and redraws the canvas contents based on the current scale.
        Redraws the image at the current scale.
        """
        self.canvas.delete("all")
        if hasattr(self, 'original_pil_image'):
            # Scale the original PIL image according to self.scale
            scaled_width = int(self.original_pil_image.width * self.scale)
            scaled_height = int(self.original_pil_image.height * self.scale)
            scaled_image = self.original_pil_image.resize(
                (scaled_width, scaled_height), Image.Resampling.LANCZOS)

            photo = ImageTk.PhotoImage(scaled_image)
            self.photo_image = photo  # keep a reference
            self.canvas.create_image(0, 0, image=self.photo_image, anchor='nw')

    def display_contours(self, contours):
        """
        Displays the image with all contours drawn in different colors on the canvas.
        Each contour is drawn with a unique color for easy differentiation, and a large
        number is placed at the center of each contour indicating its index.
        """
        # Load the original image using OpenCV
        image = cv2.imread(self.image_path)
        if image is None:
            messagebox.showerror("Error",
                                 f"Failed to load image: {self.image_path}")
            self.window.destroy()
            return

        # Resize the original image to fit within 800x600 while maintaining the aspect ratio
        max_width, max_height = 800, 600
        original_height, original_width = image.shape[:2]
        scale_factor = min(max_width / original_width,
                           max_height / original_height)
        new_width = int(original_width * scale_factor)
        new_height = int(original_height * scale_factor)
        resized_image = cv2.resize(image, (new_width, new_height),
                                   interpolation=cv2.INTER_AREA)

        # Create a copy of the resized image to draw contours
        image_with_contours = resized_image.copy()

        # Generate unique colors for each contour
        colors = self.generate_unique_colors(len(contours))

        # Adjust contours to match the resized image dimensions
        resized_contours = [(contour * scale_factor).astype(np.int32)
                            for contour in contours]

        # Draw each contour with a unique color and add the contour index at its center
        for idx, contour in enumerate(resized_contours):
            cv2.drawContours(
                image_with_contours,
                [contour],
                -1,  # Draw all contours
                colors[idx],
                2  # Thickness of contour lines
            )
            # Calculate the center of the contour
            moments = cv2.moments(contour)
            if moments["m00"] != 0:
                center_x = int(moments["m10"] / moments["m00"])
                center_y = int(moments["m01"] / moments["m00"])
            else:
                # Fallback if contour area is zero
                center_x, center_y = contour[0][0]

            # Draw the contour index at the center of the contour
            cv2.putText(
                image_with_contours,
                f"#{idx}",  # Label for the contour
                (center_x, center_y),  # Position (center of the contour)
                cv2.FONT_HERSHEY_SIMPLEX,  # Font
                1.5,  # Font scale
                (125, 125, 125),  # Text color (gray for good contrast)
                thickness=3,  # Thickness of the text
                lineType=cv2.LINE_AA  # Anti-aliased text
            )

        # Convert the image from BGR (OpenCV format) to RGB (PIL format)
        image_rgb = cv2.cvtColor(image_with_contours, cv2.COLOR_BGR2RGB)

        # Convert the NumPy array to a PIL Image
        pil_image = Image.fromarray(image_rgb)

        # Store original_pil_image for future scaling
        self.original_pil_image = pil_image

        # Convert the PIL Image to an ImageTk PhotoImage
        self.photo_image = ImageTk.PhotoImage(pil_image)

        # Update the scroll region based on resized image size
        self.canvas.config(scrollregion=(0, 0, pil_image.width,
                                         pil_image.height))

        # Display the resized image on the canvas
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
