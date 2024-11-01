# image_creation.py

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import matplotlib.pyplot as plt
import utils


class ImageCreation:

    def __init__(self):
        pass

    def draw_points_on_image(self,
                             image_size,
                             linear_paths,
                             radius,
                             dot_color,
                             font_path,
                             font_size,
                             font_color,
                             debug=False):
        """
        Draws points at the vertices of each linear path and labels each point with a number on a transparent image.
        Labels are anchored based on their position (left, right, or center).
        Adds two additional positions directly above and below the dot, with labels justified in the center.
        Displays a debug image with lines connecting consecutive points only if debug=True.
        Returns only the main output image with dots and labels.
        """
        # Create the main output image with a transparent background
        blank_image_np, blank_image_pil, draw_pil, font = self.create_blank_image(
            image_size, font_path, font_size, transparent=True)

        # Step 1: Calculate potential positions for dots and labels
        dots, labels = self.calculate_dots_and_labels(linear_paths, radius,
                                                      font, draw_pil,
                                                      font_color)

        # Step 2: Check for overlaps and adjust positions
        labels = self.adjust_label_positions(labels, dots, draw_pil, font,
                                             image_size)

        # Step 3: Draw the dots and labels on the image
        final_image = self.draw_dots_and_labels(blank_image_np, dots, labels,
                                                radius, dot_color, font)

        # Step 4: Handle debug visualization if required
        if debug:
            self.display_debug_image_with_lines(blank_image_np, linear_paths,
                                                dots, labels, radius,
                                                dot_color, font)

        # Return the processed image, dots, and labels
        return final_image, dots, labels

    # Helper methods moved from the original dot_2_dot.py

    def create_blank_image(self,
                           image_size,
                           font_path,
                           font_size,
                           transparent=False):
        """
        Creates a blank image using PIL and sets up the drawing context with the specified font.
        The image can be either transparent or with a solid color background.
        """
        if transparent:
            blank_image_pil = Image.new(
                # Transparent
                "RGBA",
                (image_size[1], image_size[0]),
                (255, 255, 255, 0))
        else:
            blank_image_pil = Image.new(
                # White background
                "RGB",
                (image_size[1], image_size[0]),
                (255, 255, 255))
        draw_pil = ImageDraw.Draw(blank_image_pil)
        font = ImageFont.truetype(font_path, font_size)
        blank_image_np = np.array(blank_image_pil)
        return blank_image_np, blank_image_pil, draw_pil, font

    def calculate_dots_and_labels(self, linear_paths, radius, font, draw_pil,
                                  font_color):
        """
        Calculate the positions for dots and potential label positions based on the dot positions.
        """
        dots = []
        labels = []
        distance_from_dots = 1.2 * radius
        global_point_index = 1  # Global counter for labeling across all paths

        for path_index, path in enumerate(linear_paths):
            for point_index, point in enumerate(path):
                dot_box = (point[0] - radius, point[1] - radius,
                           point[0] + radius, point[1] + radius)
                dots.append((point, dot_box))
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
                labels.append((label, label_positions, font_color))

        return dots, labels

    def get_label_box(self, position, text, anchor, draw_pil, font):
        """Returns the bounding box of the label (x_min, y_min, x_max, y_max) depending on anchor."""
        bbox = draw_pil.textbbox(position, text, font=font, anchor=anchor)
        return bbox

    def adjust_label_positions(self, labels, dots, draw_pil, font, image_size):
        """
        Check for overlaps between labels and dots and adjust the positions of the labels.
        Ensure that labels are not placed outside the image boundaries.
        """

        def does_overlap(box1, box2):
            """Check if two bounding boxes overlap."""
            return not (box1[2] < box2[0] or box1[0] > box2[2]
                        or box1[3] < box2[1] or box1[1] > box2[3])

        def is_within_bounds(box, image_size):
            """Check if the bounding box is within the image boundaries."""
            return (0 <= box[0] <= image_size[1]
                    and  # x_min >= 0 and within width
                    0 <= box[1] <= image_size[0]
                    and  # y_min >= 0 and within height
                    0 <= box[2] <= image_size[1] and  # x_max within width
                    0 <= box[3] <= image_size[0])  # y_max within height

        # Step 1: Precompute all label bounding boxes
        precomputed_label_boxes = []
        for idx, (label, positions, color) in enumerate(labels):
            position_boxes = []
            for pos_idx, (pos, anchor) in enumerate(positions):
                box = self.get_label_box(pos, label, anchor, draw_pil, font)
                position_boxes.append(box)
            precomputed_label_boxes.append(position_boxes)

        # Step 2: Precompute all current label bounding boxes to check overlaps
        current_label_boxes = [boxes[0] for boxes in precomputed_label_boxes
                               ]  # Assuming first position initially

        # Step 3: Iterate through each label and adjust positions
        for i, (label, positions, color) in enumerate(labels):
            valid_positions = []
            all_positions_info = []

            for pos_idx, (pos, anchor) in enumerate(positions):
                label_box = precomputed_label_boxes[i][pos_idx]
                # Check overlap with dots
                overlaps_with_dots = any(
                    does_overlap(label_box, dot[1]) for dot in dots)
                # Check overlap with other labels
                overlaps_with_labels = any(
                    does_overlap(label_box, current_label_boxes[j])
                    for j in range(len(labels)) if j != i)
                overlaps = overlaps_with_dots or overlaps_with_labels

                within_bounds = is_within_bounds(label_box, image_size)

                distance = ((pos[0] - dots[i][0][0])**2 +
                            (pos[1] - dots[i][0][1])**2)**0.5
                all_positions_info.append((pos, distance, overlaps, anchor))

                if not overlaps and within_bounds:
                    valid_positions.append((pos, anchor, pos_idx))

            if valid_positions:
                # Choose the closest non-overlapping position
                best_position, best_anchor, best_pos_idx = min(
                    valid_positions,
                    key=lambda p: all_positions_info[p[2]][
                        1]  # Sort by distance
                )
                labels[i] = (label, [(best_position, best_anchor)], color)
                current_label_boxes[i] = precomputed_label_boxes[i][
                    best_pos_idx]
            else:
                print(
                    f"Warning: Label {label} overlaps at all positions or is out of bounds"
                )
                # Red color for all positions in case of overlap or out-of-bounds
                labels[i] = (label, positions, (255, 0, 0))

        return labels

    def draw_dots_and_labels(self, blank_image_np, dots, labels, radius,
                             dot_color, font):
        """
        Draws dots and labels on the main image using PIL for both.
        """
        # Convert the NumPy array to a PIL image
        blank_image_pil = Image.fromarray(blank_image_np)
        draw_pil = ImageDraw.Draw(blank_image_pil)

        # Draw the dots using PIL
        for point, _ in dots:
            # Draw an ellipse as a dot (PIL equivalent of a circle)
            upper_left = (point[0] - radius, point[1] - radius)
            bottom_right = (point[0] + radius, point[1] + radius)
            draw_pil.ellipse([upper_left, bottom_right], fill=dot_color)

        # Draw the labels using PIL
        for label, positions, color in labels:
            if color == (255, 0, 0):  # If it's a red label (overlap warning)
                for pos, anchor in positions:
                    draw_pil.text(pos,
                                  label,
                                  font=font,
                                  fill=color,
                                  anchor=anchor)
            else:
                draw_pil.text(positions[0][0],
                              label,
                              font=font,
                              fill=color,
                              anchor=positions[0][1])

        # Convert back to NumPy array for the final image
        return np.array(blank_image_pil)

    def display_debug_image_with_lines(self, blank_image_np, linear_paths,
                                       dots, labels, radius, dot_color, font):
        """
        Displays a debug image with lines connecting consecutive points, dots, and labels.
        Alternates line color: odd lines are red, even lines are blue.
        Uses PIL for drawing both the dots and the labels.
        """
        # Convert the NumPy array to a PIL image for consistent drawing
        debug_image_pil = Image.fromarray(blank_image_np)
        draw_debug_pil = ImageDraw.Draw(debug_image_pil)

        # Draw lines between consecutive points on the debug image
        for path in linear_paths:
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

        # Draw dots on the debug image using PIL
        for point, _ in dots:
            upper_left = (point[0] - radius, point[1] - radius)
            bottom_right = (point[0] + radius, point[1] + radius)
            draw_debug_pil.ellipse([upper_left, bottom_right], fill=dot_color)

        # Add labels to the debug image
        for label, positions, color in labels:
            if color == (255, 0, 0):  # If it's a red label (overlap warning)
                for pos, anchor in positions:
                    draw_debug_pil.text(pos,
                                        label,
                                        font=font,
                                        fill=color,
                                        anchor=anchor)
            else:
                draw_debug_pil.text(positions[0][0],
                                    label,
                                    font=font,
                                    fill=color,
                                    anchor=positions[0][1])

        # Convert the PIL image back to a NumPy array for display
        final_debug_image = np.array(debug_image_pil)

        # Display the debug image with lines, dots, and labels
        utils.display_with_matplotlib(
            final_debug_image, 'Debug Image with Dots, Lines, and Labels')
