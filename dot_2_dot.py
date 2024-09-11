import cv2
import numpy as np
from utils import resize_for_debug, point_distance, insert_midpoints, display_with_matplotlib


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


def contour_to_linear_paths(contours, epsilon_factor=0.001, max_distance=10, image=None, debug=False):
    """
    Converts each contour into a sequence of dominant points and inserts midpoints if needed.
    """
    dominant_points_list = []

    for contour in contours:
        epsilon = epsilon_factor * cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, epsilon, True)
        area = cv2.contourArea(approx)

        if area > 0:
            approx = approx[::-1]

        dominant_points = [(point[0][0], point[0][1]) for point in approx]
        refined_points = insert_midpoints(dominant_points, max_distance)
        dominant_points_list.append(refined_points)

        if debug and image is not None:
            for point in refined_points:
                cv2.circle(image, point, 5, (0, 0, 255), -1)

    if debug and image is not None:
        debug_image = resize_for_debug(image)
        display_with_matplotlib(
            debug_image, 'Dominant Points with Min Distance on Image')

    return dominant_points_list


def draw_points_on_image(image_size, linear_paths, radius, dot_color, font_path, font_size, font_color, debug=False):
    """
    Draws points at the vertices of each linear path and labels each point with a number on a blank image.
    """
    from PIL import ImageFont, ImageDraw, Image
    blank_image_pil = Image.new(
        "RGB", (image_size[1], image_size[0]), (255, 255, 255))
    draw_pil = ImageDraw.Draw(blank_image_pil)

    font = ImageFont.truetype(font_path, font_size)
    blank_image_np = np.array(blank_image_pil)

    for path in linear_paths:
        for i, point in enumerate(path):
            cv2.circle(blank_image_np, point, radius,
                       dot_color, -1, lineType=cv2.LINE_AA)

            blank_image_pil = Image.fromarray(blank_image_np)
            draw_pil = ImageDraw.Draw(blank_image_pil)
            label = str(i + 1)
            label_position = (point[0] + 2 * radius, point[1] - 2 * radius)
            draw_pil.text(label_position, label, font=font, fill=font_color)
            blank_image_np = np.array(blank_image_pil)

    if debug:
        display_with_matplotlib(blank_image_np, 'Image with Dots and Labels')

    return blank_image_np
