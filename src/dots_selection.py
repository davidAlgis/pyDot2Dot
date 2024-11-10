# dots_selection.py

import cv2
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from typing import List, Tuple, Optional
from enum import Enum
import utils
from concurrent.futures import ThreadPoolExecutor
from numba import njit


class CurvatureMethod(Enum):
    TURNING_ANGLE = 1
    LENGTH_VARIATION = 2
    STEINER_FORMULA = 3
    OSCULATING_CIRCLE = 4


class DotsSelection:
    """
    A class to handle the selection and processing of dots from image contours.

    Attributes:
        max_distance (Optional[float]): Maximum distance to insert midpoints.
        min_distance (Optional[float]): Minimum distance to filter close points.
        num_points (Optional[int]): Number of points to simplify the path.
        image (Optional[np.ndarray]): The image being processed.
        contours (Optional[List[np.ndarray]]): List of contours extracted from the image.
        debug (bool): Flag to enable or disable debug mode.
        sample_start (float): Starting sample factor for optimization.
        sample_end (float): Ending sample factor for optimization.
        nbr_sample (int): Number of samples for optimization.
        multi_objective_param (List[float]): Parameters [alpha, beta] for the multi-objective function.
    """

    def __init__(
        self,
        epsilon_factor: float = 0.001,
        max_distance: Optional[float] = None,
        min_distance: Optional[float] = None,
        num_points: Optional[int] = None,
        image: Optional[np.ndarray] = None,
        contour: Optional[np.ndarray] = None,
        debug: bool = False,
    ):
        """
        Initializes the DotsSelection instance with the given parameters.
        """
        self.epsilon_factor = epsilon_factor
        self.max_distance = max_distance
        self.min_distance = min_distance
        self.num_points = num_points
        self.image = image
        self.contour = contour
        self.debug = debug
        if (self.debug):
            points = [(point[0][0], point[0][1]) for point in self.contour]
            self._plot_points_before_treatment(points)

    def contour_to_linear_paths(
        self,
        curvature_method: CurvatureMethod = CurvatureMethod.TURNING_ANGLE
    ) -> List[List[Tuple[int, int]]]:
        """
        Converts each contour into a sequence of dominant points with optional pruning and curvature analysis.

        Args:
            curvature_method (CurvatureMethod): The method to use for curvature calculation. Default is TURNING_ANGLE.

        Returns:
            List[List[Tuple[int, int]]]: A list of linear paths, each represented as a list of (x, y) tuples.
        """
        if self.contour is None:
            raise ValueError(
                "Contours must be set before calling contour_to_linear_paths.")

        dominant_points_list = []

        # Ensure clockwise direction
        area = cv2.contourArea(self.contour, oriented=True)
        if area < 0:
            self.contour = self.contour[::-1]

        # Convert to (x, y) tuples
        points = [(point[0][0], point[0][1]) for point in self.contour]

        approx = cv2.approxPolyDP(np.array(points, dtype=np.int32),
                                  self.epsilon_factor, True)

        # Ensure clockwise direction using OpenCV's oriented area
        area = cv2.contourArea(approx, oriented=True)
        if area < 0:
            approx = approx[::-1]

        # Convert to a list of (x, y) tuples
        points = [(point[0][0], point[0][1]) for point in approx]

        # Insert midpoints if needed
        if self.max_distance is not None:
            points = self.insert_midpoints(points, self.max_distance)

        # Filter close points if needed
        if self.min_distance is not None:
            points = self.filter_close_points(points, self.min_distance)
        # Simplify path if needed
        if self.num_points is not None:
            points = self.visvalingam_whyatt(points,
                                             num_points=self.num_points)

        dominant_points_list.append(points)

        return dominant_points_list

    # --- Utility Methods ---

    def insert_midpoints(self, points: List[Tuple[int, int]],
                         max_distance: float) -> List[Tuple[int, int]]:
        """
        Inserts midpoints between consecutive points if the distance between them exceeds max_distance.
        Ensures that points remain in sequential order after midpoint insertion

        Args:
            points (List[Tuple[int, int]]): List of (x, y) points.
            max_distance (float): Maximum allowable distance between consecutive points.

        Returns:
            List[Tuple[int, int]]: Refined list of points with inserted midpoints.
        """
        points_array = np.array(points)
        deltas = np.diff(points_array, axis=0)
        distances = np.hypot(deltas[:, 0], deltas[:, 1])
        num_midpoints = (distances // max_distance).astype(int)

        refined_points = [points[0]]
        for i in range(len(points_array) - 1):
            n_mid = num_midpoints[i]
            if n_mid > 0:
                t_values = np.linspace(0, 1, n_mid + 2)[1:-1]
                midpoints = (1 - t_values[:, np.newaxis]) * points_array[
                    i] + t_values[:, np.newaxis] * points_array[i + 1]
                refined_points.extend(midpoints.tolist())
            refined_points.append(points[i + 1])

        return refined_points

    def filter_close_points(self, points: List[Tuple[int, int]],
                            min_distance: float) -> List[Tuple[int, int]]:
        """
        Removes points that are closer than min_distance.
        Always keeps the first, last

        Args:
            points (List[Tuple[int, int]]): List of (x, y) points.
            min_distance (float): Minimum allowable distance between points.

        Returns:
            List[Tuple[int, int]]: Filtered list of points.
        """
        if len(points) < 2:
            return points  # Not enough points to filter

        filtered_points = [points[0]]  # Keep the first point
        last_kept_point = points[0]

        for i in range(1, len(points) - 1):
            current_point = points[i]
            dist = utils.point_distance(last_kept_point, current_point)
            if dist >= min_distance:
                filtered_points.append(current_point)
                last_kept_point = current_point

        filtered_points.append(points[-1])  # Keep the last point
        return filtered_points

    def visvalingam_whyatt(
            self,
            points: List[Tuple[int, int]],
            num_points: Optional[int] = None,
            threshold: Optional[float] = None) -> List[Tuple[int, int]]:
        """
        Simplify a path using the Visvalingam–Whyatt algorithm while preserving high-curvature points.

        Args:
            points (List[Tuple[int, int]]): List of (x, y) points.
            num_points (Optional[int]): Desired number of points after simplification.
            threshold (Optional[float]): Area threshold to stop simplification.
            high_curvature_indices (Optional[List[int]]): List of indices in 'points' that are high-curvature points.

        Returns:
            List[Tuple[int, int]]: Simplified list of points.
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

        # Loop until the desired number of points is reached
        while True:
            # Find the point with the smallest area (exclude first and last)
            min_area = min(effective_areas[1:-1])
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

    def _plot_points_before_treatment(self, points: List[Tuple[int,
                                                               int]]) -> None:
        """
        Plot the pruned contour points and highlight the points where curvature is above the threshold,
        using the output from _select_high_curvature.

        Args:
            points (List[Tuple[int, int]]): Pruned list of (x, y) points.
            high_curvature_points (List[Tuple[int, int]]): List of (x, y) points that have high curvature.
        """
        # Convert pruned points to numpy array for easier plotting
        points = np.array(points)

        # Plot the contour
        plt.figure(figsize=(8, 6))
        plt.plot(points[:, 0], points[:, 1], '.')

        plt.title('Points before any treatment')
        plt.xlabel('X-coordinate')
        plt.ylabel('Y-coordinate')
        plt.gca().invert_yaxis()  # Invert y-axis to match image coordinates
        # plt.show()