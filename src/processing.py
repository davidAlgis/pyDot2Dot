# processing.py

import cv2
import time
import utils
from image_discretization import ImageDiscretization
from dots_selection import DotsSelection
from image_creation import ImageCreation


def process_single_image(input_path, output_path, args, save_output=True):
    start_time = time.time()

    if args.verbose:
        print(f"Loading the corrected image from {input_path}...")

    # Load the corrected image for processing
    original_image = cv2.imread(input_path)
    try:
        num_points = int(args.numPoints)
    except:
        num_points = None

    # Compute the diagonal of the image
    diagonal_length = utils.compute_image_diagonal(original_image)

    # Parse distance_min and distance_max values from the combined distance argument
    if args.distance and args.distance != ("", ""):
        distance_min = utils.parse_size(args.distance[0], diagonal_length)
        distance_max = utils.parse_size(args.distance[1], diagonal_length)
    else:
        distance_min = None
        distance_max = None

    # Parse radius and font size values
    radius_px = utils.parse_size(args.radius, diagonal_length)
    font_size_px = int(utils.parse_size(args.fontSize, diagonal_length))

    if args.verbose:
        print(
            f"Processing image {input_path} using '{args.shapeDetection}' method..."
        )

    image_discretization = ImageDiscretization(input_path,
                                               args.shapeDetection.lower(),
                                               args.thresholdBinary,
                                               args.debug)

    contour = image_discretization.discretize_image()

    # Initialize DotsSelection with desired parameters
    dots_selection = DotsSelection(
        epsilon_factor=args.epsilon,  # Assuming args.epsilon is provided
        max_distance=distance_max,  # Parsed from args.distance_max
        min_distance=distance_min,  # Parsed from args.distance_min
        num_points=num_points,  # Number of points to simplify
        image=original_image,  # Original image if needed
        contour=contour,  # Contours from discretize_image
        debug=args.debug  # Debug flag
    )

    linear_paths = dots_selection.contour_to_linear_paths()

    # Get the dimensions of the original image
    image_height, image_width = original_image.shape[:2]

    font_path = utils.find_font_in_windows(args.font)

    if args.verbose:
        print("Drawing points and labels on the image...")

    # Create an instance of ImageCreation with required parameters
    image_creation = ImageCreation(image_size=(image_height, image_width),
                                   linear_paths=linear_paths,
                                   radius=radius_px,
                                   dot_color=tuple(args.dotColor),
                                   font_path=utils.find_font_in_windows(
                                       args.font),
                                   font_size=font_size_px,
                                   font_color=tuple(args.fontColor),
                                   debug=args.debug)
    # Draw the points on the image with a transparent background
    output_image_with_dots, dots, labels, combined_image_np, invalid_indices = image_creation.draw_points_on_image(
        input_path)

    elapsed_time = time.time() - start_time

    if args.verbose:
        print(f"Elapsed time for image processing: {elapsed_time:.2f} seconds")

    if save_output and output_path:
        if args.verbose:
            print(f"Saving the output image to {output_path}...")
        # Save the output images with the specified DPI
        utils.save_image(output_image_with_dots, output_path, args.dpi)

    # Return the processed image, elapsed time, dots, and labels
    return output_image_with_dots, elapsed_time, dots, labels, image_discretization.have_multiple_contours, combined_image_np, invalid_indices
