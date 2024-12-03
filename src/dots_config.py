import cv2
import utils
from dot_label import DotLabel
from dot import Dot
import os


class DotsConfig:
    """
    Class that contains the minimal config for dots configuration.
    """

    def __init__(
        self,
        dot_control,
        input_path,
        output_path,
        dpi,
        threshold_binary,
        distance_min,
        distance_max,
        epsilon,
        shape_detection,
        nbr_dots,
    ):
        self.dot_control = dot_control
        self.input_path = input_path
        self.output_path = output_path
        self.dpi = dpi
        self.threshold_binary = threshold_binary
        self.distance_min = distance_min
        self.distance_max = distance_max
        self.epsilon = epsilon
        self.nbr_dots = nbr_dots
        self.shape_detection = shape_detection
        if not self.is_valid():
            print("Dots Config is invalid")

    @staticmethod
    def arg_parse_to_dots_config(args):

        # defined the reference dots from args
        dot_control = Dot((0, 0), 0)
        # Parse radius and font size values
        radius_px = int(args.radius)
        dot_control.radius = radius_px
        font_size_px = int(args.fontSize)
        font_path = utils.find_font_in_windows(args.font)
        if not font_path:
            raise ValueError(
                f"Font '{args.font}' could not be found on the system.")
        dot_control.color = tuple(args.dotColor)
        dot_control.set_label(tuple(args.fontColor), font_path, font_size_px)

        # Parse distance_min and distance_max values from the combined distance argument
        if args.distance and args.distance != ("", ""):
            distance_min = int(args.distance[0])
            distance_max = int(args.distance[1])
        else:
            distance_min = None
            distance_max = None

        num_dots = None
        if args.numPoints is not None:
            try:
                num_dots = int(args.numPoints)
            except ValueError:
                num_dots = None
        return DotsConfig(dot_control=dot_control,
                          input_path=args.input_path,
                          output_path=args.output_path,
                          dpi=args.dpi,
                          threshold_binary=args.thresholdBinary,
                          distance_min=distance_min,
                          distance_max=distance_max,
                          epsilon=args.epsilon,
                          shape_detection=args.shapeDetection.lower(),
                          nbr_dots=num_dots)

    @staticmethod
    def main_gui_to_dots_config(main_gui):
        # we needs the diagonal length of image for further
        # computation, therefore we needs to load the image with cv2
        input_path = main_gui.input_path.get()

        # defined the reference dots from args
        dot_control = Dot((0, 0), 0)
        # Parse radius and font size values
        radius_px = int(args.radius)
        dot_control.radius = radius_px
        font_size_px = int(main_gui.font_size.get())
        font_path = utils.find_font_in_windows(main_gui.font.get())
        if not font_path:
            raise ValueError(
                f"Font '{main_gui.font.get()}' could not be found on the system."
            )
        font_color = [int(c) for c in main_gui.font_color.get().split(',')
                      ] if main_gui.font_color.get() else [0, 0, 0, 255]
        dot_color = [int(c) for c in main_gui.dot_color.get().split(',')
                     ] if main_gui.dot_color.get() else [0, 0, 0, 255]
        dot_control.color = tuple(dot_color)
        dot_control.set_label(tuple(font_color), font_path, font_size_px)

        # Parse distance_min and distance_max values from the combined distance argument
        if main_gui.distance_min.get() and main_gui.distance_max.get() != ("",
                                                                           ""):
            distance_min = int(main_gui.distance_min.get())
            distance_max = int(main_gui.distance_max.get())
        else:
            distance_min = None
            distance_max = None

        num_dots = (int(main_gui.num_points.get())
                    if main_gui.num_points.get() != "" else None)

        shape_detection = main_gui.shape_detection.get().lower()
        threshold_binary = [
            main_gui.threshold_min.get(),
            main_gui.threshold_max.get()
        ]
        return DotsConfig(dot_control=dot_control,
                          input_path=input_path,
                          output_path=None,
                          dpi=main_gui.dpi.get(),
                          threshold_binary=threshold_binary,
                          distance_min=distance_min,
                          distance_max=distance_max,
                          epsilon=main_gui.epsilon.get(),
                          shape_detection=shape_detection,
                          nbr_dots=num_dots)

    def is_valid(self):
        # Validate input_path
        if not (os.path.isfile(self.input_path)
                or os.path.isdir(self.input_path)):
            print(
                f"Invalid input_path: {self.input_path} is not a file or folder."
            )
            return False

        # Validate dpi
        if not (isinstance(self.dpi, int) and self.dpi > 0):
            print(
                f"Invalid dpi: {self.dpi} must be a strictly positive integer."
            )
            return False

        # Validate threshold_binary
        if not (isinstance(self.threshold_binary, list)
                and len(self.threshold_binary) == 2 and all(
                    isinstance(x, int) and 0 <= x <= 256
                    for x in self.threshold_binary)):
            print(
                f"Invalid threshold_binary: {self.threshold_binary} must be a list of two integers between 0 and 256."
            )
            return False

        # Validate distance_min and distance_max
        if not (self.distance_min is None
                or isinstance(self.distance_min, float)):
            print(
                f"Invalid distance_min: {self.distance_min} must be a float.")
            return False

        if not (self.distance_max is None
                or isinstance(self.distance_max, float)):
            print(
                f"Invalid distance_max: {self.distance_max} must be a float.")
            return False

        # Validate epsilon
        if not (isinstance(self.epsilon, float)
                and 1e-6 <= self.epsilon <= 10000):
            print(
                f"Invalid epsilon: {self.epsilon} must be a float between 1e-6 and 10000."
            )
            return False

        # Validate shape_detection
        if self.shape_detection not in ["path", "contour"]:
            print(
                f"Invalid shape_detection: {self.shape_detection} must be 'path' or 'contour'."
            )
            return False

        # Validate nbr_dots
        if not (self.nbr_dots is None or (isinstance(self.nbr_dots, int)
                                          and 1 <= self.nbr_dots <= 100000)):
            print(
                f"Invalid nbr_dots: {self.nbr_dots} must be an integer between 1 and 100000, or None."
            )
            return False

        # If all checks pass, the configuration is valid
        return True
