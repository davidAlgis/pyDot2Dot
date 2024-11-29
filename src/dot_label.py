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
                 anchor="ls"):
        self.position = DotLabel.default_position_label(
            associated_dot_position,
            associated_dot_radius)  # Position of the label (x, y)
        self.possible_position = [
        ]  # List of dicts with 'position' and 'anchor'
        self.color = color  # Font color as RGBA tuple
        self.font_path = font_path  # Font file path or name
        self.font_size = font_size  # Font size
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
