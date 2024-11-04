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


@njit
def _prune_points_arc_length_numba(points_array, min_arc_length):
    n = len(points_array)
    pruned_points = np.empty((n, 2), dtype=np.float64)
    pruned_points[0] = points_array[0]  # Start with the first point
    accumulated_length = 0.0
    last_kept_index = 0  # Index of the last kept point
    pruned_count = 1  # Track the number of pruned points

    for i in range(1, n):
        dist = np.linalg.norm(points_array[i] - pruned_points[last_kept_index])
        accumulated_length += dist
        if accumulated_length >= min_arc_length:
            pruned_points[pruned_count] = points_array[i]
            accumulated_length = 0.0
            last_kept_index = pruned_count  # Update the index of the last kept point
            pruned_count += 1

    return pruned_points[:
                         pruned_count]  # Return only the filled portion of pruned_points


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
        max_distance: Optional[float] = None,
        min_distance: Optional[float] = None,
        num_points: Optional[int] = None,
        image: Optional[np.ndarray] = None,
        contours: Optional[List[np.ndarray]] = None,
        debug: bool = False,
    ):
        """
        Initializes the DotsSelection instance with the given parameters.
        """
        self.max_distance = max_distance
        self.min_distance = min_distance
        self.num_points = num_points
        self.image = image
        self.contours = contours
        self.debug = debug
        self.sample_start = 0.0005
        self.sample_end = 0.05
        self.nbr_sample = 10
        self.multi_objective_param = [1, 1]  # [alpha, beta]

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
        if self.contours is None:
            raise ValueError(
                "Contours must be set before calling contour_to_linear_paths.")

        dominant_points_list = []

        for contour in self.contours:

            # Ensure clockwise direction
            area = cv2.contourArea(contour, oriented=True)
            if area < 0:
                contour = contour[::-1]

            # Convert to (x, y) tuples
            points = [(point[0][0], point[0][1]) for point in contour]

            # Calculate total arc length
            total_arc_length = self._calculate_arc_length(points)

            # Optimize sample size
            best_sample = self._optimize_multi_objective(
                points, total_arc_length, curvature_method)
            print(f"Sample the curve by a sample of {best_sample}...")

            # Prune points based on arc length
            pruned_points = self._prune_points_arc_length(
                points, total_arc_length * best_sample)

            # Calculate curvature
            curvature = self._calculate_curvature(curvature_method,
                                                  pruned_points)

            # Select high-curvature points
            high_curvature_points, high_curvature_indices = self._select_high_curvature(
                pruned_points, curvature, threshold=0.4)

            # Optional debugging plots
            if self.debug:
                self.plot_curvature(pruned_points,
                                    curvature,
                                    title='Contour Colored by Curvature')
                self._plot_high_curvature_points(pruned_points,
                                                 high_curvature_points)

            # Insert midpoints if needed
            if self.max_distance is not None:
                pruned_points = self.insert_midpoints(pruned_points,
                                                      self.max_distance,
                                                      high_curvature_indices)

            # Filter close points if needed
            if self.min_distance is not None:
                pruned_points = self.filter_close_points(
                    pruned_points, self.min_distance, high_curvature_indices)

            # Simplify path if needed
            if self.num_points is not None:
                pruned_points = self.visvalingam_whyatt(
                    pruned_points,
                    num_points=self.num_points,
                    high_curvature_indices=high_curvature_indices)

            dominant_points_list.append(pruned_points)

        return dominant_points_list

    def _optimize_multi_objective(
        self,
        points: List[Tuple[int, int]],
        total_arc_length: float,
        curvature_method: CurvatureMethod = CurvatureMethod.TURNING_ANGLE
    ) -> float:
        """Optimizes the sample size factor 's' based on a multi-objective function."""

        alpha, beta = self.multi_objective_param
        samples = np.logspace(np.log10(self.sample_start),
                              np.log10(self.sample_end), self.nbr_sample)

        # Helper function to compute f(s) using optimized calculations
        def compute_f(s):
            pruned_points = self._prune_points_arc_length(
                points, total_arc_length * s)
            curvature = self._calculate_curvature(curvature_method,
                                                  pruned_points)
            high_curvature_points, _ = self._select_high_curvature(
                pruned_points, curvature, threshold=0.4)
            variance_distance = self._calculate_variance_distance(
                high_curvature_points)
            a_s = alpha * len(high_curvature_points)
            b_s = beta * variance_distance
            return a_s / b_s if b_s != 0 else float('inf')

        # Use parallel processing for each sample calculation
        with ThreadPoolExecutor() as executor:
            f_values = list(executor.map(compute_f, samples))

        # Find the best sample based on minimum f(s)
        min_f_idx = np.argmin(f_values)
        best_sample = samples[min_f_idx]

        # Optionally, plot the f(s) values if in debug mode
        if self.debug:
            self._plot_multi_objective_function(samples, f_values)

        return best_sample

    def _calculate_curvature(self, curvature_method: CurvatureMethod,
                             points: List[Tuple[int, int]]) -> List[float]:
        """Calculate curvature using vectorized operations for efficiency."""

        points_array = np.array(points)
        v1 = points_array[1:-1] - points_array[:-2]
        v2 = points_array[2:] - points_array[1:-1]

        cross_products = np.cross(v1, v2)
        dot_products = np.einsum('ij,ij->i', v1, v2)

        angles = np.arctan2(cross_products, dot_products)

        if curvature_method == CurvatureMethod.TURNING_ANGLE:
            kappa = np.abs(angles)
        elif curvature_method == CurvatureMethod.LENGTH_VARIATION:
            kappa = 2 * np.sin(np.abs(angles) / 2)
        elif curvature_method == CurvatureMethod.STEINER_FORMULA:
            kappa = 2 * np.tan(np.abs(angles) / 2)
        elif curvature_method == CurvatureMethod.OSCULATING_CIRCLE:
            a = np.linalg.norm(v2, axis=1)
            b = np.linalg.norm(v1, axis=1)
            s = (a + b) / 2
            area = np.sqrt(s * (s - a) * (s - b))
            radius = (a * b) / (2 * area)
            kappa = 1 / radius
        else:
            raise ValueError("Unsupported curvature method.")

        return [0] + list(kappa) + [0]

    # --- High Curvature Point Selection ---

    def _select_high_curvature(
            self, pruned_points: List[Tuple[int, int]], curvature: List[float],
            threshold: float) -> Tuple[List[Tuple[int, int]], List[int]]:
        """
        Selects points with curvature above a certain threshold and removes consecutive points,
        keeping only the one with the highest curvature in each consecutive sequence.

        Args:
            pruned_points (List[Tuple[int, int]]): Pruned list of (x, y) points.
            curvature (List[float]): Curvature values corresponding to each point.
            threshold (float): Minimum curvature value to consider a point as high-curvature.

        Returns:
            Tuple[List[Tuple[int, int]], List[int]]: 
                - Filtered list of high-curvature points.
                - Corresponding list of indices in pruned_points.
        """
        curvature = np.array(curvature)
        high_curvature_indices = np.where(curvature > threshold)[0]

        # Group consecutive indices
        if high_curvature_indices.size == 0:
            return [], []

        # Use NumPy's split and where functions to group consecutive indices
        splits = np.where(np.diff(high_curvature_indices) != 1)[0] + 1
        groups = np.split(high_curvature_indices, splits)

        selected_indices = []
        for group in groups:
            idx = group[np.argmax(curvature[group])]
            selected_indices.append(idx)

        selected_points = [pruned_points[idx] for idx in selected_indices]
        return selected_points, selected_indices

    def _calculate_variance_distance(
            self, selected_points: List[Tuple[int, int]]) -> float:
        """Calculate variance in distances with optimized vectorized operations."""

        if len(selected_points) < 2:
            return 0.0

        points_array = np.array(selected_points)
        distances = np.sqrt(np.sum(np.diff(points_array, axis=0)**2, axis=1))

        return np.var(distances)

    # --- Plotting Methods ---

    def plot_curvature(self,
                       points: List[Tuple[int, int]],
                       curvature: List[float],
                       title: str = 'Contour Colored by Curvature') -> None:
        """
        Plots the curvature along the contour.

        Args:
            points (List[Tuple[int, int]]): List of (x, y) points.
            curvature (List[float]): Curvature values corresponding to each point.
            title (str): Title of the plot.
        """
        if len(points) != len(curvature):
            raise ValueError(
                "Length of points and curvature must be the same.")

        points = np.array(points)
        curvature = np.array(curvature)
        segments = np.stack([points[:-1], points[1:]], axis=1)
        avg_curvature = (curvature[:-1] + curvature[1:]) / 2
        norm = plt.Normalize(avg_curvature.min(), avg_curvature.max())

        lc = LineCollection(segments, cmap='viridis', norm=norm)
        lc.set_array(avg_curvature)
        lc.set_linewidth(2)

        plt.figure(figsize=(8, 6))
        plt.gca().add_collection(lc)
        plt.colorbar(lc, label='Curvature')
        plt.scatter(points[:, 0],
                    points[:, 1],
                    c=curvature,
                    cmap='viridis',
                    s=10)
        plt.title(title)
        plt.xlabel('X-coordinate')
        plt.ylabel('Y-coordinate')
        plt.gca().invert_yaxis()
        plt.axis('equal')
        # plt.show()

    def _plot_multi_objective_function(self, s_values, f_values):
        plt.figure(figsize=(8, 6))
        plt.plot(s_values,
                 f_values,
                 marker='o',
                 linestyle='-',
                 color='b',
                 label="f(s)")
        plt.xscale('log')
        plt.xlabel('Sample Size Factor (s)')
        plt.ylabel('Objective Function f(s)')
        plt.legend()
        plt.title('Multi-objective Optimization of f(s)')
        plt.grid(True)
        # plt.show()

    def _plot_high_curvature_points(
            self, pruned_points: List[Tuple[int, int]],
            high_curvature_points: List[Tuple[int, int]]) -> None:
        """
        Plot the pruned contour points and highlight the points where curvature is above the threshold,
        using the output from _select_high_curvature.

        Args:
            pruned_points (List[Tuple[int, int]]): Pruned list of (x, y) points.
            high_curvature_points (List[Tuple[int, int]]): List of (x, y) points that have high curvature.
        """
        # Convert pruned points to numpy array for easier plotting
        points = np.array(pruned_points)

        # Plot the contour
        plt.figure(figsize=(8, 6))
        plt.plot(points[:, 0],
                 points[:, 1],
                 'k--',
                 alpha=0.5,
                 label='Pruned Contour')

        # Convert high curvature points to numpy array for plotting
        if high_curvature_points:
            high_curvature_points = np.array(high_curvature_points)
            # Highlight high-curvature points
            plt.scatter(high_curvature_points[:, 0],
                        high_curvature_points[:, 1],
                        c='red',
                        s=50,
                        marker='x',
                        label='High Curvature Points')

        plt.title('Contour with High Curvature Points')
        plt.xlabel('X-coordinate')
        plt.ylabel('Y-coordinate')
        plt.legend()
        plt.gca().invert_yaxis()  # Invert y-axis to match image coordinates
        plt.axis('equal')  # Ensure equal scaling
        # plt.show()

    # --- Utility Methods ---

    def _calculate_arc_length(self, points: List[Tuple[int, int]]) -> float:
        """
        Calculate the total arc length of a series of points.

        Args:
            points (List[Tuple[int, int]]): List of (x, y) points.

        Returns:
            float: Total arc length.
        """
        points_array = np.array(points)
        deltas = np.diff(points_array, axis=0)
        distances = np.hypot(deltas[:, 0], deltas[:, 1])
        arc_length = np.sum(distances)
        return arc_length

    def _prune_points_arc_length(
            self, points: List[Tuple[int, int]],
            min_arc_length: float) -> List[Tuple[int, int]]:
        points_array = np.array(points, dtype=np.float64)
        pruned_points_array = _prune_points_arc_length_numba(
            points_array, min_arc_length)
        return [tuple(point) for point in pruned_points_array]

    def insert_midpoints(
            self, points: List[Tuple[int, int]], max_distance: float,
            high_curvature_indices: List[int]) -> List[Tuple[int, int]]:
        """
        Inserts midpoints between consecutive points if the distance between them exceeds max_distance.
        Ensures that points remain in sequential order after midpoint insertion and preserves high-curvature points.

        Args:
            points (List[Tuple[int, int]]): List of (x, y) points.
            max_distance (float): Maximum allowable distance between consecutive points.
            high_curvature_indices (List[int]): List of indices in 'points' that are high-curvature points.

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

    def filter_close_points(
            self, points: List[Tuple[int, int]], min_distance: float,
            high_curvature_indices: List[int]) -> List[Tuple[int, int]]:
        """
        Removes points that are closer than min_distance.
        Always keeps the first, last, and high-curvature points.
        Additionally, if there are 2 or more consecutive high-curvature points that are closer than min_distance,
        only the first one in the group is added to filtered_points.

        Args:
            points (List[Tuple[int, int]]): List of (x, y) points.
            min_distance (float): Minimum allowable distance between points.
            high_curvature_indices (List[int]): List of indices in 'points' that are high-curvature points.

        Returns:
            List[Tuple[int, int]]: Filtered list of points.
        """
        if len(points) < 2:
            return points  # Not enough points to filter

        filtered_points = [points[0]]  # Keep the first point
        last_kept_point = points[0]
        last_high_curv_point = None

        # Convert list to set for faster lookup
        high_curv_set = set(high_curvature_indices)

        for i in range(1, len(points) - 1):
            current_point = points[i]
            if i in high_curv_set:
                if last_high_curv_point is not None:
                    dist = utils.point_distance(last_high_curv_point,
                                                current_point)
                    if dist < min_distance:
                        # Skip adding this high curvature point to avoid clustering
                        continue
                # Add current high curvature point
                filtered_points.append(current_point)
                last_kept_point = current_point
                last_high_curv_point = current_point
            else:
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
        threshold: Optional[float] = None,
        high_curvature_indices: Optional[List[int]] = None
    ) -> List[Tuple[int, int]]:
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
            if high_curvature_indices and i in high_curvature_indices:
                area = float('inf')  # Preserve high-curvature points
            else:
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

            # If the point to remove is a high-curvature point, skip it
            if high_curvature_indices and (min_index
                                           in high_curvature_indices):
                # Assign a large area to prevent removal
                effective_areas[min_index] = float('inf')
                # Continue to next point
                if len(effective_areas) > min_index + 1:
                    # To avoid infinite loop, ensure there's a next point
                    continue
                else:
                    break

            # Remove the point with the smallest area
            del points[min_index]
            del effective_areas[min_index]

            # Recalculate areas for affected points
            if 1 <= min_index - 1 < len(points) - 1:
                if high_curvature_indices and (min_index - 1
                                               in high_curvature_indices):
                    effective_areas[min_index - 1] = float('inf')
                else:
                    effective_areas[min_index - 1] = utils.calculate_area(
                        points[min_index - 2], points[min_index - 1],
                        points[min_index])
            if 1 <= min_index < len(points) - 1:
                if high_curvature_indices and (min_index
                                               in high_curvature_indices):
                    effective_areas[min_index] = float('inf')
                else:
                    effective_areas[min_index] = utils.calculate_area(
                        points[min_index - 1], points[min_index],
                        points[min_index + 1])

        return points
