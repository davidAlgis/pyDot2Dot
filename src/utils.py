import cv2
import os
import numpy as np
from PIL import Image, ImageTk


def rgba_to_hex(rgba_str):
    """
    Converts an RGBA string (e.g., "255,0,0,255") to a hexadecimal color code (e.g., "#FF0000").
    Ignores the alpha channel.

    Parameters:
    - rgba_str: String representing RGBA values separated by commas.

    Returns:
    - Hexadecimal color code string.
    """
    try:
        parts = rgba_str.split(',')
        if len(parts) != 4:
            raise ValueError("RGBA must have exactly four components.")
        r, g, b, a = [int(part.strip()) for part in parts]
        return f'#{r:02X}{g:02X}{b:02X}'
    except Exception as e:
        return "#000000"  # Default to black if conversion fails


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

    # Determine the appropriate resampling filter
    try:
        resample_filter = Image.Resampling.LANCZOS
    except AttributeError:
        # For Pillow versions < 10.0.0
        resample_filter = Image.ANTIALIAS

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


def parse_size(value, diagonal_length):
    """
    Parses the given value as a pixel size or percentage of the diagonal.
    If the value ends with '%', it treats it as a percentage.
    Otherwise, it treats it as an absolute pixel value.
    """
    if isinstance(value, str) and value.endswith('%'):
        return float(value[:-1]) / 100 * diagonal_length
    else:
        return float(value)  # Treat as absolute pixel value


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
        raise argparse.ArgumentTypeError('Boolean value expected.')


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


def display_with_matplotlib(image, title="Image"):
    import matplotlib.pyplot as plt
    rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    plt.figure(figsize=(10, 8))
    plt.imshow(rgb_image)
    plt.title(title)
    plt.axis('on')


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


def save_image(image, output_path, dpi):
    """
    Save the image using matplotlib's savefig with support for transparent background.
    """
    from matplotlib import pyplot as plt
    height, width = image.shape[:2]
    fig = plt.figure(frameon=False)
    fig.set_size_inches(width / dpi, height / dpi)
    ax = plt.Axes(fig, [0., 0., 1., 1.])
    ax.set_axis_off()
    fig.add_axes(ax)
    ax.imshow(cv2.cvtColor(image, cv2.COLOR_BGRA2RGBA))  # Convert to RGBA
    plt.savefig(output_path, dpi=dpi, transparent=True)  # Enable transparency
    plt.close(fig)


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
