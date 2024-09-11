import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from utils import resize_for_debug, point_distance, insert_midpoints, filter_close_points, display_with_matplotlib


def retrieve_contours(image_path, debug=False):
    """
    Retrieves the contours found in the image and displays intermediate steps if debug is enabled.
    """
    from utils import remove_iccp_profile, handle_alpha_channel

    corrected_image_path = remove_iccp_profile(image_path)
    image = cv2.imread(corrected_image_path, cv2.IMREAD_UNCHANGED)

    if image is None:
        raise FileNotFoundError(
            f"Image file '{image_path}' could not be found or the path is incorrect.")

    image = handle_alpha_channel(image, debug=debug)

    if debug:
        debug_image = resize_for_debug(image)
        display_with_matplotlib(debug_image, 'Original Image')

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 100, 255, cv2.THRESH_BINARY_INV)
    contours, _ = cv2.findContours(
        binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_TC89_L1)

    if not contours:
        raise ValueError("No contours were found in the image.")

    if debug:
        debug_image = image.copy()
        cv2.drawContours(debug_image, contours, -1, (0, 255, 0), 1)
        debug_image = resize_for_debug(debug_image)
        display_with_matplotlib(debug_image, 'Contours on Image')

    return contours


def contour_to_linear_paths(contours, epsilon_factor=0.001, max_distance=10, min_distance=0, image=None, debug=False):
    """
    Converts each contour into a sequence of dominant points and inserts midpoints if needed.
    Optionally removes points that are closer than the specified minimum distance.
    """
    dominant_points_list = []

    for contour in contours:
        epsilon = epsilon_factor * cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, epsilon, True)
        area = cv2.contourArea(approx)

        if area > 0:
            approx = approx[::-1]

        dominant_points = [(point[0][0], point[0][1]) for point in approx]
        refined_points = dominant_points
        if max_distance > 0:
            refined_points = insert_midpoints(dominant_points, max_distance)

        if min_distance > 0:
            refined_points = filter_close_points(refined_points, min_distance)

        dominant_points_list.append(refined_points)

        if debug and image is not None:
            for point in refined_points:
                cv2.circle(image, point, 5, (0, 0, 255), -1)

    if debug and image is not None:
        debug_image = resize_for_debug(image)
        display_with_matplotlib(
            debug_image, 'Dominant Points with Max and Min Distance on Image')

    return dominant_points_list


def draw_points_on_image(image_size, linear_paths, radius, dot_color, font_path, font_size, font_color, debug=False):
    """
    Draws points at the vertices of each linear path and labels each point with a number on a blank image.
    Labels are anchored based on their position (left, right, or center).
    Adds two additional positions directly above and below the dot, with labels justified in the center.
    Displays a debug image with lines connecting consecutive points only if debug=True.
    Returns only the main output image with dots and labels.
    """
    # Create the main output image
    blank_image_np, blank_image_pil, draw_pil, font = create_blank_image(
        image_size, font_path, font_size)

    # Step 1: Calculate potential positions for dots and labels
    dots, labels = calculate_dots_and_labels(
        linear_paths, radius, font, draw_pil, font_color)

    # Step 2: Check for overlaps and adjust positions
    labels = adjust_label_positions(labels, dots, draw_pil, font)

    # Step 3: Draw the dots and labels on the image
    final_image = draw_dots_and_labels(
        blank_image_np, dots, labels, radius, dot_color, font)

    # Step 4: Handle debug visualization if required
    if debug:
        display_debug_image_with_lines(
            blank_image_np, linear_paths, labels, radius, font)

    return final_image


def create_blank_image(image_size, font_path, font_size):
    """
    Creates a blank image using PIL and sets up the drawing context with the specified font.
    """
    blank_image_pil = Image.new(
        "RGB", (image_size[1], image_size[0]), (255, 255, 255))
    draw_pil = ImageDraw.Draw(blank_image_pil)
    font = ImageFont.truetype(font_path, font_size)
    blank_image_np = np.array(blank_image_pil)
    return blank_image_np, blank_image_pil, draw_pil, font


