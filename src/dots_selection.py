# dots_selection.py

import cv2
import numpy as np
import matplotlib.pyplot as plt
import utils


class DotsSelection:

    def __init__(self):
        pass

    def contour_to_linear_paths(self,
                                contours,
                                epsilon_factor=0.001,
                                max_distance=None,
                                min_distance=None,
                                num_points=None,
                                image=None,
                                debug=False):
        """
        Converts each contour into a sequence of dominant points with optional pruning and curvature analysis.
        """
        dominant_points_list = []

        for contour in contours:
            # Convert the contour to a list of (x, y) tuples
            points = [(point[0][0], point[0][1]) for point in contour]

            # Step 1: Calculate the total arc length of the contour
            total_arc_length = self.calculate_arc_length(points)

            # Step 2: Prune points based on a fraction of the total arc length
            pruned_points = self.prune_points_arc_length(
                points, total_arc_length * 0.005)

            # Step 3: Calculate curvature on pruned points
            curvature = self.calculate_discrete_curvature(pruned_points)

            # Step 4: Identify top 10% points by curvature
            top_curvature_points = self.select_top_k_percent_points(
                pruned_points, curvature, top_percent=10)

            # Plot the results if debug mode is enabled
            if debug:
                plt.figure(figsize=(8, 6))
                x_coords, y_coords = zip(*pruned_points)
                plt.plot(x_coords,
                         y_coords,
                         'k--',
                         alpha=0.5,
                         label='Uniformly Sampled Contour')

                # Plot top curvature points
                if top_curvature_points:
                    tx, ty = zip(*top_curvature_points)
                    plt.scatter(tx,
                                ty,
                                s=50,
                                c='blue',
                                label='Top 5% Curvature Points',
                                marker='o')

                plt.title('Top Curvature Points on Pruned Contour')
                plt.xlabel('X-coordinate')
                plt.ylabel('Y-coordinate')
                plt.legend()
                plt.gca().invert_yaxis(
                )  # Invert y-axis to match image coordinates
                plt.show()

            epsilon = epsilon_factor * cv2.arcLength(np.array(points), True)
            approx = cv2.approxPolyDP(np.array(points, dtype=np.int32),
                                      epsilon, True)

            # Ensure clockwise direction using OpenCV's oriented area
            area = cv2.contourArea(approx, oriented=True)
            if area < 0:
                approx = approx[::-1]

            # Convert to a list of (x, y) tuples
            points = [(point[0][0], point[0][1]) for point in approx]

            # Optionally insert midpoints
            if max_distance is not None:
                points = utils.insert_midpoints(points, max_distance)

            # Optionally filter close points
            if min_distance is not None:
                points = utils.filter_close_points(points, min_distance)

            # Optionally simplify the path
            if num_points is not None:
                points = utils.visvalingam_whyatt(points,
                                                  num_points=num_points)

            dominant_points_list.append(points)

        return dominant_points_list

    # Helper methods moved from the original dot_2_dot.py

    def calculate_discrete_curvature(self, points):
        """
        Calculate discrete curvature at each point based on vector cross-products.
        """
        kappa = []
        for i in range(1, len(points) - 1):
            p1, p2, p3 = np.array(points[i - 1]), np.array(
                points[i]), np.array(points[i + 1])
            v1, v2 = p1 - p2, p3 - p2
            cross_product = np.cross(v1, v2)
            norm_v1, norm_v2 = np.linalg.norm(v1), np.linalg.norm(v2)
            sin_angle = cross_product / (
                norm_v1 * norm_v2) if norm_v1 * norm_v2 != 0 else 0
            curvature = abs(sin_angle) / (norm_v1 + norm_v2) if (
                norm_v1 + norm_v2) != 0 else 0
            kappa.append(curvature)
        return [0] + kappa + [0]  # Curvature at endpoints set to 0

    def select_top_k_percent_points(self, points, kappa, top_percent=5):
        """
        Select the top k% points based on curvature values.
        """
        num_points = len(kappa)
        num_top_points = max(1, int(num_points * top_percent / 100))
        indices = np.argsort(kappa)[-num_top_points:]
        selected_points = [points[i] for i in indices]
        return selected_points

    def calculate_arc_length(self, points):
        """
        Calculate the total arc length of a series of points.
        """
        arc_length = 0
        for i in range(1, len(points)):
            arc_length += np.linalg.norm(
                np.array(points[i]) - np.array(points[i - 1]))
        return arc_length

    def prune_points_arc_length(self, points, min_arc_length):
        """
        Remove points such that the arc length between consecutive pruned points 
        is at least min_arc_length.
        """
        pruned_points = [points[0]]
        accumulated_length = 0

        for i in range(1, len(points)):
            dist = np.linalg.norm(
                np.array(points[i]) - np.array(pruned_points[-1]))
            accumulated_length += dist
            if accumulated_length >= min_arc_length:
                pruned_points.append(points[i])
                accumulated_length = 0  # Reset the accumulator after adding a point

        return pruned_points
