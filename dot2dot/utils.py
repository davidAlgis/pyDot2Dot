"""
Some utilities function
"""
import os
import sys
from typing import List, Tuple
import numpy as np
from PIL import Image, ImageTk
import cv2


def str_color_to_tuple(color_str):
    split_str = color_str.split(',')
    if split_str == ['']:
        return tuple()
    color_list = []
    for s in split_str:
        s_int = str_to_int_safe(s)
        if s_int is None:
            return tuple()
        color_list.append(s_int)
    return tuple(color_list)


def str_to_int_safe(str_to_convert):
    if str_to_convert != '':
        return int(str_to_convert)
    else:
        return None


def get_base_directory():
    """
    Determines the base directory for the application, depending on whether it's run
    as a standalone executable via PyInstaller or cx_Freeze, or as a normal Python script.

    - PyInstaller sets sys._MEIPASS when frozen.
    - cx_Freeze sets sys.frozen = True but does not provide sys._MEIPASS.
      Instead, the executable directory (os.path.dirname(sys.executable)) can be used.

    If not frozen at all, we return the parent directory of the current file.
    """
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        # Running normally as a script
        current_directory = os.path.abspath(os.path.dirname(__file__))
        return os.path.abspath(os.path.join(current_directory, os.pardir))


def distance_to_segment(px, py, x1, y1, x2, y2):
    """
    Calculates the shortest distance from a point (px, py) to a line segment (x1, y1)-(x2, y2) using NumPy.

    Returns:
    - Distance as a float.
    """
    # Convert the points to NumPy arrays for vectorized operations
    point = np.array([px, py])
    p1 = np.array([x1, y1])
    p2 = np.array([x2, y2])

    # Compute the vector from p1 to p2
    line_vec = p2 - p1
    line_len = np.linalg.norm(line_vec)

    if line_len < 1e-8:
        # The segment is a point
        return np.linalg.norm(point - p1)

    # Normalize the line vector
    line_unit_vec = line_vec / line_len

    # Compute the vector from p1 to the point
    point_vec = point - p1

    # Project the point vector onto the line (dot product)
    projection = np.dot(point_vec, line_unit_vec)

    if projection < 0:
        # The projection falls before the first point, return distance to p1
        return np.linalg.norm(point - p1)
    elif projection > line_len:
        # The projection falls beyond the second point, return distance to p2
        return np.linalg.norm(point - p2)
    else:
        # The projection falls within the segment
        projection_point = p1 + projection * line_unit_vec
        return np.linalg.norm(point - projection_point)


def rgba_to_hex(rgba):
    """
    Converts an RGBA string or tuple to a hexadecimal color code.
    Ignores the alpha channel.

    Parameters:
    - rgba: String representing RGBA values separated by commas or a tuple of (R, G, B, A).

    Returns:
    - Hexadecimal color code string.
    """
    try:
        if isinstance(rgba, str):
            parts = rgba.split(',')
            if len(parts) != 4:
                raise ValueError(
                    "RGBA string must have exactly four components.")
            r, g, b, _ = [int(part.strip()) for part in parts]
        elif isinstance(rgba, tuple) and len(rgba) == 4:
            r, g, b, _ = rgba
        else:
            raise ValueError(
                "RGBA must be a string or a tuple of four components.")

        return f'#{r:02X}{g:02X}{b:02X}'
    except Exception as _:
        return "#000000"  # Default to black if conversion fails


def parse_rgba(rgba_str):
    """
    Parses an RGBA string into a list of integers.

    Args:
        rgba_str (str): A string like "248,208,73,255".

    Returns:
        list: A list of integers [248, 208, 73, 255].
    """
    try:
        return list(map(int, rgba_str.split(',')))
    except ValueError:
        return [0, 0, 0, 255]  # Default to black if parsing fails


def load_image(image_path):
    """
    Loads an image from the given path and returns a PIL Image object.
    """
    try:
        pil_image = Image.open(image_path).convert("RGBA")
        return pil_image
    except Exception as e:
        print(f"Error loading image {image_path}: {e}")
        return None


def resize_image(pil_image, target_size):
    """
    Resizes the given PIL Image to fit within the target_size while preserving aspect ratio.
    If the image is smaller than the target_size, it is scaled up; if larger, scaled down.

    Parameters:
    - pil_image: PIL Image object to resize.
    - target_size: Tuple (width, height) representing the maximum size.

    Returns:
    - Resized PIL Image object.
    """
    if pil_image is None:
        return None

    original_width, original_height = pil_image.size
    target_width, target_height = target_size

    # Calculate scaling factor while preserving aspect ratio
    scale_factor = min(target_width / original_width,
                       target_height / original_height)

    # Calculate new size
    new_width = int(original_width * scale_factor)
    new_height = int(original_height * scale_factor)

    resample_filter = Image.Resampling.LANCZOS

    # Resize the image with high-quality resampling
    resized_image = pil_image.resize((new_width, new_height),
                                     resample=resample_filter)
    return resized_image


def load_image_to_tk(pil_image, target_size):
    """
    Resizes the PIL Image to fit within target_size and converts it to a PhotoImage for Tkinter.

    Parameters:
    - pil_image: PIL Image object to convert.
    - target_size: Tuple (width, height) representing the maximum size.

    Returns:
    - ImageTk.PhotoImage object suitable for Tkinter display.
    """
    if pil_image is None:
        return None

    resized_image = resize_image(pil_image, target_size)
    return ImageTk.PhotoImage(resized_image)


