"""
Module to define the Dot class, representing a dot with associated properties and label.
"""

from dot2dot.dot_label import DotLabel


class Dot:
    """
    Represents a dot with a position, unique ID, and associated label.

    Attributes:
        position (tuple): Coordinates of the dot as (x, y).
        dot_id (int): Unique identifier for the dot.
        color (tuple): RGBA color of the dot. Default is black.
        radius (int): Radius of the dot. Default is 10.
        label (DotLabel): Associated label for the dot.
        overlap_other_dots (bool): Indicates if the dot overlaps with other dots.
        overlap_dot_list (list): List of other dots this dot overlaps with.
        overlap_label_list (list): List of labels overlapping with this dot.
    """

    def __init__(self, position, dot_id):
        """
        Initializes a Dot instance.

        Args:
            position (tuple): Position of the dot (x, y).
            dot_id (int): Unique identifier for the dot.
        """
        self.position = position
        self.dot_id = dot_id
        self.color = (0, 0, 0, 255)  # Default color: black
        self.radius = 10  # Default radius
        self.label = None
        self.overlap_other_dots = False
        self.overlap_dot_list = []
        self.overlap_label_list = []

    def set_label(self, color, font_path, font_size):
        """
        Sets a label for the dot using the DotLabel class.

        Args:
            color (tuple): RGBA color for the label text.
            font_path (str): Path to the font file.
            font_size (int): Size of the font.
        """
        self.label = DotLabel(self.position, self.radius, color, font_path,
                              font_size, self.dot_id)

    def __repr__(self):
        """
        Returns a string representation of the Dot instance.
        """
        return (
            f"Dot(position={self.position}, dot_id={self.dot_id}, color={self.color}, "
            f"radius={self.radius}, label={repr(self.label)})")
