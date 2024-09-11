import argparse
import cv2
import os
import matplotlib.pyplot as plt
from dot_2_dot import retrieve_contours, contour_to_linear_paths, draw_points_on_image
from utils import find_font_in_windows, save_image, compute_image_diagonal, resize_for_debug, display_with_matplotlib, remove_iccp_profile


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
                        help='Font size for labeling (default: 48)')
    parser.add_argument('-fc', '--fontColor', nargs=3, type=int, default=[0, 0, 0],
                        help='Font color for labeling as 3 values in rgb format (default: black [0, 0, 0])')
    parser.add_argument('-dc', '--dotColor', nargs=3, type=int, default=[0, 0, 0],
                        help='Dot color as 3 values in rgb format (default: black [0, 0, 0])')
    parser.add_argument('-r', '--radius', type=int, default=20,
                        help='Radius of the points (default: 10)')
    parser.add_argument('-d', '--dpi', type=int, default=400,
                        help='DPI of the output image (default: 400)')
    parser.add_argument('-e', '--epsilon', type=float, default=0.001,
                        help='Epsilon for contour approximation (default: 0.001)')
    parser.add_argument('-dma', '--distanceMax', type=float, default=0.05,
                        help='Maximum distance between points as a percentage of the diagonal'
                        'If > 0, will make sure that all dots are at a distance lesser than this argument.')
    parser.add_argument('-dmi', '--distanceMin', type=float, default=0.01,
                        help='Minimum distance between points as a percentage of the diagonal.'
                        'If > 0, will make sure that all dots are at a distance greater than this argument.')
    parser.add_argument('-de', '--debug', action='store_true', default=False,
                        help='Enable debug mode to display intermediate steps.')
    parser.add_argument('-o', '--output', type=str, default='output.png',
                        help='Output image path (default: output.png)')
    parser.add_argument('-do', '--displayOutput', action='store_true', default=False,
                        help='If set to True, display the output image after processing.')
    parser.add_argument('-v', '--verbose', action='store_true', default=False,
                        help='If set to True, display progress prints to show the script\'s progress.')

    args = parser.parse_args()
    print("Processing picture to dots to dots...")

    if ((args.distanceMin != 0 and args.distanceMax != 0) and args.distanceMin >= args.distanceMax):
        print(f"Error - Distance min {args.distanceMin} cannot be"
              f" greater than distance max {args.distanceMax}."
              " Change arguments --distanceMin and --distanceMax")
        exit(-1)

    if os.path.isfile(args.input):
        # Remove the ICC profile to prevent the warning and get a corrected image path
        corrected_image_path = remove_iccp_profile(args.input)
    else:
        print(
            f"Error - Input image {args.input} does not exists, give its path with --input arguments")

    if args.verbose:
        print("Loading the corrected image...")

    # Load the corrected image for processing
    original_image = cv2.imread(corrected_image_path)

    # Compute the diagonal of the image
    diagonal_length = compute_image_diagonal(original_image)

    # Convert distanceMax and distanceMin from percentage to pixel values
    distance_max_px = args.distanceMax * diagonal_length
    distance_min_px = args.distanceMin * diagonal_length

    if args.verbose:
        print(f"Retrieving contours from image {corrected_image_path}...")

    # Load the contours and paths with debug mode
    contours = retrieve_contours(corrected_image_path, debug=args.debug)

    if args.verbose:
        print("Processing contours into linear paths...")

    linear_paths = contour_to_linear_paths(
        contours, epsilon_factor=args.epsilon, max_distance=distance_max_px, min_distance=distance_min_px, image=original_image, debug=args.debug
    )

    # Get the dimensions of the original image
    image_height, image_width = original_image.shape[:2]

    font_path = find_font_in_windows(args.font)

    if args.verbose:
        print("Drawing points and labels on the image...")

    # Draw the points on two blank images (one with lines, one without)
    output_image_with_dots = draw_points_on_image(
        (image_height, image_width), linear_paths, args.radius, tuple(
            args.dotColor), font_path, args.fontSize, tuple(args.fontColor), debug=args.debug
    )

    if args.verbose:
        print(f"Saving the output image to {args.output}...")

    # Save the output images with the specified DPI
    save_image(output_image_with_dots, f"{args.output}", args.dpi)

    # Display output if --displayOutput is set or --debug is enabled
    if args.debug or args.displayOutput:
        debug_image = resize_for_debug(output_image_with_dots)
        display_with_matplotlib(debug_image, 'Output')
        plt.show()

    print("Processing complete.")
