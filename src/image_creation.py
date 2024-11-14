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
        self, input_path
    ) -> Tuple[np.ndarray, List[Tuple[Tuple[int, int], Tuple[
            int, int, int, int]]], List[Tuple[str, List[Tuple[Tuple[
                int, int], str]], Tuple[int, int, int]]], np.ndarray,
               List[int]]:  # Adding List[int] for invalid indices
        """
        Draws points and returns invalid label indices as part of the output.
        """
        blank_image_np, blank_image_pil, draw_pil, font = self._create_blank_image(
        )
        self.dots, self.labels = self._calculate_dots_and_labels(
            draw_pil, font)
        self.labels, invalid_indices = self._adjust_label_positions(
            draw_pil, font, blank_image_pil)
        final_image = self._draw_dots_and_labels(blank_image_pil)
        final_image_np = np.array(final_image)
        combined_image_np = self.create_combined_image_with_background_and_lines(
            input_path, final_image)

        if self.debug:
            self._display_debug_image_with_lines(blank_image_np)

        return final_image_np, self.dots, self.labels, combined_image_np, invalid_indices

    def create_combined_image_with_background_and_lines(
            self, input_path: str, final_image: Image.Image) -> np.ndarray:
        """
        Creates an image that overlays the final image on top of the input image with opacity set to 0.1.
        Also adds red lines connecting successive dots.

        Args:
            input_path (str): Path to the input image to be used as the background.
            final_image (Image.Image): The image with dots and labels.

        Returns:
            np.ndarray: Image with the input image as background and red lines connecting dots.
        """
        # Load the input image
        input_image = Image.open(input_path).convert("RGBA")
        input_image = input_image.resize(
            (self.image_size[1], self.image_size[0]))
        input_image_np = np.array(input_image)

        # Adjust the opacity of the input image
        input_image_np[...,
                       3] = (input_image_np[..., 3] * 0.1).astype(np.uint8)
        input_image_with_opacity = Image.fromarray(input_image_np)

        # Overlay the final image on top of the input image with opacity
        combined_image = Image.alpha_composite(input_image_with_opacity,
                                               final_image)
        draw_combined = ImageDraw.Draw(combined_image)

        # Draw red lines connecting each successive dot
        for path in self.linear_paths:
            for i in range(1, len(path)):
                draw_combined.line([path[i - 1], path[i]],
                                   fill=(255, 0, 0),
                                   width=2)

        # Convert the combined image to a NumPy array
        combined_image_np = np.array(combined_image)

        return combined_image_np

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
    ) -> Tuple[List[Tuple[str, List[Tuple[Tuple[int, int], str]], Tuple[
            int, int, int]]], List[int]]:
        """
        Adjusts label positions to prevent overlaps and ensure labels are within image bounds.
        Also tracks indices of labels without suitable positions.
        
        Returns:
            - Adjusted labels list.
            - List of indices where no suitable position was found.
        """

        def does_overlap(box1, box2):
            return not (box1[2] < box2[0] or box1[0] > box2[2]
                        or box1[3] < box2[1] or box1[1] > box2[3])

        def is_within_bounds(box, image_size):
            return (0 <= box[0] <= image_size[1]
                    and 0 <= box[1] <= image_size[0]
                    and 0 <= box[2] <= image_size[1]
                    and 0 <= box[3] <= image_size[0])

        image_size = self.image_size
        precomputed_label_boxes = [[
            self._get_label_box(pos, label, anchor, draw_pil, font)
            for pos, anchor in positions
        ] for label, positions, color in self.labels]
        occupied_boxes = [dot_box for _, dot_box in self.dots]
        adjusted_labels = []
        invalid_indices = []  # List to hold indices with no valid position

        for idx, (label, positions, color) in enumerate(self.labels):
            valid_position_found = False
            for pos_idx, (pos, anchor) in enumerate(positions):
                label_box = precomputed_label_boxes[idx][pos_idx]
                overlaps = any(
                    does_overlap(label_box, occupied_box)
                    for occupied_box in occupied_boxes)
                within_bounds = is_within_bounds(label_box, image_size)
                if not overlaps and within_bounds:
                    adjusted_labels.append((label, [(pos, anchor)], color))
                    occupied_boxes.append(label_box)
                    valid_position_found = True
                    break

            if not valid_position_found:
                # If no valid position, append the original positions and mark index as problematic
                invalid_indices.append(idx)
                adjusted_labels.append((label, positions, (255, 0, 0)))

        return adjusted_labels, invalid_indices

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
