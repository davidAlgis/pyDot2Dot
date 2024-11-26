from dot_label import DotLabel


class Dot:
    """
    Class to represent a dot with associated properties and label.
    """

    def __init__(self, position, dot_id):
        self.position = position  # Position of the dot (x, y)
        self.dot_id = dot_id  # Unique ID for the dot
        self.color = (0, 0, 0, 255)  # Dot color as RGBA tuple
        self.radius = 10  # Radius of the dot
        self.label = None  # Associated DotLabel object
        self.overlap_other_dots = False

    def add_possible_label_position(self, position):
        self.label.add_possible_position(position)

    def set_label(self, position, color, font, font_size):
        self.label = DotLabel(position, color, font, font_size)

    def set_color_font(self, color):
        self.label.set_color_font(color)

    def set_font_size(self, size):
        self.label.set_font_size(size)

    def set_font(self, font):
        self.label.set_font(font)

    def __repr__(self):
        return (
            f"Dot(position={self.position}, dot_id={self.dot_id}, color={self.color}, "
            f"radius={self.radius}, label={repr(self.label)})")
