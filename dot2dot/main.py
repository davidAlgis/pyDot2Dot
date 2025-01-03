"""
Entry point of the full dot to dot application
"""
import argparse
import traceback
import sys
import os
import cv2

from dot2dot.utils import str2bool, generate_output_path, save_image, resize_for_debug, display_with_opencv
from dot2dot.gui.main_gui import DotToDotGUI
from dot2dot.dots_config import DotsConfig
from dot2dot.processing import process_single_image
from dot2dot.load_config import LoadConfig


def main():
    try:
        config = LoadConfig()

        # Ensure the configuration is loaded correctly
        if not config.get_config():
            raise RuntimeError("Failed to load configuration.")

        parser = argparse.ArgumentParser(
            description=
            "Process an image or a folder of images and draw points at path vertices on a blank background."
        )
        parser.add_argument(
            '-i',
            '--input',
            type=str,
            default=config["input"],
            help='Input image path or folder (default: input.png).')
        parser.add_argument('-o',
                            '--output',
                            type=str,
                            default=config["output"],
                            help='Output image path or folder.')
        parser.add_argument(
            '-sd',
            '--shapeDetection',
            type=str,
            default=config["shapeDetection"],
            help=
            'Shape detection method: "Automatic", "Contour" or "Path" (default: "Automatic")'
        )
        parser.add_argument(
            '-d',
            '--distance',
            nargs=2,
            type=str,
            default=config["distance"],
            help='Minimum and maximum distances between points.')
        parser.add_argument('-f',
                            '--font',
                            type=str,
                            default=config["font"],
                            help='Font file name.')
        parser.add_argument('-fs',
                            '--fontSize',
                            type=str,
                            default=config["fontSize"],
                            help='Font size as pixels.')
        parser.add_argument('-fc',
                            '--fontColor',
                            nargs=4,
                            type=int,
                            default=config["fontColor"],
                            help='Font color in RGBA format.')
        parser.add_argument('-dc',
                            '--dotColor',
                            nargs=4,
                            type=int,
                            default=config["dotColor"],
                            help='Dot color in RGBA format.')
        parser.add_argument('-r',
                            '--radius',
                            type=str,
                            default=config["radius"],
                            help='Radius of points as pixels.')
        parser.add_argument('--dpi',
                            type=int,
                            default=config["dpi"],
                            help='DPI of the output image.')
        parser.add_argument('-e',
                            '--epsilon',
                            type=float,
                            default=config["epsilon"],
                            help='Epsilon for path approximation.')
        parser.add_argument('-de',
                            '--debug',
                            type=str2bool,
                            nargs='?',
                            const=True,
                            default=config["debug"],
                            help='Enable debug mode.')
        parser.add_argument('-do',
                            '--displayOutput',
                            type=str2bool,
                            nargs='?',
                            const=True,
                            default=config["displayOutput"],
                            help='Display the output image.')
        parser.add_argument('-v',
                            '--verbose',
                            type=str2bool,
                            nargs='?',
                            const=True,
                            default=config["verbose"],
                            help='Enable verbose mode.')
        parser.add_argument('-tb',
                            '--thresholdBinary',
                            nargs=2,
                            type=int,
                            default=config["thresholdBinary"],
                            help='Threshold for binary thresholding.')
        parser.add_argument('-g',
                            '--gui',
                            type=str2bool,
                            default=True,
                            help='Launch the graphical user interface.')
        args = parser.parse_args()

        if args.gui:
            try:
                app = DotToDotGUI(config)
                app.run()
            except ImportError as _:
                print(
                    "Failed to import the GUI module. Ensure the 'gui' package is in the same directory and contains 'main_gui.py'."
                )
                sys.exit(1)
            except Exception as e:
                print("Error occurred in GUI mode:", str(e))
                traceback.print_exc()
                sys.exit(1)
        else:
            try:
                dots_config = DotsConfig.arg_parse_to_dots_config(args)
                # [Existing command-line processing code]
                print("Processing picture(s) to dot to dot...")

                # If input and output are folders, process all images in the
                # folder
                if os.path.isdir(dots_config.input_path) and (
                        dots_config.output_path is None
                        or os.path.isdir(dots_config.output_path)):
                    output_dir = dots_config.output_path if dots_config.output_path else dots_config.input_path
                    image_files = [
                        f for f in os.listdir(dots_config.input_path)
                        if f.lower().endswith(('.png', '.jpg', '.jpeg'))
                    ]
                    if args.verbose:
                        print(
                            f"Processing {len(image_files)} images in the folder {dots_config.input_path}..."
                        )

                    for image_file in image_files:
                        input_path = os.path.join(dots_config.input_path,
                                                  image_file)
                        output_path_for_file = generate_output_path(
                            input_path,
                            os.path.join(output_dir, image_file)
                            if args.output else None)
                        output_image_with_dots, _, _, _, _ = process_single_image(
                            dots_config)
                        if output_path_for_file:
                            print(
                                f"Saving the output image to {output_path_for_file}..."
                            )
                            # Save the output images with the specified DPI
                            save_image(output_image_with_dots,
                                       output_path_for_file, dots_config.dpi)

                # Otherwise, process a single image
                elif os.path.isfile(dots_config.input_path):
                    output_path = generate_output_path(dots_config.input_path,
                                                       args.output)
                    output_image_with_dots, _, _, _, _ = process_single_image(
                        dots_config)
                    if dots_config.output_path:
                        print(
                            f"Saving the output image to {dots_config.output_path}..."
                        )
                        # Save the output images with the specified DPI
                        save_image(output_image_with_dots,
                                   dots_config.output_path, dots_config.dpi)
                        # Display output if --displayOutput is set or --debug is
                        # enabled
                        if args.debug or args.displayOutput:
                            if os.path.isfile(
                                    output_path
                            ):  # Check if the generated output file exists
                                debug_image = resize_for_debug(
                                    cv2.imread(output_path))
                                display_with_opencv(debug_image, 'Output')
                else:
                    print(
                        f"Error - Input {dots_config.input_path} does not exist or is not a valid file/folder."
                    )

                print("Processing complete.")
            except Exception as e:
                print("Error occurred in command-line mode:", str(e))
                traceback.print_exc()
                sys.exit(1)

    except Exception as e:
        error_message = f"An unexpected error occurred:\n{str(e)}\n{traceback.format_exc()}"
        print(error_message, file=sys.stderr)
        with open("error.log", "w") as error_file:
            error_file.write(error_message)
        sys.exit(1)


if __name__ == "__main__":
    main()
