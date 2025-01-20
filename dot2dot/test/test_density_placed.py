import numpy as np
import random
import math
from PIL import Image, ImageDraw, ImageFont
from dot2dot.dot import Dot
from dot2dot.dot_label import DotLabel
from dot2dot.grid_dots import GridDots
from dot2dot.utils import kernel_cubic_spline


# Define Dot and DotLabel classes if not imported from dot2dot
class DotLabel:

    def __init__(self, position, color, font, font_size, anchor, label_id):
        self.position = position
        self.color = color
        self.font = font
        self.font_size = font_size
        self.anchor = anchor
        self.label_id = label_id
        self.text = str(label_id)  # The text of the label

    @staticmethod
    def default_position_label(dot_pos, dot_radius):
        distance_from_dots = 1.2 * dot_radius
        position_label = (dot_pos[0] + distance_from_dots,
                          dot_pos[1] - distance_from_dots)
        return position_label


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
        self.radius = self.dots[0].radius
        self.radius_label_pos = 5 * int(self.radius)
        self.h = 7 * int(self.radius)
        self.debug = debug
        self.grid = GridDots(self.image_size[0], self.image_size[1], self.h,
                             self.dots)
        self.random_smoothed_density_disposition(10)

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

    def random_smoothed_density_disposition(self, number_try):
        """
        Randomly selects the best label position based on smoothed density constraints.
        Adds a plot for a specific dot X, showing:
        - The dot and its neighbors
        - All tested positions in opaque
        - A color for each tested position based on density
        - A cross on the chosen position.
        """
        # Specify which dot (by ID) to visualize
        dot_to_visualize = 3  # Change this to the dot_id you want to visualize
        plot_data = None

        possible_anchors = ["ls", "rs", "ms"]  # List of possible anchors

        for dot in self.dots:
            label = dot.label
            random_positions = []

            # Default position based on radius with a random anchor
            default_pos = DotLabel.default_position_label(
                dot.position, dot.radius)
            default_anchor = random.choice(possible_anchors)  # Random anchor
            random_positions.append({
                "position": default_pos,
                "anchor": default_anchor
            })

            # Generate random positions within radius_label_pos with random anchors
            for _ in range(number_try):
                theta = random.uniform(0, 2 * math.pi)  # Angle in radians
                r = random.uniform(dot.radius,
                                   self.radius_label_pos)  # Random radius
                random_pos = (dot.position[0] + r * math.cos(theta),
                              dot.position[1] + r * math.sin(theta))
                random_anchor = random.choice(possible_anchors)
                random_positions.append({
                    "position": random_pos,
                    "anchor": random_anchor
                })

            # Evaluate positions based on smoothed density
            min_density = float('inf')
            ref_pos = default_pos
            ref_anchor = default_anchor
            position_density_data = []

            for idx, pos_data in enumerate(random_positions):
                pos = pos_data["position"]
                anchor = pos_data["anchor"]
                label.position = pos
                label.anchor = anchor

                overlap_found, _, _ = self.grid.do_overlap(label)
                if overlap_found:
                    density = float(
                        'inf')  # Assign infinite density for overlaps
                else:
                    density = self.smoothing_density_label(label, pos)

                # Reduce density for the default position to favor it
                if idx == 0:
                    density *= 0.9

                position_density_data.append((pos, density))

                if density < min_density:
                    min_density = density
                    ref_pos = pos
                    ref_anchor = anchor

            # Assign the best position and anchor to the label
            label.position = ref_pos
            label.anchor = ref_anchor

            # Collect data for plotting if the current dot matches the one to visualize
            if dot.dot_id == dot_to_visualize:
                plot_data = {
                    "dot": dot,
                    "random_positions": random_positions,
                    "position_density_data": position_density_data,
                    "chosen_position": ref_pos
                }

    def smoothing_density_label(self, label, pos):
        """
            Calculates smoothed density for a given label position using neighboring labels.
            """
        neighbors = self.grid.find_neighbors(label)
        density = 0
        for neighbor in neighbors:
            # Mass of the neighbor, defined as the diagonal of its bounding box
            mass_neighbor = 0
            if isinstance(neighbor, Dot):
                mass_neighbor = neighbor.radius
            elif isinstance(neighbor, DotLabel):
                x_min, y_min, x_max, y_max = self.grid.get_label_bbox(neighbor)
                mass_neighbor = math.sqrt((x_max - x_min)**2 +
                                          (y_max - y_min)**2)
            w_ij = kernel_cubic_spline(pos, neighbor.position, self.h)
            distance = math.sqrt((pos[0] - neighbor.position[0])**2 +
                                 (pos[1] - neighbor.position[1])**2)
            density += mass_neighbor * w_ij
            # print(
            #     f"        mass neighbor = {mass_neighbor} and w_ij = {w_ij}, x_i = {pos}, x_j ={neighbor.position}, distance = {distance}"
            # )
        # print(f"    density = {density}")
        return density


# Initialize the dots and their labels
def initialize_dots():
    font = ImageFont.truetype("arial.ttf",
                              size=57)  # Update to a valid font path if needed

    dots = [
        Dot(
            position=(2530, 2179),
            dot_id=206,
            color=(0, 0, 0, 255),
            radius=9,
            label=DotLabel(position=(2540.8, 2168.2),
                           color=(0, 0, 0, 255),
                           font=font,
                           font_size=57,
                           anchor="ls",
                           label_id=206),
        ),
        Dot(
            position=(2508, 2144),
            dot_id=207,
            color=(0, 0, 0, 255),
            radius=9,
            label=DotLabel(position=(2518.8, 2133.2),
                           color=(0, 0, 0, 255),
                           font=font,
                           font_size=57,
                           anchor="ls",
                           label_id=207),
        ),
        Dot(
            position=(2475, 2113),
            dot_id=208,
            color=(0, 0, 0, 255),
            radius=9,
            label=DotLabel(position=(2485.8, 2102.2),
                           color=(0, 0, 0, 255),
                           font=font,
                           font_size=57,
                           anchor="ls",
                           label_id=208),
        ),
        Dot(
            position=(2446, 2095),
            dot_id=209,
            color=(0, 0, 0, 255),
            radius=9,
            label=DotLabel(position=(2456.8, 2084.2),
                           color=(0, 0, 0, 255),
                           font=font,
                           font_size=57,
                           anchor="ls",
                           label_id=209),
        ),
        Dot(
            position=(2408, 2087),
            dot_id=210,
            color=(0, 0, 0, 255),
            radius=9,
            label=DotLabel(position=(2418.8, 2076.2),
                           color=(0, 0, 0, 255),
                           font=font,
                           font_size=57,
                           anchor="ls",
                           label_id=210),
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
