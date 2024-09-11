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
    Checks all possible positions for each label before deciding on placement.
    In debug mode, it tests all positions for each label, prints distance and overlap information,
    draws small dots at each possible label position, and adds labels in red for overlapping positions.
    """
    blank_image_pil = Image.new(
        "RGB", (image_size[1], image_size[0]), (255, 255, 255))
    draw_pil = ImageDraw.Draw(blank_image_pil)
    font = ImageFont.truetype(font_path, font_size)
    blank_image_np = np.array(blank_image_pil)
    dots = []
    labels = []
    debug_dots = []

    def get_label_box(position, text, anchor):
        """Returns the bounding box of the label (x_min, y_min, x_max, y_max) depending on anchor."""
        bbox = draw_pil.textbbox(position, text, font=font, anchor=anchor)
        return bbox  # bbox is already in (x_min, y_min, x_max, y_max) format

    def does_overlap(box1, box2):
        """Check if two bounding boxes overlap."""
        return not (box1[2] < box2[0] or box1[0] > box2[2] or box1[3] < box2[1] or box1[1] > box2[3])

    # Step 1: Calculate potential positions for dots and labels
    for path_index, path in enumerate(linear_paths):
        for point_index, point in enumerate(path):
            dot_box = (point[0] - radius, point[1] - radius,
                       point[0] + radius, point[1] + radius)
            dots.append((point, dot_box))
            label = str(point_index + 1)
            # Adjust label positions to be relative to the dot, with various anchors
            distance_from_dots = 1.2 * radius
            label_positions = [
                # Top-right and bottom-right (left-justified)
                ((point[0] + distance_from_dots, point[1] - \
                 distance_from_dots), "ls"),  # top-right
                ((point[0] + distance_from_dots, point[1] + \
                 distance_from_dots), "ls"),  # bottom-right

                # Top-left and bottom-left (right-justified)
                ((point[0] - distance_from_dots, point[1] - \
                 distance_from_dots), "rs"),  # top-left
                ((point[0] - distance_from_dots, point[1] + \
                 distance_from_dots), "rs"),  # bottom-left

                # Centered above and below the dot (middle-justified)
                # directly above
                ((point[0], point[1] - 2 * distance_from_dots), "ms"),
                # directly below
                ((point[0], point[1] + 3 * distance_from_dots), "ms")
            ]
            labels.append((label, label_positions, font_color))

    # Step 2: Check for overlaps and adjust positions
    for i, (label, positions, color) in enumerate(labels):
        valid_positions = []
        all_positions_info = []
        for pos, anchor in positions:
            label_box = get_label_box(pos, label, anchor)
            overlaps = any(does_overlap(label_box, dot[1]) for dot in dots) or \
                any(does_overlap(label_box, get_label_box(
                    l[1][0][0], l[0], l[1][0][1])) for j, l in enumerate(labels) if i != j)

            distance = ((pos[0] - dots[i][0][0])**2 +
                        (pos[1] - dots[i][0][1])**2)**0.5
            all_positions_info.append((pos, distance, overlaps, anchor))

            if not overlaps:
                valid_positions.append((pos, anchor))

            # if debug:
            #     # print(f"Label {label} at position {pos} with anchor {anchor}: Distance from dot = "
            #     # f"{distance:.2f}, {'Overlaps' if overlaps else 'No overlap'}")
            #     debug_dots.append(pos)

        if valid_positions:
            # Choose the closest non-overlapping position
            best_position, best_anchor = min(valid_positions, key=lambda p: next(
                info[1] for info in all_positions_info if info[0] == p[0]))
            labels[i] = (label, [(best_position, best_anchor)], color)
        else:
            if debug:
                print(f"Error: Label {label} overlaps at all positions")
            # Red color for all positions in case of error
            labels[i] = (label, positions, (255, 0, 0))

    # Step 3: Apply dots and labels to the image
    for point, _ in dots:
        cv2.circle(blank_image_np, point, radius,
                   dot_color, -1, lineType=cv2.LINE_AA)

    if debug:
        for debug_point in debug_dots:
            cv2.circle(blank_image_np, (int(debug_point[0]), int(debug_point[1])),
                       radius // 3, (0, 255, 0), -1, lineType=cv2.LINE_AA)

    blank_image_pil = Image.fromarray(blank_image_np)
    draw_pil = ImageDraw.Draw(blank_image_pil)

    for label, positions, color in labels:
        if color == (255, 0, 0):  # If it's a red label (error case)
            for pos, anchor in positions:
                draw_pil.text(pos, label, font=font, fill=color, anchor=anchor)
        else:
            draw_pil.text(positions[0][0], label,
                          font=font, fill=color, anchor=positions[0][1])

    final_image = np.array(blank_image_pil)

    if debug:
        display_with_matplotlib(
            final_image, 'Image with Dots, Anchored Labels, and Debug Points')

    return final_image
