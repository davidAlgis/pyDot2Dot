from PIL import Image
import cv2
import numpy as np
import argparse


def remove_iccp_profile(image_path):
    """
    Opens the image using Pillow, removes any incorrect color profiles, and saves a temporary version
    for further use by OpenCV.

    Parameters:
        image_path (str): The path to the image file.

    Returns:
        str: The path to the corrected image.
    """
    img = Image.open(image_path)

    # Remove the ICC profile if present (which causes the iCCP warning)
    if "icc_profile" in img.info:
        img.info.pop("icc_profile", None)

    # Save the image to a temporary file (or you can overwrite the original image)
    corrected_image_path = 'corrected_image.png'
    img.save(corrected_image_path)

    return corrected_image_path


def resize_for_debug(image, max_width=1000, max_height=700):
    """
    Resizes the image if its width exceeds the maximum width or height exceeds the maximum height, maintaining aspect ratio.

    Parameters:
        image (np.ndarray): The input image.
        max_width (int): The maximum width of the image for debug display.
        max_height (int): The maximum height of the image for debug display.

    Returns:
        np.ndarray: The resized image if necessary, otherwise the original image.
    """
    height, width = image.shape[:2]

    # Determine the scaling factor by checking both width and height
    width_scaling_factor = max_width / \
        float(width) if width > max_width else 1.0
    height_scaling_factor = max_height / \
        float(height) if height > max_height else 1.0

    # Choose the most restrictive scaling factor (the one that makes the image fit both dimensions)
    scaling_factor = min(width_scaling_factor, height_scaling_factor)

    # Only resize if the scaling factor is less than 1 (image is larger than max dimensions)
    if scaling_factor < 1.0:
        new_width = int(width * scaling_factor)
        new_height = int(height * scaling_factor)
        resized_image = cv2.resize(
            image, (new_width, new_height), interpolation=cv2.INTER_AREA)
        return resized_image
    else:
        return image


def handle_alpha_channel(image, debug=False):
    """
    If the image has an alpha channel, replaces transparent areas with green and removes the alpha channel.

    Parameters:
        image (np.ndarray): The input image.
        debug (bool): If True, displays the image with replaced alpha areas.

    Returns:
        np.ndarray: The image without the alpha channel, with transparency replaced by green.
    """
    if image.shape[2] == 4:  # Check if the image has an alpha channel
        bgr_image = image[:, :, :3]  # Extract BGR channels
        alpha_channel = image[:, :, 3]  # Extract the alpha channel

        # Create a green background (full green)
        green_background = np.ones_like(
            bgr_image, dtype=np.uint8) * [0, 255, 0]  # Full green

        # Create a mask where the alpha channel is less than 255 (transparent areas)
        mask = alpha_channel < 255

        # Replace transparent areas in the BGR image with green
        bgr_image[mask] = green_background[mask]

        if debug:
            debug_image = resize_for_debug(bgr_image)
            cv2.imshow('Image with Alpha Replaced by Green', debug_image)
            cv2.waitKey(0)

        return bgr_image
    else:
        return image


def retrieve_contours(image_path, debug=False):
    """
    Retrieves the contours found in the image and displays intermediate steps if debug is enabled.

    Parameters:
        image_path (str): The path to the image file.
        debug (bool): If True, displays the intermediate steps.

    Returns:
        List[np.ndarray]: A list of contours found in the image.
    """
    # Remove iCCP profile using Pillow
    corrected_image_path = remove_iccp_profile(image_path)

    # Load the image with OpenCV
    # Load image with alpha channel if it exists
    image = cv2.imread(corrected_image_path, cv2.IMREAD_UNCHANGED)

    if image is None:
        raise FileNotFoundError(
            f"Image file '{image_path}' could not be found or the path is incorrect.")

    # Handle alpha channel by replacing transparency with green
    image = handle_alpha_channel(image, debug=debug)

    # Display the original image in debug mode
    if debug:
        debug_image = resize_for_debug(image)
        cv2.imshow('Original Image', debug_image)
        cv2.waitKey(0)

    # Convert the image to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Display the grayscale image in debug mode
    if debug:
        debug_image = resize_for_debug(gray)
        cv2.imshow('Grayscale Image', debug_image)
        cv2.waitKey(0)

    # Apply a binary threshold to the image
    _, binary = cv2.threshold(gray, 100, 255, cv2.THRESH_BINARY_INV)

    # Display the binary image in debug mode
    if debug:
        debug_image = resize_for_debug(binary)
        cv2.imshow('Binary Image', debug_image)
        cv2.waitKey(0)

    # Find contours in the binary image
    contours, _ = cv2.findContours(
        binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Check if any contours were found
    if not contours:
        raise ValueError("No contours were found in the image.")

    # Draw contours on the original image in debug mode
    if debug:
        debug_image = image.copy()
        cv2.drawContours(debug_image, contours, -1, (0, 255, 0), 2)
        debug_image = resize_for_debug(debug_image)
        cv2.imshow('Contours on Image', debug_image)
        cv2.waitKey(0)

    return contours


def contour_to_linear_paths(contours, epsilon_factor=0.01, image=None, debug=False):
    """
    Converts each contour into a sequence of linear paths by approximating the contour with fewer points
    and ensures the points are ordered clockwise. If debug is enabled, draws the paths in red.

    Parameters:
        contours (List[np.ndarray]): A list of contours.
        epsilon_factor (float): The approximation accuracy as a percentage of the contour's perimeter.
        image (np.ndarray): The image on which to draw the paths (only in debug mode).
        debug (bool): If True, draws the paths on the image in red.

    Returns:
        List[List[Tuple[int, int]]]: A list of linear paths, each represented as a list of (x, y) points.
    """
    linear_paths = []

    for contour in contours:
        # Approximate the contour with a polygon
        epsilon = epsilon_factor * cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, epsilon, True)

        # Check if the contour is anti-clockwise (positive area)
        area = cv2.contourArea(approx)
        if area > 0:
            # If anti-clockwise, reverse the points to make it clockwise
            approx = approx[::-1]

        # Convert the approximated contour to a list of (x, y) points
        path = [(point[0][0], point[0][1]) for point in approx]
        linear_paths.append(path)

        # If debug mode is enabled, draw the path on the image in red
        if debug and image is not None:
            for i in range(len(path)):
                start_point = path[i]
                # Connect to the next point, or loop back to the first
                end_point = path[(i + 1) % len(path)]
                # Red color for debug path
                cv2.line(image, start_point, end_point, (0, 0, 255), 2)

    # If debug mode is enabled, display the paths drawn on the image
    if debug and image is not None:
        debug_image = resize_for_debug(image)
        cv2.imshow('Paths Drawn on Image', debug_image)
        cv2.waitKey(0)

    return linear_paths


