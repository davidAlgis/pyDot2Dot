from dot2dot.dot_label import DotLabel


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
        self.overlap_dot_list = []
        self.overlap_label_list = []

    def set_label(self, color, font_path, font_size):
        self.label = DotLabel(self.position, self.radius, color, font_path,
                              font_size, self.dot_id)

    def __repr__(self):
        return (
            f"Dot(position={self.position}, dot_id={self.dot_id}, color={self.color}, "
            f"radius={self.radius}, label={repr(self.label)})")
