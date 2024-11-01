# image_discretization.py

import cv2
import numpy as np
from skimage.morphology import skeletonize
import networkx as nx
import matplotlib.pyplot as plt
import utils


class ImageDiscretization:

    def __init__(self, image_path, contour_mode, threshold_values, debug):
        self.contour_mode = contour_mode
        self.debug = debug
        self.threshold_values = threshold_values
        self.image_path = image_path
        self.image = cv2.imread(self.image_path, cv2.IMREAD_UNCHANGED)

        if self.image is None:
            raise FileNotFoundError(
                f"Image file '{self.image_path}' could not be found or the path is incorrect."
            )

        # Handle the alpha channel and remove transparency if it exists
        image = self.handle_alpha_channel()
        if self.debug:
            # Display the original image without any modifications
            original_image = image.copy()  # Copy to avoid any changes
            debug_image = utils.resize_for_debug(original_image)
            utils.display_with_matplotlib(debug_image, 'Original Image')
        pass

    def discretize_image(self):
        contours, gray = self.retrieve_contours()
        if (self.contour_mode == 'contour'):
            return contours
        elif (self.contour_mode == 'path'):
            return self.retrieve_skeleton_path(contours, gray)
        else:
            raise ValueError(
                f"Invalid contour_mode '{self.contour_mode}'. Use 'contour' or 'path'."
            )

    def retrieve_contours(self):
        """
        Retrieves the contours found in the image and displays intermediate steps if debug is enabled.
        """
        gray = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)

        # Use the threshold values provided as arguments
        threshold_value, max_value = self.threshold_values
        _, binary = cv2.threshold(gray, threshold_value, max_value,
                                  cv2.THRESH_BINARY_INV)

        # Find the contours
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL,
                                       cv2.CHAIN_APPROX_NONE)

        if not contours:
            print(
                "No contours were found in the image. You can modify the binary"
                " thresholding arguments (-tb) to search contours in a wider range."
                " Use debug argument (-de) to have more information.")
            plt.show()
            exit(-3)

        if self.debug:
            # Create a blank canvas for drawing contours
            height, width = self.image.shape[:2]
            blank_canvas = np.zeros((height, width, 3),
                                    dtype=np.uint8)  # Black background

            # Draw contours on the blank canvas
            cv2.drawContours(blank_canvas, contours, -1, (0, 255, 0),
                             1)  # Green contours

            # Resize for better visualization
            debug_image = utils.resize_for_debug(blank_canvas)
            utils.display_with_matplotlib(debug_image, 'Contours Only')

        return contours, gray

    def retrieve_skeleton_path(self, contours, gray):
        """
        Retrieves the skeleton path from the largest shape in the image.
        Ensures that the path is ordered in a clockwise direction.
        """
        # Create an empty mask
        mask = np.zeros_like(gray)

        # Find the largest contour by area
        largest_contour = max(contours, key=cv2.contourArea)

        # Draw the largest contour on the mask
        cv2.drawContours(mask, [largest_contour],
                         -1,
                         255,
                         thickness=cv2.FILLED)

        # Skeletonize the shape
        skeleton = skeletonize(mask / 255)  # Convert to binary image (0 and 1)

        if self.debug:
            debug_image = utils.resize_for_debug(
                (skeleton * 255).astype(np.uint8))
            utils.display_with_matplotlib(debug_image, 'Skeletonized Image')

        ordered_skeleton_points = self.prune_skeleton_to_one_branch(skeleton)

        # Convert the list of tuples to a NumPy array with shape (N, 1, 2)
        ordered_skeleton_array = np.array(ordered_skeleton_points,
                                          dtype=np.int32).reshape(-1, 1, 2)

        return [ordered_skeleton_array]

    def prune_skeleton_to_one_branch(self,
                                     skeleton,
                                     epsilon_factor=0.001,
                                     max_distance=None,
                                     min_distance=None,
                                     num_points=None):
        """
        Prunes the skeleton to retain only the longest branch. This method ensures that only the main structure remains,
        discarding minor branches.
        """
        y_coords, x_coords = np.nonzero(skeleton)
        skeleton_coords = list(zip(x_coords, y_coords))

        # Create graph of the skeleton
        G = nx.Graph()
        for x, y in skeleton_coords:
            G.add_node((x, y))
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    if dx != 0 or dy != 0:
                        nx_ = x + dx
                        ny_ = y + dy
                        if (0 <= nx_ < skeleton.shape[1]
                                and 0 <= ny_ < skeleton.shape[0]
                                and skeleton[ny_, nx_]):
                            G.add_edge((x, y), (nx_, ny_))

        # Find endpoints (degree 1 nodes)
        endpoints = [node for node in G.nodes() if G.degree(node) == 1]

        if len(endpoints) < 2:
            start = next(iter(G.nodes()))
            longest_path = list(nx.dfs_preorder_nodes(G, source=start))
        else:
            longest_path = self.find_longest_path(G, endpoints)
        points_list = [(int(p[0]), int(p[1])) for p in longest_path]
        return points_list

    def find_longest_path(self, G, endpoints):
        """
        Finds the longest path between any two endpoints in the skeleton graph.
        """
        max_length = 0
        longest_path = []

        for i in range(len(endpoints)):
            for j in range(i + 1, len(endpoints)):
                try:
                    path = nx.shortest_path(G,
                                            source=endpoints[i],
                                            target=endpoints[j])
                    length = self.path_length(path)
                    if length > max_length:
                        max_length = length
                        longest_path = path
                except nx.NetworkXNoPath:
                    continue
        return longest_path

    def path_length(self, path):
        """Calculate the Euclidean length of a path."""
        return sum(
            utils.point_distance(path[i], path[i + 1])
            for i in range(len(path) - 1))

    def handle_alpha_channel(self):
        if self.image.shape[2] == 4:
            bgr_image = self.image[:, :, :3]
            alpha_channel = self.image[:, :, 3]
            green_background = (0, 255, 0)
            mask = alpha_channel < 255
            bgr_image[mask] = green_background
            return bgr_image
        return self.image
