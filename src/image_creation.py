# image_creation.py

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import matplotlib.pyplot as plt
import utils
from typing import List, Tuple, Optional, Any


class ImageCreation:
    """
    A class to handle the creation of images with annotated dots and labels based on linear paths.

    Attributes:
        image_size (Tuple[int, int]): Size of the image as (height, width).
        linear_paths (List[List[Tuple[int, int]]]): List of linear paths, each path is a list of (x, y) tuples.
        radius (int): Radius of the dots to be drawn.
        dot_color (Tuple[int, int, int]): Color of the dots in RGB.
        font_path (str): Path to the font file used for labels.
        font_size (int): Size of the font for labels.
        font_color (Tuple[int, int, int]): Color of the font in RGB.
        debug (bool): Flag to enable or disable debug mode.
    """

    def __init__(
        self,
        image_size: Tuple[int, int],
        linear_paths: List[List[Tuple[int, int]]],
        radius: int,
        dot_color: Tuple[int, int, int],
        font_path: str,
        font_size: int,
        font_color: Tuple[int, int, int],
        debug: bool = False,
    ):
        """
        Initializes the ImageCreation instance with the given parameters.

        Args:
            image_size (Tuple[int, int]): Size of the image as (height, width).
            linear_paths (List[List[Tuple[int, int]]]): List of linear paths, each path is a list of (x, y) tuples.
            radius (int): Radius of the dots to be drawn.
            dot_color (Tuple[int, int, int]): Color of the dots in RGB.
            font_path (str): Path to the font file used for labels.
            font_size (int): Size of the font for labels.
            font_color (Tuple[int, int, int]): Color of the font in RGB.
            debug (bool): Flag to enable or disable debug mode.
        """
        self.image_size = image_size
        self.linear_paths = linear_paths
        self.radius = radius
        self.dot_color = dot_color
        self.font_path = font_path
        self.font_size = font_size
        self.font_color = font_color
        self.debug = debug

        # Initialize labels and dots
        self.dots: List[Tuple[Tuple[int, int], Tuple[int, int, int, int]]] = []
        self.labels: List[Tuple[str, List[Tuple[Tuple[int, int], str]],
                                Tuple[int, int, int]]] = []

    def draw_points_on_image(
        self
    ) -> Tuple[np.ndarray, List[Tuple[Tuple[int, int], Tuple[
            int, int, int, int]]], List[Tuple[str, List[Tuple[Tuple[
                int, int], str]], Tuple[int, int, int]]]]:
        """
        Draws points at the vertices of each linear path and labels each point with a number on a transparent image.
        Labels are anchored based on their position (left, right, or center).
        Adds two additional positions directly above and below the dot, with labels justified in the center.
        Displays a debug image with lines connecting consecutive points only if debug=True.

        Returns:
            Tuple[np.ndarray, List[Tuple[Tuple[int, int], Tuple[int, int, int, int]]], List[Tuple[str, List[Tuple[Tuple[int, int], str]], Tuple[int, int, int]]]]:
                - The final image as a NumPy array with dots and labels.
                - List of dots with their positions and bounding boxes.
                - List of labels with their text, possible positions, and colors.
        """
        # Step 1: Create a blank image with a transparent background
        blank_image_np, blank_image_pil, draw_pil, font = self._create_blank_image(
        )

        # Step 2: Calculate positions for dots and labels
        self.dots, self.labels = self._calculate_dots_and_labels(
            draw_pil, font)

        # Step 3: Adjust label positions to prevent overlaps and ensure they are within image bounds
        self.labels = self._adjust_label_positions(draw_pil, font,
                                                   blank_image_pil)

        # Step 4: Draw the dots and labels on the image
        final_image = self._draw_dots_and_labels(blank_image_pil)

        # Step 5: Handle debug visualization if required
        if self.debug:
            self._display_debug_image_with_lines(blank_image_np)

        # Convert final image back to NumPy array
        final_image_np = np.array(final_image)

        return final_image_np, self.dots, self.labels

    def _create_blank_image(
        self
    ) -> Tuple[np.ndarray, Image.Image, ImageDraw.Draw,
               ImageFont.FreeTypeFont]:
        """
        Creates a blank image using PIL and sets up the drawing context with the specified font.
        The image has a transparent background.

        Returns:
            Tuple containing:
                - NumPy array representation of the blank image.
                - PIL Image object.
                - PIL ImageDraw object.
                - PIL ImageFont object.
        """
        blank_image_pil = Image.new(
            "RGBA",
            (self.image_size[1], self.image_size[0]),
            (255, 255, 255, 0)  # Transparent background
        )
        draw_pil = ImageDraw.Draw(blank_image_pil)
        font = ImageFont.truetype(self.font_path, self.font_size)
        blank_image_np = np.array(blank_image_pil)
        return blank_image_np, blank_image_pil, draw_pil, font

    def _calculate_dots_and_labels(
        self, draw_pil: ImageDraw.Draw, font: ImageFont.FreeTypeFont
    ) -> Tuple[List[Tuple[Tuple[int, int], Tuple[int, int, int, int]]],
               List[Tuple[str, List[Tuple[Tuple[int, int], str]], Tuple[
                   int, int, int]]]]:
        """
        Calculate the positions for dots and potential label positions based on the dot positions.

        Args:
            draw_pil (ImageDraw.Draw): PIL ImageDraw object for text measurements.
            font (ImageFont.FreeTypeFont): PIL ImageFont object for text measurements.

        Returns:
            Tuple containing:
                - List of dots with their positions and bounding boxes.
                - List of labels with their text, possible positions, and colors.
        """
        dots = []
        labels = []
        distance_from_dots = 1.2 * self.radius
        global_point_index = 1  # Global counter for labeling across all paths

        for path in self.linear_paths:
            for point in path:
                # Define the bounding box for the dot
                dot_box = (point[0] - self.radius, point[1] - self.radius,
                           point[0] + self.radius, point[1] + self.radius)
                dots.append((point, dot_box))

                # Define the label
                label = str(global_point_index)
                global_point_index += 1

                # Define possible label positions around the dot
                label_positions = [
                    ((point[0] + distance_from_dots,
                      point[1] - distance_from_dots), "ls"),  # top-right
                    ((point[0] + distance_from_dots,
                      point[1] + distance_from_dots), "ls"),  # bottom-right
                    ((point[0] - distance_from_dots,
                      point[1] - distance_from_dots), "rs"),  # top-left
                    ((point[0] - distance_from_dots,
                      point[1] + distance_from_dots), "rs"),  # bottom-left
                    ((point[0], point[1] - 2 * distance_from_dots),
                     "ms"),  # directly above
                    ((point[0], point[1] + 3 * distance_from_dots), "ms"
                     )  # directly below
                ]
                labels.append((label, label_positions, self.font_color))

        return dots, labels

    def _get_label_box(
            self, position: Tuple[int, int], text: str, anchor: str,
            draw_pil: ImageDraw.Draw,
            font: ImageFont.FreeTypeFont) -> Tuple[int, int, int, int]:
        """
        Returns the bounding box of the label (x_min, y_min, x_max, y_max) depending on anchor.

        Args:
            position (Tuple[int, int]): Position where the text is to be drawn.
            text (str): The text of the label.
            anchor (str): The anchor position for the text.
            draw_pil (ImageDraw.Draw): PIL ImageDraw object for text measurements.
            font (ImageFont.FreeTypeFont): PIL ImageFont object for text measurements.

        Returns:
            Tuple[int, int, int, int]: Bounding box of the text.
        """
        bbox = draw_pil.textbbox(position, text, font=font, anchor=anchor)
        return bbox

    def _adjust_label_positions(
        self, draw_pil: ImageDraw.Draw, font: ImageFont.FreeTypeFont,
        image: Image.Image
    ) -> List[Tuple[str, List[Tuple[Tuple[int, int], str]], Tuple[int, int,
                                                                  int]]]:
        """
        Check for overlaps between labels and dots and adjust the positions of the labels.
        Ensure that labels are not placed outside the image boundaries.

        Args:
            draw_pil (ImageDraw.Draw): PIL ImageDraw object for text measurements.
            font (ImageFont.FreeTypeFont): PIL ImageFont object for text measurements.
            image (Image.Image): PIL Image object representing the image.

        Returns:
            List[Tuple[str, List[Tuple[Tuple[int, int], str]], Tuple[int, int, int]]]: 
                Adjusted list of labels with their selected positions and colors.
        """

        def does_overlap(box1: Tuple[int, int, int, int],
                         box2: Tuple[int, int, int, int]) -> bool:
            """Check if two bounding boxes overlap."""
            return not (box1[2] < box2[0] or box1[0] > box2[2]
                        or box1[3] < box2[1] or box1[1] > box2[3])

        def is_within_bounds(box: Tuple[int, int, int, int],
                             image_size: Tuple[int, int]) -> bool:
            """Check if the bounding box is within the image boundaries."""
            return (0 <= box[0] <= image_size[1]
                    and 0 <= box[1] <= image_size[0]
                    and 0 <= box[2] <= image_size[1]
                    and 0 <= box[3] <= image_size[0])

        image_size = self.image_size

        # Step 1: Precompute all label bounding boxes
        precomputed_label_boxes = []
        for label, positions, color in self.labels:
            position_boxes = []
            for pos, anchor in positions:
                box = self._get_label_box(pos, label, anchor, draw_pil, font)
                position_boxes.append(box)
            precomputed_label_boxes.append(position_boxes)

        # Step 2: Initialize list to keep track of occupied label areas
        occupied_boxes = [dot_box for _, dot_box in self.dots]

        # Step 3: Iterate through each label and select a valid position
        adjusted_labels = []
        for idx, (label, positions, color) in enumerate(self.labels):
            valid_position_found = False
            for pos_idx, (pos, anchor) in enumerate(positions):
                label_box = precomputed_label_boxes[idx][pos_idx]
                # Check overlap with dots and previously placed labels
                overlaps = any(
                    does_overlap(label_box, occupied_box)
                    for occupied_box in occupied_boxes)
                within_bounds = is_within_bounds(label_box, image_size)
                if not overlaps and within_bounds:
                    # Position is valid
                    adjusted_labels.append((label, [(pos, anchor)], color))
                    occupied_boxes.append(label_box)
                    valid_position_found = True
                    break
            if not valid_position_found:
                print(
                    f"Warning: Label '{label}' overlaps at all positions or is out of bounds."
                )
                # Assign original positions with red color to indicate warning
                adjusted_labels.append(
                    (label, positions,
                     (255, 0, 0)))  # Red color for problematic labels

        return adjusted_labels

    def _draw_dots_and_labels(self, image: Image.Image) -> Image.Image:
        """
        Draws dots and labels on the main image using PIL.

        Args:
            image (Image.Image): PIL Image object to draw on.

        Returns:
            Image.Image: PIL Image object with drawn dots and labels.
        """
        draw_pil = ImageDraw.Draw(image)

        # Draw the dots
        for point, _ in self.dots:
            upper_left = (point[0] - self.radius, point[1] - self.radius)
            bottom_right = (point[0] + self.radius, point[1] + self.radius)
            draw_pil.ellipse([upper_left, bottom_right], fill=self.dot_color)

        # Draw the labels
        for label, positions, color in self.labels:
            if len(positions) == 1:
                pos, anchor = positions[0]
                draw_pil.text(pos,
                              label,
                              font=self._get_font(),
                              fill=color,
                              anchor=anchor)
            else:
                # If label has multiple positions due to overlap, draw all in red
                for pos, anchor in positions:
                    draw_pil.text(pos,
                                  label,
                                  font=self._get_font(),
                                  fill=color,
                                  anchor=anchor)

        return image

    def _get_font(self) -> ImageFont.FreeTypeFont:
        """
        Loads and returns the font object.

        Returns:
            ImageFont.FreeTypeFont: Loaded font object.
        """
        return ImageFont.truetype(self.font_path, self.font_size)

    def _display_debug_image_with_lines(self,
                                        blank_image_np: np.ndarray) -> None:
        """
        Displays a debug image with lines connecting consecutive points, dots, and labels.
        Alternates line color: odd lines are red, even lines are blue.

        Args:
            blank_image_np (np.ndarray): NumPy array representation of the blank image.
        """
        # Convert the NumPy array to a PIL image for consistent drawing
        debug_image_pil = Image.fromarray(blank_image_np)
        draw_debug_pil = ImageDraw.Draw(debug_image_pil)

        # Draw lines between consecutive points on the debug image
        for path in self.linear_paths:
            for i, point in enumerate(path):
                if i > 0:
                    prev_point = path[i - 1]
                    # Alternate colors: red for odd, blue for even
                    line_color = (255, 0, 0) if (i % 2 == 1) else (
                        0, 0, 255)  # Red for odd, blue for even
                    # Draw line between prev_point and point
                    draw_debug_pil.line([prev_point, point],
                                        fill=line_color,
                                        width=2)

        # Draw dots on the debug image
        for point, _ in self.dots:
            upper_left = (point[0] - self.radius, point[1] - self.radius)
            bottom_right = (point[0] + self.radius, point[1] + self.radius)
            draw_debug_pil.ellipse([upper_left, bottom_right],
                                   fill=self.dot_color)

        # Add labels to the debug image
        for label, positions, color in self.labels:
            if len(positions) == 1:
                pos, anchor = positions[0]
                draw_debug_pil.text(pos,
                                    label,
                                    font=self._get_font(),
                                    fill=color,
                                    anchor=anchor)
            else:
                # If label has multiple positions due to overlap, draw all in red
                for pos, anchor in positions:
                    draw_debug_pil.text(pos,
                                        label,
                                        font=self._get_font(),
                                        fill=color,
                                        anchor=anchor)

        # Convert the PIL image back to a NumPy array for display
        final_debug_image = np.array(debug_image_pil)

        # Display the debug image with lines, dots, and labels
        utils.display_with_matplotlib(
            final_debug_image, 'Debug Image with Dots, Lines, and Labels')
