import utils
from dot import Dot


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
    ):
        self.dot_control = dot_control
        self.input_path = input_path
        self.output_path = output_path
        self.dpi = dpi
        self.threshold_binary = threshold_binary
        self.distance_min = distance_min
        self.distance_max = distance_max
        self.epsilon = epsilon
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

        if args.distance[0] != '':
            distance_min = int(args.distance[0])
        else:
            distance_min = None

        if args.distance[1] != '':
            distance_max = int(args.distance[1])
        else:
            distance_max = None
        return DotsConfig(dot_control=dot_control,
                          input_path=args.input,
                          output_path=args.output,
                          dpi=args.dpi,
                          threshold_binary=args.thresholdBinary,
                          distance_min=distance_min,
                          distance_max=distance_max,
                          epsilon=args.epsilon,
                          shape_detection=args.shapeDetection.lower())

    def is_valid(self):

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
        if self.shape_detection not in ["automatic", "path", "contour"]:
            print(
                f"Invalid shape_detection: {self.shape_detection} must be 'path' or 'contour'."
            )
            return False

        # If all checks pass, the configuration is valid
        return True

    def reset_dot_control(self, config):
        DotsConfig.reset_dot_control(self.dot_control, config)

    @staticmethod
    def reset_dot_control(dot_control: Dot, config):
        default_diagonal_a4 = 36.37
        dot_control.radius = int(config["radius"])
        font_size_px = int(config["fontSize"])
        dot_control.color = tuple(config["dotColor"])
        font_path = utils.find_font_in_windows(config["font"])
        dot_control.set_label(tuple(config["fontColor"]), font_path,
                              font_size_px)

    @staticmethod
    def default_dots_config(config):
        default_diagonal_a4 = 36.37
        dot_control = Dot((0, 0), 0)
        DotsConfig.reset_dot_control(dot_control, config)
        input_path = config["input"]
        output_path = config["output"]
        shape_detection = config["shapeDetection"].lower()

        if config["distance"] and config["distance"] != ['', '']:
            distance_min = int(config["distance"][0])
            distance_max = int(config["distance"][1])
        else:
            distance_min = None
            distance_max = None
        dpi = config["dpi"]
        epsilon = float(config["epsilon"])
        threshold_binary = config["thresholdBinary"]
        return DotsConfig(dot_control, input_path, output_path, dpi,
                          threshold_binary, distance_min, distance_max,
                          epsilon, shape_detection)
