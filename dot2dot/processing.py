"""
Function to process a full image to a dot to dot image.
"""
import os
import time
import cv2
from dot2dot.image_discretization import ImageDiscretization
from dot2dot.dots_selection import DotsSelection
from dot2dot.image_creation import ImageCreation


def process_single_image(dots_config, debug=False):
    start_time = time.time()

    print(f"Loading the corrected image from {dots_config.input_path}...")

    if not os.path.isfile(dots_config.input_path):
        print(
            f"Couldn't process at address {dots_config.input_path}, which isn't a file."
        )
        return
    # Load the corrected image for processing
    original_image = cv2.imread(dots_config.input_path)

    image_height, image_width = original_image.shape[:2]

    print(
        f"Processing image {dots_config.input_path} using '{dots_config.shape_detection}' method..."
    )

    # Step 1: Image discretization
    image_discretization = ImageDiscretization(dots_config.input_path,
                                               dots_config.shape_detection,
                                               dots_config.threshold_binary,
                                               debug)
    dots = image_discretization.discretize_image()

    # Step 2: Dot selection and filtering
    dots_selection = DotsSelection(epsilon_factor=dots_config.epsilon,
                                   max_distance=dots_config.distance_max,
                                   min_distance=dots_config.distance_min,
                                   dots=dots,
                                   debug=debug)
    # Returns a refined list of Dot objects
    selected_dots = dots_selection.contour_to_linear_paths()

    print("Drawing points and labels on the image...")

    # Create an instance of ImageCreation with required parameters
    image_creation = ImageCreation(image_size=(image_height, image_width),
                                   dots=selected_dots,
                                   dot_control=dots_config.dot_control,
                                   debug=debug)

    # Draw the points on the image with a transparent background
    output_image_with_dots, updated_dots, combined_image_np = image_creation.draw_points_on_image(
        dots_config.input_path)

    elapsed_time = time.time() - start_time

    print(f"Elapsed time for image processing: {elapsed_time:.2f} seconds")

    # Return the processed image, elapsed time, dots, and labels
    return (output_image_with_dots, combined_image_np, elapsed_time,
            updated_dots, image_discretization.have_multiple_contours)
