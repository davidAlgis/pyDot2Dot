import cv2
import numpy as np
import argparse


def retrieve_contours(image_path):
    """
    Retrieves the contours found in the image.

    Parameters:
        image_path (str): The path to the image file.

    Returns:
        List[np.ndarray]: A list of contours found in the image.
    """
    # Load the image
    image = cv2.imread(image_path)

    # Check if the image was loaded successfully
    if image is None:
        raise FileNotFoundError(
            f"Image file '{image_path}' could not be found or the path is incorrect.")

    # Convert the image to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Apply a binary threshold to the image
    _, binary = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)

    # Find contours in the binary image
    contours, _ = cv2.findContours(
        binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Check if any contours were found
    if not contours:
        raise ValueError("No contours were found in the image.")

    return contours


def contour_to_linear_paths(contours, epsilon_factor=0.01):
    """
    Converts each contour into a sequence of linear paths by approximating the contour with fewer points.

    Parameters:
        contours (List[np.ndarray]): A list of contours.
        epsilon_factor (float): The approximation accuracy as a percentage of the contour's perimeter.

    Returns:
        List[List[Tuple[int, int]]]: A list of linear paths, each represented as a list of (x, y) points.
    """
    linear_paths = []

    for contour in contours:
        # Approximate the contour with a polygon
        epsilon = epsilon_factor * cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, epsilon, True)

        # Convert the approximated contour to a list of (x, y) points
        path = [(point[0][0], point[0][1]) for point in approx]
        linear_paths.append(path)

    return linear_paths


def draw_points_on_blank_image(image_size, linear_paths, radius, font, font_scale, font_color):
    """
    Draws points at the vertices of each linear path and labels each point with a number on a blank image.

    Parameters:
        image_size (Tuple[int, int]): The size of the output image (height, width).
        linear_paths (List[List[Tuple[int, int]]]): A list of paths, where each path is a list of (x, y) points.
        radius (int): The radius of the points to be drawn.
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
            # Draw a smooth circle at each vertex
            cv2.circle(blank_image, point, radius, (0, 0, 255), -1,
                       lineType=cv2.LINE_AA)  # Red circle with anti-aliasing

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
                        default=0.5, help='Font scale for labeling (default: 0.5)')
    parser.add_argument('-fc', '--fontColor', nargs=3, type=int, default=[
                        0, 0, 0], help='Font color for labeling as 3 values (default: black [0, 0, 0])')
    parser.add_argument('-r', '--radius', type=int, default=5,
                        help='Radius of the points (default: 5)')
    parser.add_argument('-d', '--dpi', type=int, default=400,
                        help='DPI of the output image (default: 400)')
    parser.add_argument('-o', '--output', type=str, default='output.png',
                        help='Output image path (default: output.png)')

    args = parser.parse_args()

    # Load the contours and paths
    contours = retrieve_contours(args.input)
    linear_paths = contour_to_linear_paths(contours)

    # Load the original image to get dimensions
    original_image = cv2.imread(args.input)
    image_height, image_width = original_image.shape[:2]

    # Draw the points on a blank image (white background) and label the vertices
    output_image_with_points = draw_points_on_blank_image(
        (image_height, image_width), linear_paths, args.radius, args.font, args.fontScale, tuple(args.fontColor))

    # Save the output image with the specified DPI
    save_image(output_image_with_points, args.output, args.dpi)

    print(f"Output image saved to {args.output}")
