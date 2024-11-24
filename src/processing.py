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

    # Safely parse num_points
    num_points = None
    if args.numPoints is not None:
        try:
            num_points = int(args.numPoints)
        except ValueError:
            raise ValueError(f"Invalid value for numPoints: {args.numPoints}")

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
    font_path = utils.find_font_in_windows(args.font)
    if not font_path:
        raise ValueError(
            f"Font '{args.font}' could not be found on the system.")
    image_height, image_width = original_image.shape[:2]

    if args.verbose:
        print(
            f"Processing image {input_path} using '{args.shapeDetection}' method..."
        )

    # Step 1: Image discretization
    image_discretization = ImageDiscretization(input_path,
                                               args.shapeDetection.lower(),
                                               args.thresholdBinary,
                                               args.debug)
    dots = image_discretization.discretize_image(
    )  # Returns a list of Dot objects
    print(args.shapeDetection)
    print(dots[0])

    # Step 2: Dot selection and filtering
    dots_selection = DotsSelection(
        epsilon_factor=args.epsilon,  # Assuming args.epsilon is provided
        max_distance=distance_max,  # Parsed from args.distance_max
        min_distance=distance_min,  # Parsed from args.distance_min
        num_points=num_points,  # Number of points to simplify
        dots=dots,  # Use the dots list instead of image or contour
        debug=args.debug  # Debug flag
    )

    selected_dots = dots_selection.contour_to_linear_paths(
    )  # Returns a refined list of Dot objects

    if args.verbose:
        print("Drawing points and labels on the image...")

    # Create an instance of ImageCreation with required parameters
    image_creation = ImageCreation(image_size=(image_height, image_width),
                                   dots=selected_dots,
                                   radius=radius_px,
                                   dot_color=tuple(args.dotColor),
                                   font_path=utils.find_font_in_windows(
                                       args.font),
                                   font_size=font_size_px,
                                   font_color=tuple(args.fontColor),
                                   debug=args.debug)

    # Draw the points on the image with a transparent background
    output_image_with_dots, updated_dots, combined_image_np, invalid_indices = image_creation.draw_points_on_image(
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
    return (
        output_image_with_dots,
        elapsed_time,
        updated_dots,
        [dot.label for dot in updated_dots if dot.label is not None],
        image_discretization.have_multiple_contours,
        None,
        []  # No invalid indices are returned for now
    )
