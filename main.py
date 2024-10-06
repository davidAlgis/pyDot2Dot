import argparse
import os
import cv2
import matplotlib.pyplot as plt
import dot_2_dot
import utils
import time


def process_single_image(input_path, output_path, args):
    start_time = time.time()
    # Remove the ICC profile to prevent the warning and get a corrected image path
    # corrected_image_path = utils.remove_iccp_profile(input_path)

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
        return

    # Get the dimensions of the original image
    image_height, image_width = original_image.shape[:2]

    font_path = utils.find_font_in_windows(args.font)

    if args.verbose:
        print("Drawing points and labels on the image...")

    # Draw the points on the image with a transparent background
    output_image_with_dots = dot_2_dot.draw_points_on_image(
        (image_height, image_width),
        linear_paths,
        radius_px,
        tuple(args.dotColor),
        font_path,
        font_size_px,
        tuple(args.fontColor),
        debug=args.debug)

    if args.verbose:
        print(f"Saving the output image to {output_path}...")

    if args.verbose:
        print(f"Elapsed time for image processing : {elapsed_time} seconds")
    # Save the output images with the specified DPI
    utils.save_image(output_image_with_dots, output_path, args.dpi)

    # Delete the corrected image after processing
    # if os.path.exists(input_path):
    # os.remove(corrected_image_path)
    return elapsed_time


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=
        "Process an image or a folder of images and draw points at path vertices on a blank background."
    )
    parser.add_argument(
        '-i',
        '--input',
        type=str,
        default='input.png',
        help=
        'Input image path or folder (default: input.png). If a folder is provided, all images inside will be processed.'
    )
    parser.add_argument(
        '-o',
        '--output',
        type=str,
        default=None,
        help=
        'Output image path or folder. If not provided, the input name with "_dotted" will be used.'
    )
    parser.add_argument(
        '-sd',
        '--shapeDetection',
        type=str,
        default='Contour',
        help='Shape detection method: "Contour" or "Path" (default: "Contour")'
    )
    parser.add_argument(
        '-np',
        '--numPoints',
        type=int,
        default=200,
        help=
        'Desired number of points in the simplified path (applies to both methods).'
    )
    parser.add_argument('-e',
                        '--epsilon',
                        type=float,
                        default=0.001,
                        help='Epsilon for path approximation (default: 0.001)')
    parser.add_argument(
        '-d',
        '--distance',
        nargs=2,
        type=
        str,  # Change to string so it can accept both percentages and numbers
        default=None,  # use this syntax for default ("1%", "50%")
        help=
        'Minimum and maximum distances between points, either in pixels or percentages (e.g., -d 0.01 0.05 or -d 10% 50%).'
    )
    parser.add_argument(
        '-f',
        '--font',
        type=str,
        default='Arial.ttf',
        help='Font file name (searched automatically in C:\\Windows\\Fonts)')
    parser.add_argument(
        '-fs',
        '--fontSize',
        type=str,  # Change to string to allow percentage (e.g., "10%")
        default='1%',
        help=
        'Font size as pixels or percentage of the diagonal (e.g., 12 or 10%).')
    parser.add_argument(
        '-fc',
        '--fontColor',
        nargs=4,
        type=int,
        default=[0, 0, 0, 255],
        help=
        'Font color for labeling as 4 values in rgba format (default: black [0, 0, 0, 255])'
    )
    parser.add_argument(
        '-dc',
        '--dotColor',
        nargs=4,
        type=int,
        default=[0, 0, 0, 255],
        help=
        'Dot color as 4 values in rgba format (default: black [0, 0, 0, 255])')
    parser.add_argument(
        '-r',
        '--radius',
        type=str,
        default='0.5%',
        help=
        'Radius of the points as pixels or percentage of the diagonal (e.g., 12 or 8%).'
    )
    parser.add_argument('--dpi',
                        type=int,
                        default=400,
                        help='DPI of the output image (default: 400)')
    parser.add_argument(
        '-de',
        '--debug',
        type=utils.str2bool,
        nargs='?',
        const=True,
        default=False,
        help='Enable debug mode to display intermediate steps.')
    parser.add_argument(
        '-do',
        '--displayOutput',
        type=utils.str2bool,
        nargs='?',
        const=True,
        default=True,
        help='If set to True, display the output image after processing.')
    parser.add_argument(
        '-v',
        '--verbose',
        type=utils.str2bool,
        nargs='?',
        const=True,
        default=True,
        help=
        'If set to True, display progress prints to show the script\'s progress.'
    )
    parser.add_argument(
        '-tb',
        '--thresholdBinary',
        nargs=2,
        type=int,
        default=[100, 255],
        help=
        'Threshold and maximum value for binary thresholding (default: 100 255).'
    )
    parser.add_argument('-g',
                        '--gui',
                        type=utils.str2bool,
                        nargs='?',
                        const=True,
                        default=True,
                        help='Launch the graphical user interface.')

    args = parser.parse_args()

    if args.gui:
        try:
            from dot_2_dot_gui import DotToDotGUI
            app = DotToDotGUI()
            app.run()
        except ImportError as e:
            print(
                "Failed to import the GUI module. Ensure 'dot_2_dot_gui.py' is in the same directory."
            )
            sys.exit(1)
    else:
        # [Existing command-line processing code]
        print("Processing picture(s) to dot to dot...")

        # If input and output are folders, process all images in the folder
        if os.path.isdir(args.input) and (args.output is None
                                          or os.path.isdir(args.output)):
            output_dir = args.output if args.output else args.input
            image_files = [
                f for f in os.listdir(args.input)
                if f.lower().endswith(('.png', '.jpg', '.jpeg'))
            ]
            if args.verbose:
                print(
                    f"Processing {len(image_files)} images in the folder {args.input}..."
                )

            for image_file in image_files:
                input_path = os.path.join(args.input, image_file)
                output_path = utils.generate_output_path(
                    input_path,
                    os.path.join(output_dir, image_file)
                    if args.output else None)
                process_single_image(input_path, output_path, args)

        # Otherwise, process a single image
        elif os.path.isfile(args.input):
            output_path = utils.generate_output_path(args.input, args.output)
            process_single_image(args.input, output_path, args)
        else:
            print(
                f"Error - Input {args.input} does not exist or is not a valid file/folder."
            )

        # Display output if --displayOutput is set or --debug is enabled
        if args.debug or args.displayOutput:
            if os.path.isfile(
                    output_path):  # Check if the generated output file exists
                debug_image = utils.resize_for_debug(cv2.imread(output_path))
                utils.display_with_matplotlib(debug_image, 'Output')
                plt.show()

        print("Processing complete.")