def str2bool(v):
    """
    Converts a string argument to a boolean value.
    """
    if isinstance(v, bool):
        return v
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise ArgumentTypeError('Boolean value expected.')


def find_font_in_windows(font_name='Arial.ttf'):
    fonts_dir = r'C:\\Windows\\Fonts'
    font_path = os.path.join(fonts_dir, font_name)

    default_font = 'Arial.ttf'
    default_font_path = os.path.join(fonts_dir, default_font)

    if os.path.isfile(font_path):
        return font_path
    else:

        print("Use a font in this list:")
        for item in os.listdir(fonts_dir):
            print(f"- {item}")
        print(
            f"Font '{font_name}' not found in {fonts_dir}. Use a font from the list above. Using default font: {default_font}."
        )
        if os.path.isfile(default_font_path):
            return default_font_path
        print(f"Error - Could not find default font too {default_font}...")
        return None


def display_with_opencv(image, title="Image"):
    # Convert the image to RGB if it's in BGR (OpenCV uses BGR by default)
    rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    # Display the image in a window with the specified title
    cv2.imshow(title, rgb_image)

    # Wait indefinitely until a key is pressed, then close the window
    cv2.waitKey(0)
    cv2.destroyAllWindows()


def resize_for_debug(image, max_width=1000, max_height=700):
    height, width = image.shape[:2]
    width_scaling_factor = max_width / \
        float(width) if width > max_width else 1.0
    height_scaling_factor = max_height / \
        float(height) if height > max_height else 1.0
    scaling_factor = min(width_scaling_factor, height_scaling_factor)

    if scaling_factor < 1.0:
        new_width = int(width * scaling_factor)
        new_height = int(height * scaling_factor)
        resized_image = cv2.resize(image, (new_width, new_height),
                                   interpolation=cv2.INTER_AREA)
        return resized_image
    else:
        return image


def generate_output_path(input_path, output_path=None):
    """
    Generate output file path based on input image name if output path is not provided.
    Appends '_dotted' before the file extension in the input file name.
    """
    if output_path:
        return output_path
    base_name = os.path.basename(input_path)
    name, ext = os.path.splitext(base_name)
    return os.path.join(os.path.dirname(input_path), f"{name}_dotted{ext}")


def save_image(image, output_path, dpi=None):
    """
    Save the image using OpenCV.
    
    Args:
        image (numpy.ndarray): The image to save.
        output_path (str): Path to save the image.
        dpi (int or None): DPI value (not applicable in OpenCV; included for compatibility).
    """
    # Save the image using OpenCV
    cv2.imwrite(output_path, image)


def image_to_pil_rgb(image):
    return Image.fromarray(image)


def compute_image_diagonal(image):
    height, width = image.shape[:2]
    return (width**2 + height**2)**0.5


def remove_iccp_profile(image_path):
    img = Image.open(image_path)
    if "icc_profile" in img.info:
        img.info.pop("icc_profile", None)
    corrected_image_path = 'corrected_image.png'
    img.save(corrected_image_path)
    return corrected_image_path


def point_distance(p1, p2):
    return ((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)**0.5


def calculate_area(p1, p2, p3):
    """
    Calculate the area of the triangle formed by three points.
    """
    return 0.5 * abs((p2[0] - p1[0]) * (p3[1] - p1[1]) - (p3[0] - p1[0]) *
                     (p2[1] - p1[1]))


def filter_close_points(points: List[Tuple[int, int]],
                        min_distance: float) -> List[Tuple[int, int]]:
    """
    Removes points that are closer than min_distance.
    Always keeps the first, last

    Args:
        points (List[Tuple[int, int]]): List of (x, y) points.
        min_distance (float): Minimum allowable distance between points.

    Returns:
        List[Tuple[int, int]]: Filtered list of points.
    """
    if len(points) < 2:
        return points  # Not enough points to filter

    filtered_points = [points[0]]  # Keep the first point
    last_kept_point = points[0]

    for i in range(1, len(points) - 1):
        current_point = points[i]
        dist = point_distance(last_kept_point, current_point)
        if dist >= min_distance:
            filtered_points.append(current_point)
            last_kept_point = current_point

    filtered_points.append(points[-1])  # Keep the last point
    return filtered_points


def insert_midpoints(points: List[Tuple[int, int]],
                     max_distance: float) -> List[Tuple[int, int]]:
    """
    Inserts midpoints between consecutive points if the distance between them exceeds max_distance.
    Ensures that points remain in sequential order after midpoint insertion.

    Args:
        points (List[Tuple[int, int]]): List of (x, y) points.
        max_distance (float): Maximum allowable distance between consecutive points.

    Returns:
        List[Tuple[int, int]]: Refined list of points with inserted midpoints, all as integer coordinates.
    """
    points_array = np.array(points)
    deltas = np.diff(points_array, axis=0)
    distances = np.hypot(deltas[:, 0], deltas[:, 1])
    num_midpoints = (distances // max_distance).astype(int)

    refined_points = [points[0]]
    for i in range(len(points_array) - 1):
        n_mid = num_midpoints[i]
        if n_mid > 0:
            t_values = np.linspace(0, 1, n_mid + 2)[1:-1]
            midpoints = (1 - t_values[:, np.newaxis]) * points_array[
                i] + t_values[:, np.newaxis] * points_array[i + 1]
            # Convert midpoints to integer coordinates
            refined_points.extend(
                [tuple(map(np.int32, midpoint)) for midpoint in midpoints])
        refined_points.append(tuple(map(np.int32, points[i + 1])))

    return refined_points
