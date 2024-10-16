# processing.py

import cv2
import time
import utils
import dot_2_dot


def process_single_image(input_path, output_path, args, save_output=True):
    start_time = time.time()

    if args.verbose:
        print(f"Loading the corrected image from {input_path}...")

    # Load the corrected image for processing
    original_image = cv2.imread(input_path)

    # Compute the diagonal of the image
    diagonal_length = utils.compute_image_diagonal(original_image)

    # Parse distance_min and distance_max values from the combined distance argument
    if args.distance:
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

    if args.shapeDetection.lower() == 'contour':
        # Retrieve contours
        contours = dot_2_dot.retrieve_contours(input_path,
                                               args.thresholdBinary,
                                               debug=args.debug)

        if args.verbose:
            print("Processing contours into linear paths...")

        linear_paths = dot_2_dot.contour_to_linear_paths(
            contours,
            epsilon_factor=args.epsilon,
            max_distance=distance_max,
            min_distance=distance_min,
            num_points=args.numPoints,
            image=original_image,
            debug=args.debug)

    elif args.shapeDetection.lower() == 'path':
        # Path-based method using skeletonization
        linear_paths = dot_2_dot.retrieve_skeleton_path(
            input_path,
            epsilon_factor=args.epsilon,
            max_distance=distance_max,
            min_distance=distance_min,
            num_points=args.numPoints,
            debug=args.debug)

    else:
        print(
            f"Error - Invalid shape detection method '{args.shapeDetection}'. Use 'Contour' or 'Path'."
        )
        return None, None, None, None

    # Get the dimensions of the original image
    image_height, image_width = original_image.shape[:2]

    font_path = utils.find_font_in_windows(args.font)

    if args.verbose:
        print("Drawing points and labels on the image...")

    # Draw the points on the image with a transparent background
    output_image_with_dots, dots, labels = dot_2_dot.draw_points_on_image(
        (image_height, image_width),
        linear_paths,
        radius_px,
        tuple(args.dotColor),
        font_path,
        font_size_px,
        tuple(args.fontColor),
        debug=args.debug)

    elapsed_time = time.time() - start_time

    if args.verbose:
        print(f"Elapsed time for image processing: {elapsed_time:.2f} seconds")

    if save_output and output_path:
        if args.verbose:
            print(f"Saving the output image to {output_path}...")
        # Save the output images with the specified DPI
        utils.save_image(output_image_with_dots, output_path, args.dpi)

    # Return the processed image, elapsed time, dots, and labels
    return output_image_with_dots, elapsed_time, dots, labels
