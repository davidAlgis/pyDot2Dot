import cv2
import os
from PIL import Image


def find_font_in_windows(font_name='Arial.ttf'):
    fonts_dir = r'C:\\Windows\\Fonts'
    font_path = os.path.join(fonts_dir, font_name)

    default_font = 'Arial.ttf'
    default_font_path = os.path.join(fonts_dir, default_font)

    if os.path.isfile(font_path):
        return font_path
    else:

        print("Use a font in this list :", )
        for item in os.listdir(fonts_dir):
            print(f"- {item}")
        print(
            f"Font '{font_name}' not found in {fonts_dir}. Use a font of the list above. Using default font :{default_font}.")
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
        resized_image = cv2.resize(
            image, (new_width, new_height), interpolation=cv2.INTER_AREA)
        return resized_image
    else:
        return image


def save_image(image, output_path, dpi):
    """
    Save the image using matplotlib's `savefig` with support for transparent background.
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
    return (width**2 + height**2) ** 0.5


def remove_iccp_profile(image_path):
    img = Image.open(image_path)
    if "icc_profile" in img.info:
        img.info.pop("icc_profile", None)
    corrected_image_path = 'corrected_image.png'
    img.save(corrected_image_path)
    return corrected_image_path


def handle_alpha_channel(image, debug=False):
    if image.shape[2] == 4:
        bgr_image = image[:, :, :3]
        alpha_channel = image[:, :, 3]
        green_background = (0, 255, 0)
        mask = alpha_channel < 255
        bgr_image[mask] = green_background
        return bgr_image
    return image


def point_distance(p1, p2):
    return ((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2) ** 0.5


def insert_midpoints(points, max_distance):
    """
    Inserts midpoints between consecutive points if the distance between them exceeds max_distance.
    Ensures that points remain in sequential order after midpoint insertion.
    """
    refined_points = []

    for i in range(len(points) - 1):
        p1, p2 = points[i], points[i + 1]
        refined_points.append(p1)  # Always keep the original point

        # Compute the number of midpoints needed
        distance = point_distance(p1, p2)
        if distance > max_distance:
            num_midpoints = int(distance // max_distance)
            for j in range(1, num_midpoints + 1):
                # Insert evenly spaced midpoints between p1 and p2
                t = j / (num_midpoints + 1)
                midpoint = (int(p1[0] * (1 - t) + p2[0] * t),
                            int(p1[1] * (1 - t) + p2[1] * t))
                refined_points.append(midpoint)

    refined_points.append(points[-1])  # Add the last point
    return refined_points


def filter_close_points(points, min_distance):
    """
    Removes points that are closer than min_distance.
    Keeps the first and last point always.
    """
    if len(points) < 2:
        return points  # Not enough points to filter

    filtered_points = [points[0]]  # Keep the first point

    for i in range(1, len(points)-1):
        prev_point = filtered_points[-1]
        current_point = points[i]

        # Only keep points that are at least min_distance away
        if point_distance(prev_point, current_point) >= min_distance:
            filtered_points.append(current_point)

    filtered_points.append(points[-1])  # Keep the last point
    return filtered_points