def draw_points_on_blank_image(image_size, linear_paths, radius, dot_color, font, font_scale, font_color):
    """
    Draws points at the vertices of each linear path and labels each point with a number on a blank image.

    Parameters:
        image_size (Tuple[int, int]): The size of the output image (height, width).
        linear_paths (List[List[Tuple[int, int]]]): A list of paths, where each path is a list of (x, y) points.
        radius (int): The radius of the points to be drawn.
        dot_color (Tuple[int, int, int]): The color of the dots in BGR format.
        font (int): The font type for labeling the points.
        font_scale (float): The scale of the font for labeling the points.
        font_color (Tuple[int, int, int]): The color of the font for labeling the points.

    Returns:
        np.ndarray: The blank image with points drawn and vertices labeled.
    """
    # Create a blank white image
    blank_image = np.ones(
        (image_size[0], image_size[1], 3), np.uint8) * 255  # White background

    # Draw each point on the blank image
    for path_idx, path in enumerate(linear_paths):
        for i, point in enumerate(path):
            # Draw a smooth circle at each vertex with the user-defined dot color
            cv2.circle(blank_image, point, radius, dot_color, -1,
                       lineType=cv2.LINE_AA)  # Dot with anti-aliasing

            # Label each point with a number
            label = str(i + 1)
            # Offset to avoid overlapping the point
            label_position = (point[0] + 5, point[1] - 5)
            cv2.putText(blank_image, label, label_position, font,
                        font_scale, font_color, 1, cv2.LINE_AA)

    return blank_image


def save_image(image, output_path, dpi):
    """
    Saves the image with the specified DPI.

    Parameters:
        image (np.ndarray): The image to save.
        output_path (str): The path to save the output image.
        dpi (int): The DPI (dots per inch) for the saved image.
    """
    # Convert the DPI into pixel size (for matplotlib saving)
    from matplotlib import pyplot as plt
    height, width = image.shape[:2]
    fig = plt.figure(frameon=False)
    fig.set_size_inches(width / dpi, height / dpi)
    ax = plt.Axes(fig, [0., 0., 1., 1.])
    ax.set_axis_off()
    fig.add_axes(ax)
    ax.imshow(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    plt.savefig(output_path, dpi=dpi)
    plt.close(fig)


if __name__ == "__main__":
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description="Process an image and draw points at path vertices on a blank background.")
    parser.add_argument('-i', '--input', type=str, default='input.png',
                        help='Input image path (default: input.png)')
    parser.add_argument('-f', '--font', type=int, default=cv2.FONT_HERSHEY_SIMPLEX,
                        help='Font type for labeling (default: cv2.FONT_HERSHEY_SIMPLEX)')
    parser.add_argument('-fs', '--fontScale', type=float,
                        default=5, help='Font scale for labeling (default: 0.5)')
    parser.add_argument('-fc', '--fontColor', nargs=3, type=int, default=[
                        0, 0, 0], help='Font color for labeling as 3 values (default: black [0, 0, 0])')
    parser.add_argument('-dc', '--dotColor', nargs=3, type=int,
                        default=[0, 0, 0], help='Dot color as 3 values (default: black [0, 0, 0])')
    parser.add_argument('-r', '--radius', type=int, default=25,
                        help='Radius of the points (default: 5)')
    parser.add_argument('-d', '--dpi', type=int, default=400,
                        help='DPI of the output image (default: 400)')
    parser.add_argument('-de', '--debug', action='store_true', default=True,
                        help='Enable debug mode to display intermediate steps.')
    parser.add_argument('-o', '--output', type=str, default='output.png',
                        help='Output image path (default: output.png)')

    args = parser.parse_args()

    # Load the original image for debugging purposes
    original_image = cv2.imread(args.input)

    # Load the contours and paths with debug mode
    contours = retrieve_contours(args.input, debug=args.debug)
    linear_paths = contour_to_linear_paths(
        contours, image=original_image, debug=args.debug)

    # Get the dimensions of the original image
    image_height, image_width = original_image.shape[:2]

    # Draw the points on a blank image (white background) and label the vertices
    output_image_with_points = draw_points_on_blank_image((image_height, image_width), linear_paths, args.radius, tuple(
        args.dotColor), args.font, args.fontScale, tuple(args.fontColor))

    # Save the output image with the specified DPI
    save_image(output_image_with_points, args.output, args.dpi)

    print(f"Output image saved to {args.output}")

    # If debug is enabled, close all OpenCV windows after displaying the intermediate images
    if args.debug:
        cv2.destroyAllWindows()
