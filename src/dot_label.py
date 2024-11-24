class DotLabel:
    """
    Class to represent the label associated with a dot.
    """

    def __init__(self, position, color, font, font_size):
        """
        Initializes a DotLabel object.

        Parameters:
        - position: Tuple (x, y) representing the position of the label.
        - color: Tuple (R, G, B, A) representing the color of the font.
        - font: String representing the font used for the label.
        - font_size: Integer representing the size of the font.
        """
        self.position = position  # Position of the label (x, y)
        self.possible_position = []
        self.color = color  # Font color as RGBA tuple
        self.font = font  # Font file path or name
        self.font_size = font_size  # Font size

    def add_possible_position(self, position):
        self.possible_position.append(position)

    def __repr__(self):
        return (f"DotLabel(position={self.position}, color={self.color}, "
                f"font='{self.font}', font_size={self.font_size})")
