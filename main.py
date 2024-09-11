import argparse
import cv2
import matplotlib.pyplot as plt
from dot_2_dot import retrieve_contours, contour_to_linear_paths, draw_points_on_image
from utils import find_font_in_windows, save_image, compute_image_diagonal


if __name__ == "__main__":
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description="Process an image and draw points at path vertices on a blank background."
    )
    parser.add_argument('-i', '--input', type=str, default='input.png',
                        help='Input image path (default: input.png)')
    parser.add_argument('-f', '--font', type=str, default='Arial.ttf',
                        help='Font file name (searched automatically in C:\\Windows\\Fonts)')
    parser.add_argument('-fs', '--fontSize', type=int, default=48,
                        help='Font size for labeling (default: 24)')
    parser.add_argument('-fc', '--fontColor', nargs=3, type=int, default=[0, 0, 0],
                        help='Font color for labeling as 3 values (default: black [0, 0, 0])')
    parser.add_argument('-dc', '--dotColor', nargs=3, type=int, default=[0, 0, 0],
                        help='Dot color as 3 values (default: black [0, 0, 0])')
    parser.add_argument('-r', '--radius', type=int, default=20,
                        help='Radius of the points (default: 10)')
    parser.add_argument('-d', '--dpi', type=int, default=400,
                        help='DPI of the output image (default: 400)')
    parser.add_argument('-e', '--epsilon', type=float, default=0.001,
                        help='Epsilon for contour approximation (default: 0.001)')
    parser.add_argument('-dma', '--distanceMax', type=float, default=0.05,
                        help='Minimum distance between points as a percentage of the diagonal (default: 5%)')
    parser.add_argument('-de', '--debug', action='store_true', default=True,
                        help='Enable debug mode to display intermediate steps.')
    parser.add_argument('-o', '--output', type=str, default='output.png',
                        help='Output image path (default: output.png)')

    args = parser.parse_args()

    # Load the original image for debugging purposes
    original_image = cv2.imread(args.input)

    # Compute the diagonal of the image
    diagonal_length = compute_image_diagonal(original_image)

    # Convert distanceMin from percentage to pixel value
    distance_max_px = args.distanceMax * diagonal_length

    # Load the contours and paths with debug mode
    contours = retrieve_contours(args.input, debug=args.debug)
    linear_paths = contour_to_linear_paths(
        contours, epsilon_factor=args.epsilon, max_distance=distance_max_px, image=original_image, debug=args.debug
    )

    # Get the dimensions of the original image
    image_height, image_width = original_image.shape[:2]

    font_path = find_font_in_windows(args.font)
    # Draw the points on two blank images (one with lines, one without)
    output_image_with_dots = draw_points_on_image(
        (image_height, image_width), linear_paths, args.radius, tuple(
            args.dotColor), font_path, args.fontSize, tuple(args.fontColor), debug=args.debug
    )

    # Save the output images with the specified DPI
    # Save image with only dots and labels
    save_image(output_image_with_dots, f"{args.output}", args.dpi)

    print(f"Output images saved as {args.output}")

    # If debug is enabled, close all OpenCV windows after displaying the intermediate images
    if args.debug:
        plt.show()
