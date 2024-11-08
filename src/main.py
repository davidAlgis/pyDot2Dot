# main.py

import argparse
import os
import cv2
import matplotlib.pyplot as plt
import utils
import time
import sys

from gui.main_gui import DotToDotGUI
from processing import process_single_image
import config

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=
        "Process an image or a folder of images and draw points at path vertices on a blank background."
    )
    parser.add_argument(
        '-i',
        '--input',
        type=str,
        default=config.DEFAULTS["input"],
        help='Input image path or folder (default: input.png).')
    parser.add_argument('-o',
                        '--output',
                        type=str,
                        default=config.DEFAULTS["output"],
                        help='Output image path or folder.')
    parser.add_argument(
        '-sd',
        '--shapeDetection',
        type=str,
        default=config.DEFAULTS["shapeDetection"],
        help='Shape detection method: "Contour" or "Path" (default: "Contour")'
    )
    parser.add_argument(
        '-np',
        '--numPoints',
        type=str,
        default=config.DEFAULTS["numPoints"],
        help='Desired number of points in the simplified path.')
    parser.add_argument('-d',
                        '--distance',
                        nargs=2,
                        type=str,
                        default=config.DEFAULTS["distance"],
                        help='Minimum and maximum distances between points.')
    parser.add_argument('-f',
                        '--font',
                        type=str,
                        default=config.DEFAULTS["font"],
                        help='Font file name.')
    parser.add_argument('-fs',
                        '--fontSize',
                        type=str,
                        default=config.DEFAULTS["fontSize"],
                        help='Font size as pixels or percentage.')
    parser.add_argument('-fc',
                        '--fontColor',
                        nargs=4,
                        type=int,
                        default=config.DEFAULTS["fontColor"],
                        help='Font color in RGBA format.')
    parser.add_argument('-dc',
                        '--dotColor',
                        nargs=4,
                        type=int,
                        default=config.DEFAULTS["dotColor"],
                        help='Dot color in RGBA format.')
    parser.add_argument('-r',
                        '--radius',
                        type=str,
                        default=config.DEFAULTS["radius"],
                        help='Radius of points as pixels or percentage.')
    parser.add_argument('--dpi',
                        type=int,
                        default=config.DEFAULTS["dpi"],
                        help='DPI of the output image.')
    parser.add_argument('-e',
                        '--epsilon',
                        type=float,
                        default=config.DEFAULTS["epsilon"],
                        help='Epsilon for path approximation.')
    parser.add_argument('-de',
                        '--debug',
                        type=utils.str2bool,
                        nargs='?',
                        const=True,
                        default=config.DEFAULTS["debug"],
                        help='Enable debug mode.')
    parser.add_argument('-do',
                        '--displayOutput',
                        type=utils.str2bool,
                        nargs='?',
                        const=True,
                        default=config.DEFAULTS["displayOutput"],
                        help='Display the output image.')
    parser.add_argument('-v',
                        '--verbose',
                        type=utils.str2bool,
                        nargs='?',
                        const=True,
                        default=config.DEFAULTS["verbose"],
                        help='Enable verbose mode.')
    parser.add_argument('-tb',
                        '--thresholdBinary',
                        nargs=2,
                        type=int,
                        default=config.DEFAULTS["thresholdBinary"],
                        help='Threshold for binary thresholding.')
    parser.add_argument('-g',
                        '--gui',
                        type=utils.str2bool,
                        default=True,
                        help='Launch the graphical user interface.')
    args = parser.parse_args()

    if args.gui:
        try:
            app = DotToDotGUI()
            app.run()
        except ImportError as e:
            print(
                "Failed to import the GUI module. Ensure the 'gui' package is in the same directory and contains 'main_gui.py'."
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
