import numpy as np
from PIL import Image, ImageDraw, ImageFont
from dot2dot.dot import Dot
from dot2dot.dot_label import DotLabel
from dot2dot.grid_dots import GridDots

# Define Dot and DotLabel classes if not imported from dot2dot
class DotLabel:
    def __init__(self, position, color, font, font_size, anchor):
        self.position = position
        self.color = color
        self.font = font
        self.font_size = font_size
        self.anchor = anchor


class Dot:
    def __init__(self, position, dot_id, color, radius, label):
        self.position = position
        self.dot_id = dot_id
        self.color = color
        self.radius = radius
        self.label = label


class ImageCreation:
    def __init__(self, image_size, dots, debug=False):
        self.image_size = image_size
        self.dots = dots
        self.debug = debug

    def draw_points_on_image(self):
        """
        Draws points and labels on an image using PIL.
        """
        # Create a blank image
        image = Image.new("RGBA", self.image_size, (255, 255, 255, 255))
        draw = ImageDraw.Draw(image)

        # Draw dots and labels
        for dot in self.dots:
            # Draw the dot
            x, y = dot.position
            radius = dot.radius
            draw.ellipse(
                [(x - radius, y - radius), (x + radius, y + radius)],
                fill=dot.color,
            )

            # Draw the label
            label = dot.label
            draw.text(
                label.position,
                str(dot.dot_id),
                font=label.font,
                fill=label.color,
                anchor=label.anchor,
            )

        return image


# Initialize the dots and their labels
def initialize_dots():
    font = ImageFont.truetype("arial.ttf", size=57)  # Update to a valid font path if needed

    dots = [
        Dot(
            position=(2530, 2179),
            dot_id=206,
            color=(0, 0, 0, 255),
            radius=9,
            label=DotLabel(
                position=(2540.8, 2168.2),
                color=(0, 0, 0, 255),
                font=font,
                font_size=57,
                anchor="ls",
            ),
        ),
        Dot(
            position=(2508, 2144),
            dot_id=207,
            color=(0, 0, 0, 255),
            radius=9,
            label=DotLabel(
                position=(2518.8, 2133.2),
                color=(0, 0, 0, 255),
                font=font,
                font_size=57,
                anchor="ls",
            ),
        ),
        Dot(
            position=(2475, 2113),
            dot_id=208,
            color=(0, 0, 0, 255),
            radius=9,
            label=DotLabel(
                position=(2485.8, 2102.2),
                color=(0, 0, 0, 255),
                font=font,
                font_size=57,
                anchor="ls",
            ),
        ),
        Dot(
            position=(2446, 2095),
            dot_id=209,
            color=(0, 0, 0, 255),
            radius=9,
            label=DotLabel(
                position=(2456.8, 2084.2),
                color=(0, 0, 0, 255),
                font=font,
                font_size=57,
                anchor="ls",
            ),
        ),
        Dot(
            position=(2408, 2087),
            dot_id=210,
            color=(0, 0, 0, 255),
            radius=9,
            label=DotLabel(
                position=(2418.8, 2076.2),
                color=(0, 0, 0, 255),
                font=font,
                font_size=57,
                anchor="ls",
            ),
        ),
    ]

    return dots


# Main function to test the visualization
if __name__ == "__main__":
    # Define image size
    image_size = (3000, 3000)  # Adjust to fit your data

    # Initialize dots
    dots = initialize_dots()

    # Create ImageCreation instance
    image_creator = ImageCreation(image_size=image_size, dots=dots, debug=True)

    # Generate the image with dots and labels
    final_image = image_creator.draw_points_on_image()

    # Save and show the image
    final_image.save("dots_with_labels.png")
    final_image.show()
