# image_creation.py

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import matplotlib.pyplot as plt
import utils
from dot import Dot
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
        dots: List[Dot],
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
        self.dots = dots
        self.radius = radius
        self.dot_color = dot_color
        self.font_path = font_path
        self.font_size = font_size
        self.font_color = font_color

        self.debug = debug

        for dot in self.dots:
            distance_from_dots = 1.2 * self.radius  # Distance for label placement
            position_label = (dot.position[0] + distance_from_dots,
                              dot.position[1] - distance_from_dots)
            dot.set_label(position_label, font_color, font_path, font_size)

        # Initialize labels and dots
        # self.dots: List[Tuple[Tuple[int, int], Tuple[int, int, int, int]]] = []
        # self.labels: List[Tuple[str, List[Tuple[Tuple[int, int], str]],
        #                         Tuple[int, int, int]]] = []

    def draw_points_on_image(
            self,
            input_path) -> Tuple[np.ndarray, List[Dot], np.ndarray, List[int]]:
        """
        Draws points and returns invalid label indices as part of the output.

        Args:
            input_path (str): Path to the input image.

        Returns:
            Tuple containing:
                - Final image as a NumPy array.
                - Updated list of Dot objects.
                - Combined image with background and dots as a NumPy array.
                - List of invalid label indices.
        """
        # Create a blank image
        blank_image_np, blank_image_pil, draw_pil, font = self._create_blank_image(
        )

        # Calculate dots and their potential label positions
        self._calculate_dots_and_labels(draw_pil, font)

        # Adjust label positions and retrieve invalid indices
        invalid_indices = self._adjust_label_positions(draw_pil, font,
                                                       blank_image_pil)

        # Draw dots and labels on the blank image
        final_image = self._draw_dots_and_labels(blank_image_pil)
        final_image_np = np.array(final_image)

        # Create a combined image with the input image as the background
        combined_image_np = self.create_combined_image_with_background_and_lines(
            input_path, final_image)

        # Debug: Display intermediate results
        if self.debug:
            self._display_debug_image_with_lines(blank_image_np)

        return final_image_np, self.dots, combined_image_np, invalid_indices

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
        for i in range(1, len(self.dots)):
            previous_dot = self.dots[i - 1]
            current_dot = self.dots[i]
            draw_combined.line([previous_dot.position, current_dot.position],
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

    def _calculate_dots_and_labels(self, draw_pil: ImageDraw.Draw,
                                   font: ImageFont.FreeTypeFont):
        """
        Updates the positions for dots and potential label positions directly based on `self.dots`.

        Args:
            draw_pil (ImageDraw.Draw): PIL ImageDraw object for text measurements.
            font (ImageFont.FreeTypeFont): PIL ImageFont object for text measurements.

        Updates:
            - Updates `self.dots` with potential label positions directly in the Dot objects.
        """
        distance_from_dots = 1.2 * self.radius  # Distance for label placement
        for dot in self.dots:
            # Clear any existing label positions to avoid duplication
            dot.label.possible_position = []

            # Add possible label positions directly to the Dot object
            dot.add_possible_label_position(
                ((dot.position[0] + distance_from_dots,
                  dot.position[1] - distance_from_dots), "ls")  # Top-right
            )
            dot.add_possible_label_position(
                ((dot.position[0] + distance_from_dots,
                  dot.position[1] + distance_from_dots), "ls")  # Bottom-right
            )
            dot.add_possible_label_position(
                ((dot.position[0] - distance_from_dots,
                  dot.position[1] - distance_from_dots), "rs")  # Top-left
            )
            dot.add_possible_label_position(
                ((dot.position[0] - distance_from_dots,
                  dot.position[1] + distance_from_dots), "rs")  # Bottom-left
            )
            dot.add_possible_label_position(
                ((dot.position[0], dot.position[1] - 2 * distance_from_dots),
                 "ms")  # Directly above
            )
            dot.add_possible_label_position(
                ((dot.position[0], dot.position[1] + 3 * distance_from_dots),
                 "ms")  # Directly below
            )

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

    def _adjust_label_positions(self, draw_pil: ImageDraw.Draw,
                                font: ImageFont.FreeTypeFont,
                                image: Image.Image) -> List[int]:
        """
        Adjusts label positions for all dots in self.dots to prevent overlaps and ensure labels are within image bounds.
        Updates the label position and overlap status of each dot.

        Returns:
            - List of indices of dots where no suitable label position was found.
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
        occupied_boxes = []  # Track occupied areas on the image
        invalid_indices = []  # Indices of dots with no valid label positions

        for idx, dot in enumerate(self.dots):
            valid_position_found = False
            for pos, anchor in dot.label.possible_position:
                # Compute the bounding box for the label at the current position
                label_box = self._get_label_box(pos, str(dot.dot_id), anchor,
                                                draw_pil, font)

                # Check if this position is valid
                overlaps = any(
                    does_overlap(label_box, occupied_box)
                    for occupied_box in occupied_boxes)
                within_bounds = is_within_bounds(label_box, image_size)

                if not overlaps and within_bounds:
                    # Update the dot's label position
                    dot.label.position = pos
                    # Add the label box to occupied boxes
                    occupied_boxes.append(label_box)
                    dot.overlap_other_dots = False  # Mark as not overlapping
                    valid_position_found = True
                    break

            if not valid_position_found:
                # Mark the dot as having an invalid label position
                invalid_indices.append(idx)
                dot.label.position = None  # No valid position found
                dot.overlap_other_dots = True  # Mark as overlapping

        return invalid_indices

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
        for dot in self.dots:
            upper_left = (dot.position[0] - dot.radius,
                          dot.position[1] - dot.radius)
            bottom_right = (dot.position[0] + dot.radius,
                            dot.position[1] + dot.radius)
            draw_pil.ellipse([upper_left, bottom_right], fill=dot.color)

        # Draw the labels
        for dot in self.dots:
            if dot.label and dot.label.position:
                # Draw the label at the valid position
                draw_pil.text(
                    dot.label.position,
                    str(dot.dot_id),
                    font=self._get_font(),
                    fill=dot.label.color,
                    anchor="ms",  # Default anchor can be adjusted
                )
            elif dot.overlap_other_dots:
                # Optional: Mark overlapping labels in red
                draw_pil.text(
                    (dot.position[0] + dot.radius * 1.5, dot.position[1]),
                    str(dot.dot_id),
                    font=self._get_font(),
                    fill=(255, 0, 0),  # Red color for overlap
                    anchor="ms",
                )

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
