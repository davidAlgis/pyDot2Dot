# image_discretization.py

import cv2
import numpy as np
from skimage.morphology import skeletonize
import networkx as nx
import matplotlib.pyplot as plt
import utils


class ImageDiscretization:

    def __init__(self, contour_mode, debug):
        self.contour_mode = contour_mode
        self.debug = debug
        pass

    def retrieve_contours(self, image_path, threshold_values, debug=False):
        """
        Retrieves the contours found in the image and displays intermediate steps if debug is enabled.
        """
        image = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)

        if image is None:
            raise FileNotFoundError(
                f"Image file '{image_path}' could not be found or the path is incorrect."
            )

        # Handle the alpha channel and remove transparency if it exists
        image_no_alpha = utils.handle_alpha_channel(image, debug=debug)

        if debug:
            # Display the original image without any modifications
            original_image = image_no_alpha.copy()  # Copy to avoid any changes
            debug_image = utils.resize_for_debug(original_image)
            utils.display_with_matplotlib(debug_image, 'Original Image')

        gray = cv2.cvtColor(image_no_alpha, cv2.COLOR_BGR2GRAY)

        # Use the threshold values provided as arguments
        threshold_value, max_value = threshold_values
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

        if debug:
            # Create a blank canvas for drawing contours
            height, width = image_no_alpha.shape[:2]
            blank_canvas = np.zeros((height, width, 3),
                                    dtype=np.uint8)  # Black background

            # Draw contours on the blank canvas
            cv2.drawContours(blank_canvas, contours, -1, (0, 255, 0),
                             1)  # Green contours

            # Resize for better visualization
            debug_image = utils.resize_for_debug(blank_canvas)
            utils.display_with_matplotlib(debug_image, 'Contours Only')

        return contours

    def retrieve_skeleton_path(self,
                               image_path,
                               epsilon_factor=0.001,
                               max_distance=None,
                               min_distance=None,
                               num_points=None,
                               debug=False):
        """
        Retrieves the skeleton path from the largest shape in the image.
        Ensures that the path is ordered in a clockwise direction.
        """
        image = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)

        if image is None:
            raise FileNotFoundError(
                f"Image file '{image_path}' could not be found or the path is incorrect."
            )

        image = utils.handle_alpha_channel(image, debug=debug)

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Threshold the image to obtain a binary image
        _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY_INV)

        # Find contours in the binary image
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL,
                                       cv2.CHAIN_APPROX_SIMPLE)

        if not contours:
            print(
                "No contours were found in the image. You can modify the binary"
                " thresholding arguments (-tb) to search contours in a wider range."
                " Use debug argument (-de) to have more information.")
            exit(-3)

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

        if debug:
            debug_image = utils.resize_for_debug(
                (skeleton * 255).astype(np.uint8))
            utils.display_with_matplotlib(debug_image, 'Skeletonized Image')

        ordered_skeleton_points = self.prune_skeleton_to_one_branch(skeleton)
        return [ordered_skeleton_points]
        # ordered_skeleton_points = self.ensure_clockwise_order(
        #     ordered_skeleton_points)
        # # Simplify the skeleton path
        # simplified_skeleton = self.simplify_path(ordered_skeleton_points,
        #                                          epsilon_factor=epsilon_factor,
        #                                          max_distance=max_distance,
        #                                          min_distance=min_distance,
        #                                          num_points=num_points)

        # if debug and image is not None:
        #     debug_image = image.copy()
        #     for point in simplified_skeleton:
        #         cv2.circle(debug_image, (point[0], point[1]), 3, (0, 0, 255),
        #                    -1)
        #     debug_image = utils.resize_for_debug(debug_image)
        #     utils.display_with_matplotlib(debug_image,
        #                                   'Simplified Skeleton Points')

        # # Return as a list containing one path (to be consistent with existing code)
        # return [simplified_skeleton]

    # Helper methods moved from the original dot_2_dot.py

    # def ensure_clockwise_order(self, points):
    #     """
    #     Ensures that the given set of points forms a path in clockwise order.
    #     Points should be a list of (x, y) tuples.
    #     """

    #     def signed_area(points):
    #         """
    #         Compute the signed area of the polygon formed by the points.
    #         Positive area indicates clockwise ordering, negative indicates counter-clockwise.
    #         """
    #         area = 0
    #         n = len(points)
    #         for i in range(n):
    #             x1, y1 = points[i]
    #             x2, y2 = points[(i + 1) % n]
    #             area += (x2 - x1) * (y2 + y1)
    #         return area

    #     # Compute the signed area of the points
    #     area = signed_area(points)

    #     # If the area is negative, the points are in counter-clockwise order
    #     if area > 0:
    #         return points[::-1]  # Reverse the points to make them clockwise

    #     # Otherwise, the points are already in clockwise order
    #     return points

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

        # Simplify the longest path
        simplified_skeleton = self.simplify_path(longest_path, epsilon_factor,
                                                 max_distance, min_distance,
                                                 num_points)

        return simplified_skeleton

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

    # def simplify_path(self,
    #                   points,
    #                   epsilon_factor=0.001,
    #                   max_distance=None,
    #                   min_distance=None,
    #                   num_points=None):
    #     """
    #     Simplifies the path using the Visvalingam–Whyatt algorithm and other optional parameters.
    #     """
    #     # Convert points to the required format (list of tuples)
    #     points_list = [(int(p[0]), int(p[1])) for p in points]

    #     # Optionally approximate the path (for skeletons, this might not be necessary)
    #     if epsilon_factor is not None:
    #         points_array = np.array(points_list, dtype=np.int32)
    #         epsilon = epsilon_factor * cv2.arcLength(points_array, False)
    #         approx = cv2.approxPolyDP(points_array, epsilon, False)
    #         points_list = [(int(p[0][0]), int(p[0][1])) for p in approx]

    #     # Optionally insert midpoints
    #     if max_distance is not None:
    #         points_list = utils.insert_midpoints(points_list, max_distance)

    #     # Optionally filter close points
    #     if min_distance is not None:
    #         points_list = utils.filter_close_points(points_list, min_distance)

    #     # Simplify the path using the Visvalingam–Whyatt algorithm
    #     if num_points is not None:
    #         points_list = utils.visvalingam_whyatt(points_list,
    #                                                num_points=num_points)

    #     return points_list
