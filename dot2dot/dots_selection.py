# dots_selection.py

from typing import List, Tuple, Optional
import numpy as np
import cv2
from dot2dot.utils import point_distance, insert_midpoints, filter_close_points, calculate_area
from dot2dot.dot import Dot


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
        image: Optional[np.ndarray] = None,
        dots=[],
        debug: bool = False,
    ):
        """
        Initializes the DotsSelection instance with the given parameters.
        """
        self.epsilon_factor = epsilon_factor
        self.max_distance = max_distance
        self.min_distance = min_distance
        self.image = image
        self.dots = dots
        self.debug = debug

    def contour_to_linear_paths(self):
        if not self.dots or len(self.dots) < 3:
            raise ValueError(
                "Dots must be set and have at least 3 points to check orientation."
            )

        # Convert `self.dots` into a contour-compatible format
        contour = np.array([dot.position for dot in self.dots], dtype=np.int32)

        # Ensure contour has the correct shape (N, 2) for OpenCV
        if contour.ndim != 2 or contour.shape[1] != 2:
            raise ValueError(
                f"Invalid contour shape {contour.shape}. Expected shape (N, 2)."
            )

        # Ensure clockwise direction using OpenCV's contourArea
        area = cv2.contourArea(contour)

        if area < 0:
            # Reverse the order of `self.dots`
            self.dots = self.dots[::-1]

        # Convert to (x, y) tuples
        original_points = [dot.position for dot in self.dots]
        original_start_point = original_points[0]

        approx = cv2.approxPolyDP(np.array(original_points, dtype=np.int32),
                                  self.epsilon_factor, True)

        # Convert to a list of (x, y) tuples
        points = [(point[0][0], point[0][1]) for point in approx]

        # Reorder points to start from the point closest to the original start point
        distances = [point_distance(original_start_point, p) for p in points]
        min_index = distances.index(min(distances))
        points = points[min_index:] + points[:min_index]
        # Insert midpoints if needed
        if self.max_distance is not None:
            points = insert_midpoints(points, self.max_distance)
        # Filter close points if needed
        if self.min_distance is not None:
            points = filter_close_points(points, self.min_distance)

        # Update self.dots with new positions
        self.dots = [
            Dot(position=point, dot_id=idx + 1)
            for idx, point in enumerate(points)
        ]

        return self.dots

    # --- Utility Methods ---

    def _visvalingam_whyatt(
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
            area = calculate_area(points[i - 1], points[i], points[i + 1])
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
                effective_areas[min_index - 1] = calculate_area(
                    points[min_index - 2], points[min_index - 1],
                    points[min_index])
            if 1 <= min_index < len(points) - 1:
                effective_areas[min_index] = calculate_area(
                    points[min_index - 1], points[min_index],
                    points[min_index + 1])

        return points
