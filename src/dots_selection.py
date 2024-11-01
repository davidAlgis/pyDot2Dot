# dots_selection.py

import cv2
import numpy as np
import matplotlib.pyplot as plt
import utils
from typing import List, Tuple, Optional


class DotsSelection:
    """
    A class to handle the selection and processing of dots from image contours.

    Attributes:
        epsilon_factor (float): Factor to determine the approximation accuracy.
        max_distance (Optional[float]): Maximum distance to insert midpoints.
        min_distance (Optional[float]): Minimum distance to filter close points.
        num_points (Optional[int]): Number of points to simplify the path.
        image (Optional[np.ndarray]): The image being processed.
        contours (Optional[List[np.ndarray]]): List of contours extracted from the image.
        debug (bool): Flag to enable or disable debug mode.
    """

    def __init__(
        self,
        max_distance: Optional[float] = None,
        min_distance: Optional[float] = None,
        num_points: Optional[int] = None,
        image: Optional[np.ndarray] = None,
        contours: Optional[List[np.ndarray]] = None,
        debug: bool = False,
    ):
        """
        Initializes the DotsSelection instance with the given parameters.

        Args:
            epsilon_factor (float): Factor to determine the approximation accuracy.
            max_distance (Optional[float]): Maximum distance to insert midpoints.
            min_distance (Optional[float]): Minimum distance to filter close points.
            num_points (Optional[int]): Number of points to simplify the path.
            image (Optional[np.ndarray]): The image being processed.
            contours (Optional[List[np.ndarray]]): List of contours extracted from the image.
            debug (bool): Flag to enable or disable debug mode.
        """
        self.max_distance = max_distance
        self.min_distance = min_distance
        self.num_points = num_points
        self.image = image
        self.contours = contours
        self.debug = debug

    def contour_to_linear_paths(self) -> List[List[Tuple[int, int]]]:
        """
        Converts each contour into a sequence of dominant points with optional pruning and curvature analysis.

        Returns:
            List[List[Tuple[int, int]]]: A list of linear paths, each represented as a list of (x, y) tuples.
        """
        if self.contours is None:
            raise ValueError(
                "Contours must be set before calling contour_to_linear_paths.")

        dominant_points_list = []

        for contour in self.contours:
            # Ensure clockwise direction using OpenCV's oriented area
            area = cv2.contourArea(contour, oriented=True)
            if area < 0:
                contour = contour[::-1]
            # Convert the contour to a list of (x, y) tuples
            points = [(point[0][0], point[0][1]) for point in contour]

            # Step 1: Calculate the total arc length of the contour
            total_arc_length = self._calculate_arc_length(points)

            # Step 2: Prune points based on a fraction of the total arc length
            pruned_points = self._prune_points_arc_length(
                points, total_arc_length * 0.005)

            # Step 3: Calculate curvature on pruned points
            curvature = self._calculate_discrete_curvature(pruned_points)

            # Step 4: Identify top 10% points by curvature
            top_curvature_points = self._select_top_k_percent_points(
                pruned_points, curvature, top_percent=10)

            # Plot the results if debug mode is enabled
            if self.debug:
                self._plot_curvature(pruned_points, top_curvature_points)

            # Optionally insert midpoints
            if self.max_distance is not None:
                pruned_points = self.insert_midpoints(pruned_points,
                                                      self.max_distance)

            # Optionally filter close points
            if self.min_distance is not None:
                pruned_points = self.filter_close_points(
                    pruned_points, self.min_distance)

            # Optionally simplify the path
            if self.num_points is not None:
                pruned_points = self.visvalingam_whyatt(
                    pruned_points, num_points=self.num_points)

            dominant_points_list.append(pruned_points)

        return dominant_points_list

    def _calculate_discrete_curvature(
            self, points: List[Tuple[int, int]]) -> List[float]:
        """
        Calculate discrete curvature at each point based on vector cross-products.

        Args:
            points (List[Tuple[int, int]]): List of (x, y) points.

        Returns:
            List[float]: Curvature values for each point.
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

    def _select_top_k_percent_points(
            self,
            points: List[Tuple[int, int]],
            kappa: List[float],
            top_percent: float = 5) -> List[Tuple[int, int]]:
        """
        Select the top k% points based on curvature values.

        Args:
            points (List[Tuple[int, int]]): List of (x, y) points.
            kappa (List[float]): Curvature values corresponding to each point.
            top_percent (float): Percentage of top curvature points to select.

        Returns:
            List[Tuple[int, int]]: Selected top curvature points.
        """
        num_points = len(kappa)
        num_top_points = max(1, int(num_points * top_percent / 100))
        indices = np.argsort(kappa)[-num_top_points:]
        selected_points = [points[i] for i in indices]
        return selected_points

    def _calculate_arc_length(self, points: List[Tuple[int, int]]) -> float:
        """
        Calculate the total arc length of a series of points.

        Args:
            points (List[Tuple[int, int]]): List of (x, y) points.

        Returns:
            float: Total arc length.
        """
        arc_length = 0.0
        for i in range(1, len(points)):
            arc_length += np.linalg.norm(
                np.array(points[i]) - np.array(points[i - 1]))
        return arc_length

    def _prune_points_arc_length(
            self, points: List[Tuple[int, int]],
            min_arc_length: float) -> List[Tuple[int, int]]:
        """
        Remove points such that the arc length between consecutive pruned points is at least min_arc_length.

        Args:
            points (List[Tuple[int, int]]): List of (x, y) points.
            min_arc_length (float): Minimum arc length between points.

        Returns:
            List[Tuple[int, int]]: Pruned list of points.
        """
        pruned_points = [points[0]]
        accumulated_length = 0.0

        for i in range(1, len(points)):
            dist = np.linalg.norm(
                np.array(points[i]) - np.array(pruned_points[-1]))
            accumulated_length += dist
            if accumulated_length >= min_arc_length:
                pruned_points.append(points[i])
                accumulated_length = 0.0  # Reset the accumulator after adding a point

        return pruned_points

    def _plot_curvature(self, pruned_points: List[Tuple[int, int]],
                        top_curvature_points: List[Tuple[int, int]]) -> None:
        """
        Plot the pruned contour points and highlight the top curvature points.

        Args:
            pruned_points (List[Tuple[int, int]]): Pruned list of (x, y) points.
            top_curvature_points (List[Tuple[int, int]]): Top curvature points to highlight.
        """
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
                        label='Top 10% Curvature Points',
                        marker='o')

        plt.title('Top Curvature Points on Pruned Contour')
        plt.xlabel('X-coordinate')
        plt.ylabel('Y-coordinate')
        plt.legend()
        plt.gca().invert_yaxis()  # Invert y-axis to match image coordinates
        plt.show()

    def insert_midpoints(self, points, max_distance):
        """
        Inserts midpoints between consecutive points if the distance between them exceeds max_distance.
        Ensures that points remain in sequential order after midpoint insertion.
        """
        refined_points = []

        for i in range(len(points) - 1):
            p1, p2 = points[i], points[i + 1]
            refined_points.append(p1)  # Always keep the original point

            # Compute the number of midpoints needed
            distance = utils.point_distance(p1, p2)
            if distance > max_distance:
                num_midpoints = int(distance // max_distance)
                for j in range(1, num_midpoints + 1):
                    # Insert evenly spaced midpoints between p1 and p2
                    t = j / (num_midpoints + 1)
                    midpoint = (int(p1[0] * (1 - t) + p2[0] * t),
                                int(p1[1] * (1 - t) + p2[1] * t))
                    refined_points.append(midpoint)

        refined_points.append(points[-1])  # Add the last point
        return refined_points

    def filter_close_points(self, points, min_distance):
        """
        Removes points that are closer than min_distance.
        Keeps the first and last point always.
        """
        if len(points) < 2:
            return points  # Not enough points to filter

        filtered_points = [points[0]]  # Keep the first point

        for i in range(1, len(points) - 1):
            prev_point = filtered_points[-1]
            current_point = points[i]

            # Only keep points that are at least min_distance away
            if utils.point_distance(prev_point, current_point) >= min_distance:
                filtered_points.append(current_point)

        filtered_points.append(points[-1])  # Keep the last point
        return filtered_points

    def visvalingam_whyatt(self, points, num_points=None, threshold=None):
        """
        Simplify a path using the Visvalingam–Whyatt algorithm.
        """
        if len(points) < 3:
            return points

        # Initialize effective areas
        effective_areas = [float('inf')]  # First point has infinite area
        for i in range(1, len(points) - 1):
            area = utils.calculate_area(points[i - 1], points[i],
                                        points[i + 1])
            effective_areas.append(area)
        effective_areas.append(float('inf'))  # Last point has infinite area

        # Create a list of point indices
        point_indices = list(range(len(points)))

        # Loop until the desired number of points is reached
        while True:
            # Find the point with the smallest area
            min_area = min(
                effective_areas[1:-1])  # Exclude first and last point
            min_index = effective_areas.index(min_area)

            # Check stopping conditions
            if num_points is not None and len(points) <= num_points:
                break
            if threshold is not None and min_area >= threshold:
                break

            # Remove the point with the smallest area
            del points[min_index]
            del effective_areas[min_index]

            # Recalculate areas for affected points
            if 1 <= min_index - 1 < len(points) - 1:
                effective_areas[min_index - 1] = utils.calculate_area(
                    points[min_index - 2], points[min_index - 1],
                    points[min_index])
            if 1 <= min_index < len(points) - 1:
                effective_areas[min_index] = utils.calculate_area(
                    points[min_index - 1], points[min_index],
                    points[min_index + 1])

        return points
