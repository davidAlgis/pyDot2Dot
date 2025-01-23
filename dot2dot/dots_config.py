"""
Module defining the DotsConfig class for managing dot configuration settings.
"""

from dot2dot.utils import find_font_in_windows
from dot2dot.dot import Dot


class DotsConfig:
    """
    Class that contains the minimal configuration for dot settings.

    Attributes:
        dot_control (Dot): Dot configuration object.
        input_path (str): Path to the input file.
        output_path (str): Path to the output file.
        dpi (int): Resolution of the output in dots per inch.
        threshold_binary (list): Binary threshold values [min, max].
        distance_min (float or None): Minimum distance between dots.
        distance_max (float or None): Maximum distance between dots.
        epsilon (float): Epsilon value for contour approximation.
        shape_detection (str): Shape detection mode ('automatic', 'path', 'contour').
    """

    MAX_ATTRIBUTES = 7

    def __init__(
        self,
        dot_control,
        input_path,
        output_path,
        dpi,
        threshold_binary,
        distance_min=None,
        distance_max=None,
        epsilon=0.01,
        shape_detection="automatic",
    ):
        """
        Initializes a DotsConfig instance.

        Args:
            dot_control (Dot): Dot configuration object.
            input_path (str): Path to the input file.
            output_path (str): Path to the output file.
            dpi (int): Resolution of the output in dots per inch.
            threshold_binary (list): Binary threshold values [min, max].
            distance_min (float or None): Minimum distance between dots. Default is None.
            distance_max (float or None): Maximum distance between dots. Default is None.
            epsilon (float): Epsilon value for contour approximation. Default is 0.01.
            shape_detection (str): Shape detection mode. Default is "automatic".
        """
        self.dot_control = dot_control
        self.input_path = input_path
        self.output_path = output_path
        self.dpi = dpi
        self.threshold_binary = threshold_binary
        self.distance_min = distance_min
        self.distance_max = distance_max
        self.epsilon = epsilon
        self.shape_detection = shape_detection.lower()

        if not self.is_valid():
            print("DotsConfig is invalid")

    @staticmethod
    def arg_parse_to_dots_config(args):
        """
        Creates a DotsConfig instance from parsed command-line arguments.

        Args:
            args (Namespace): Parsed command-line arguments.

        Returns:
            DotsConfig: Configured instance.
        """
        dot_control = Dot((0, 0), 0)
        dot_control.radius = int(args.radius)
        font_size_px = int(args.fontSize)
        font_path = find_font_in_windows(args.font)
        if not font_path:
            raise ValueError(
                f"Font '{args.font}' could not be found on the system.")
        dot_control.color = tuple(args.dotColor)
        dot_control.set_label(tuple(args.fontColor), font_path, font_size_px)

        distance_min = int(args.distance[0]) if args.distance[0] else None
        distance_max = int(args.distance[1]) if args.distance[1] else None

        return DotsConfig(
            dot_control=dot_control,
            input_path=args.input,
            output_path=args.output,
            dpi=args.dpi,
            threshold_binary=args.thresholdBinary,
            distance_min=distance_min,
            distance_max=distance_max,
            epsilon=args.epsilon,
            shape_detection=args.shapeDetection.lower(),
        )

    def is_valid(self):
        """
        Validates the configuration.

        Returns:
            bool: True if the configuration is valid, False otherwise.
        """
        if not isinstance(self.dpi, int) or self.dpi <= 0:
            print(f"Invalid dpi: {self.dpi}. It must be a positive integer.")
            return False

        if not (isinstance(self.threshold_binary, list)
                and len(self.threshold_binary) == 2 and all(
                    isinstance(x, int) and 0 <= x <= 256
                    for x in self.threshold_binary)):
            print(f"Invalid threshold_binary: {self.threshold_binary}. "
                  "It must be a list of two integers between 0 and 256.")
            return False

        if self.threshold_binary[0] >= self.threshold_binary[1]:
            print(
                f"Threshold min {self.threshold_values[0]} should be less than "
                f"threshold max {self.threshold_values[1]}. Manually put it to 100"
            )
            self.threshold_binary[0] = 100
            return False

        if self.distance_min is not None and not isinstance(
                self.distance_min, (float, int)):
            print(
                f"Invalid distance_min: {self.distance_min}. It must be a float or None."
            )
            return False

        if self.distance_max is not None and not isinstance(
                self.distance_max, (float, int)):
            print(
                f"Invalid distance_max: {self.distance_max}. It must be a float or None."
            )
            return False

        if not isinstance(self.epsilon,
                          float) or not (1e-6 <= self.epsilon <= 10000):
            print(
                f"Invalid epsilon: {self.epsilon}. It must be a float between 1e-6 and 10000."
            )
            return False

        if self.shape_detection not in ["automatic", "path", "contour"]:
            print(f"Invalid shape_detection: {self.shape_detection}. "
                  "It must be 'automatic', 'path', or 'contour'.")
            return False

        return True

    @staticmethod
    def reset_dot_control(dot_control, config):
        """
        Resets the dot_control attributes based on a configuration.

        Args:
            dot_control (Dot): Dot instance to update.
            config (dict): Configuration dictionary.
        """
        dot_control.radius = int(config["radius"])
        font_size_px = int(config["fontSize"])
        dot_control.color = tuple(config["dotColor"])
        font_path = find_font_in_windows(config["font"])
        dot_control.set_label(tuple(config["fontColor"]), font_path,
                              font_size_px)

    @staticmethod
    def default_dots_config(config,
                            old_dots_config=None,
                            apply_input_path=True):
        """
        Creates a default DotsConfig instance from a configuration dictionary.

        Args:
            config (dict): Configuration dictionary.

        Returns:
            DotsConfig: Configured instance.
        """
        dot_control = Dot((0, 0), 0)
        DotsConfig.reset_dot_control(dot_control, config)

        distance_min = int(
            config["distance"][0]) if config["distance"][0] else None
        distance_max = int(
            config["distance"][1]) if config["distance"][1] else None
        input_path = config["input"]

        if apply_input_path is False and old_dots_config:
            input_path = old_dots_config.input_path

        return DotsConfig(
            dot_control=dot_control,
            input_path=input_path,
            output_path=config["output"],
            dpi=config["dpi"],
            threshold_binary=config["thresholdBinary"],
            distance_min=distance_min,
            distance_max=distance_max,
            epsilon=float(config["epsilon"]),
            shape_detection=config["shapeDetection"].lower(),
        )
