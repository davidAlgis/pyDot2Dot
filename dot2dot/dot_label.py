"""
Module that contains all the data related to the label associated to each dot
"""
from PIL import ImageFont


class DotLabel:
    """
    Class to represent the label associated with a dot.
    """

    def __init__(self,
                 associated_dot_position,
                 associated_dot_radius,
                 color,
                 font_path,
                 font_size,
                 label_id,
                 anchor="ls"):
        self.position = DotLabel.default_position_label(
            associated_dot_position, associated_dot_radius)
        self.possible_position = [
        ]  # List of dicts with 'position' and 'anchor'
        self.color = color  # Font color as RGBA tuple
        self.label_id = label_id  # The text of the label
        self.text = str(label_id)  # The text of the label
        self.font_path = font_path  # Font file path or name
        self.font_size = font_size  # Font size
        self.has_move = False
        # Load the font
        try:
            self.font = ImageFont.truetype(self.font_path, self.font_size)
        except IOError:
            # Fallback to default font if specified font is not found
            self.font = ImageFont.load_default()
            print(
                f"Warning: Font '{self.font_path}' not found. Using default font."
            )
        self.anchor = anchor  # Anchor for the label
        self.overlap_other_dots = False
        self.overlap_dot_list = []
        self.overlap_label_list = []

    @staticmethod
    def default_position_label(dot_pos, dot_radius):
        distance_from_dots = 1.2 * dot_radius
        position_label = (dot_pos[0] + distance_from_dots,
                          dot_pos[1] - distance_from_dots)
        return position_label

    def add_possible_position(self, position, anchor):
        self.possible_position.append({"position": position, "anchor": anchor})

    def __repr__(self):
        return (
            f"DotLabel(position={self.position}, color={self.color}, "
            f"font='{self.font}', font_size={self.font_size}, anchor='{self.anchor}')"
        )
