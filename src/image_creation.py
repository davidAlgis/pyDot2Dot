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
        # Set default label data
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

            # Add possible label positions directly to the Dot object with explicit keys
            dot.add_possible_label_position(
                (dot.position[0] + distance_from_dots,
                 dot.position[1] - distance_from_dots), "ls")  # Top-right
            dot.add_possible_label_position(
                (dot.position[0] + distance_from_dots,
                 dot.position[1] + distance_from_dots), "rs")  # Bottom-right
            dot.add_possible_label_position(
                (dot.position[0] - distance_from_dots,
                 dot.position[1] - distance_from_dots), "ls")  # Top-left
            dot.add_possible_label_position(
                (dot.position[0] - distance_from_dots,
                 dot.position[1] + distance_from_dots), "rs")  # Bottom-left
            dot.add_possible_label_position(
                (dot.position[0], dot.position[1] - 2 * distance_from_dots),
                "ms")  # Directly above
            dot.add_possible_label_position(
                (dot.position[0], dot.position[1] + 3 * distance_from_dots),
                "ms")  # Directly below

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
        Adjusts label positions for all dots in self.dots to prevent overlaps with other dots
        or labels and ensure labels are within image bounds. Updates the label position
        and overlap status of each dot.

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
        occupied_boxes = []  # Track occupied areas (dots + labels)
        invalid_indices = []  # Indices of dots with no valid label positions

        # Precompute the bounding boxes of all dots
        for dot in self.dots:
            dot_box = [
                dot.position[0] - dot.radius, dot.position[1] - dot.radius,
                dot.position[0] + dot.radius, dot.position[1] + dot.radius
            ]
            occupied_boxes.append(dot_box)

        for idx, dot in enumerate(self.dots):
            valid_position_found = False

            # Set a default position from the first possible position
            if dot.label.possible_position:
                default_possible_position = dot.label.possible_position[0]
                dot.label.position = default_possible_position["position"]
                dot.label.anchor = default_possible_position["anchor"]

            for pos_data in dot.label.possible_position:
                pos = pos_data["position"]
                anchor = pos_data["anchor"]

                # Compute the bounding box for the label at the current position
                label_box = self._get_label_box(pos, str(dot.dot_id), anchor,
                                                draw_pil, font)

                # Check if this position is valid
                overlaps = any(
                    does_overlap(label_box, occupied_box)
                    for occupied_box in occupied_boxes)
                within_bounds = is_within_bounds(label_box, image_size)

                if not overlaps and within_bounds:
                    # Update the dot's label position and anchor
                    dot.label.position = pos
                    dot.label.anchor = anchor
                    # Add the label box to occupied boxes
                    occupied_boxes.append(label_box)
                    dot.overlap_other_dots = False  # Mark as not overlapping
                    valid_position_found = True
                    break

            if not valid_position_found:
                # Mark the dot as having an invalid label position
                invalid_indices.append(idx)
                dot.label.color = (0, 0, 255, 255)  # Mark label color as blue
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
            if dot.position and dot.radius > 0:
                # Convert to plain integers
                upper_left = (
                    int(dot.position[0] - dot.radius),
                    int(dot.position[1] - dot.radius),
                )
                bottom_right = (
                    int(dot.position[0] + dot.radius),
                    int(dot.position[1] + dot.radius),
                )
                draw_pil.ellipse([upper_left, bottom_right],
                                 fill=(0, 0, 0, 255))
            else:
                print(f"Skipping invalid dot: {dot}")

        # Draw the labels
        color_overlap = (255, 0, 0)
        for dot in self.dots:
            draw_pil.text(
                dot.label.position,
                str(dot.dot_id),
                font=self._get_font(),
                fill=dot.label.color,
                anchor=dot.label.anchor,  # Default anchor can be adjusted
            )
            print(
                f"Drawing label id = {str(dot.dot_id)} at: {dot.label.position}, Anchor={dot.label.anchor}"
            )

        return image

    def _get_font(self) -> ImageFont.FreeTypeFont:
        """
        Loads and returns the font object.

        Returns:
            ImageFont.FreeTypeFont: Loaded font object.
        """
        return ImageFont.truetype(self.font_path, self.font_size)
