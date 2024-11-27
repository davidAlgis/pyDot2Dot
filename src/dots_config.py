import cv2
import utils
from dot_label import DotLabel
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
        # we needs the diagonal length of image for further
        # computation, therefore we needs to load the image with cv2
        original_image = cv2.imread(args.input_path)
        # Compute the diagonal of the image
        diagonal_length = utils.compute_image_diagonal(original_image)

        # defined the reference dots from args
        dot_control = Dot((0, 0), 0)
        # Parse radius and font size values
        radius_px = utils.parse_size(args.radius, diagonal_length)
        dot_control.radius = radius_px
        font_size_px = int(utils.parse_size(args.fontSize, diagonal_length))
        font_path = utils.find_font_in_windows(args.font)
        if not font_path:
            raise ValueError(
                f"Font '{args.font}' could not be found on the system.")
        dot_control.color = tuple(args.dotColor)
        dot_control.set_label(tuple(args.fontColor), font_path, font_size_px)

        # Parse distance_min and distance_max values from the combined distance argument
        if args.distance and args.distance != ("", ""):
            distance_min = utils.parse_size(args.distance[0], diagonal_length)
            distance_max = utils.parse_size(args.distance[1], diagonal_length)
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
        original_image = cv2.imread(input_path)
        # Compute the diagonal of the image
        diagonal_length = utils.compute_image_diagonal(original_image)

        # defined the reference dots from args
        dot_control = Dot((0, 0), 0)
        # Parse radius and font size values
        radius_px = utils.parse_size(main_gui.radius.get(), diagonal_length)
        dot_control.radius = radius_px
        font_size_px = int(
            utils.parse_size(main_gui.font_size.get(), diagonal_length))
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
            distance_min = utils.parse_size(main_gui.distance_min.get(),
                                            diagonal_length)
            distance_max = utils.parse_size(main_gui.distance_max.get(),
                                            diagonal_length)
        else:
            distance_min = None
            distance_max = None

        num_dots = (int(main_gui.num_points.get())
                    if main_gui.num_points.get().strip() else None)

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
        # TODO
        return True