def calculate_dots_and_labels(linear_paths, radius, font, draw_pil, font_color):
    """
    Calculate the positions for dots and potential label positions based on the dot positions.
    """
    dots = []
    labels = []
    distance_from_dots = 1.2 * radius

    for path_index, path in enumerate(linear_paths):
        for point_index, point in enumerate(path):
            dot_box = (point[0] - radius, point[1] - radius,
                       point[0] + radius, point[1] + radius)
            dots.append((point, dot_box))
            label = str(point_index + 1)

            # Define possible label positions around the dot
            label_positions = [
                ((point[0] + distance_from_dots, point[1] -
                 distance_from_dots), "ls"),  # top-right
                ((point[0] + distance_from_dots, point[1] + \
                 distance_from_dots), "ls"),  # bottom-right
                ((point[0] - distance_from_dots, point[1] - \
                 distance_from_dots), "rs"),  # top-left
                ((point[0] - distance_from_dots, point[1] + \
                 distance_from_dots), "rs"),  # bottom-left
                ((point[0], point[1] - 2 * distance_from_dots),
                 "ms"),                   # directly above
                ((point[0], point[1] + 3 * distance_from_dots),
                 "ms")                    # directly below
            ]
            labels.append((label, label_positions, font_color))

    return dots, labels


def get_label_box(position, text, anchor, draw_pil, font):
    """Returns the bounding box of the label (x_min, y_min, x_max, y_max) depending on anchor."""
    bbox = draw_pil.textbbox(position, text, font=font, anchor=anchor)
    return bbox


def adjust_label_positions(labels, dots, draw_pil, font):
    """
    Check for overlaps between labels and dots and adjust the positions of the labels.
    """
    def does_overlap(box1, box2):
        """Check if two bounding boxes overlap."""
        return not (box1[2] < box2[0] or box1[0] > box2[2] or box1[3] < box2[1] or box1[1] > box2[3])

    for i, (label, positions, color) in enumerate(labels):
        valid_positions = []
        all_positions_info = []
        for pos, anchor in positions:
            label_box = get_label_box(pos, label, anchor, draw_pil, font)
            overlaps = any(does_overlap(label_box, dot[1]) for dot in dots) or \
                any(does_overlap(label_box, get_label_box(
                    l[1][0][0], l[0], l[1][0][1], draw_pil, font)) for j, l in enumerate(labels) if i != j)

            distance = ((pos[0] - dots[i][0][0])**2 +
                        (pos[1] - dots[i][0][1])**2)**0.5
            all_positions_info.append((pos, distance, overlaps, anchor))

            if not overlaps:
                valid_positions.append((pos, anchor))

        if valid_positions:
            # Choose the closest non-overlapping position
            best_position, best_anchor = min(valid_positions, key=lambda p: next(
                info[1] for info in all_positions_info if info[0] == p[0]))
            labels[i] = (label, [(best_position, best_anchor)], color)
        else:
            print(f"Error: Label {label} overlaps at all positions")
            # Red color for all positions in case of error
            labels[i] = (label, positions, (255, 0, 0))

    return labels


def draw_dots_and_labels(blank_image_np, dots, labels, radius, dot_color, font):
    """
    Draws dots and labels on the main image.
    """
    blank_image_pil = Image.fromarray(blank_image_np)
    draw_pil = ImageDraw.Draw(blank_image_pil)

    # Draw the dots
    for point, _ in dots:
        cv2.circle(blank_image_np, point, radius,
                   dot_color, -1, lineType=cv2.LINE_AA)

    # Draw the labels
    for label, positions, color in labels:
        if color == (255, 0, 0):  # If it's a red label (error case)
            for pos, anchor in positions:
                draw_pil.text(pos, label, font=font, fill=color, anchor=anchor)
        else:
            draw_pil.text(positions[0][0], label, font=font,
                          fill=color, anchor=positions[0][1])

    return np.array(blank_image_pil)


def display_debug_image_with_lines(blank_image_np, linear_paths, labels, radius, font):
    """
    Displays a debug image with lines connecting consecutive points, dots, and labels.
    """
    debug_image_np = blank_image_np.copy()

    # Draw lines between consecutive points on the debug image
    for path in linear_paths:
        for i, point in enumerate(path):
            if i > 0:
                prev_point = path[i - 1]
                cv2.line(debug_image_np, prev_point, point,
                         (0, 0, 0), 1, lineType=cv2.LINE_AA)

    # Add labels to the debug image
    debug_image_pil = Image.fromarray(debug_image_np)
    draw_debug_pil = ImageDraw.Draw(debug_image_pil)

    for label, positions, color in labels:
        for pos, anchor in positions:
            draw_debug_pil.text(pos, label, font=font,
                                fill=color, anchor=anchor)

    # Display the debug image with lines, dots, and labels
    final_debug_image = np.array(debug_image_pil)
    display_with_matplotlib(
        final_debug_image, 'Debug Image with Dots, Lines, and Labels')
