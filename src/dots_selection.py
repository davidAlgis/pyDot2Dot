# dots_selection.py

import cv2
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from typing import List, Tuple, Optional
from enum import Enum
import utils


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
            # Ensure clockwise direction using OpenCV's oriented area
            area = cv2.contourArea(contour, oriented=True)
            if area < 0:
                contour = contour[::-1]
            points = [(point[0][0], point[0][1]) for point in contour]

            # Calculate the total arc length of the contour
            total_arc_length = self._calculate_arc_length(points)

            # Optimize multi-objective to find the best sample size
            best_sample = self._optimize_multi_objective(curvature_method)
            print(f"Sample the curve by a sample of {best_sample}...")

            # Prune points based on the optimized sample size
            pruned_points = self._prune_points_arc_length(
                points, total_arc_length * best_sample)

            # Calculate curvature based on the selected method
            curvature = self._calculate_curvature(curvature_method,
                                                  pruned_points)

            # Select high curvature points and their indices
            high_curvature_points, high_curvature_indices = self._select_high_curvature(
                pruned_points, curvature, threshold=0.4)

            # Plot curvature if debug mode is enabled
            if self.debug:
                self.plot_curvature(pruned_points,
                                    curvature,
                                    title='Contour Colored by Curvature')
                self._plot_high_curvature_points(pruned_points,
                                                 high_curvature_points)

            # Insert midpoints and filter close points if needed, preserving high-curvature points
            if self.max_distance is not None:
                pruned_points = self.insert_midpoints(pruned_points,
                                                      self.max_distance,
                                                      high_curvature_indices)

            if self.min_distance is not None:
                pruned_points = self.filter_close_points(
                    pruned_points, self.min_distance, high_curvature_indices)

            if self.num_points is not None:
                pruned_points = self.visvalingam_whyatt(
                    pruned_points,
                    num_points=self.num_points,
                    high_curvature_indices=high_curvature_indices)

            dominant_points_list.append(pruned_points)

        return dominant_points_list

    def _optimize_multi_objective(
        self,
        curvature_method: CurvatureMethod = CurvatureMethod.TURNING_ANGLE
    ) -> float:
        """
        Optimizes the sample size factor 's' based on a multi-objective function.

        Args:
            curvature_method (CurvatureMethod): The method to use for curvature calculation.

        Returns:
            float: The best sample size factor 's'.
        """
        if self.contours is None:
            raise ValueError(
                "Contours must be set before calling _optimize_multi_objective."
            )

        alpha, beta = self.multi_objective_param

        # Generate the logarithmic spaced samples
        samples = np.logspace(np.log10(self.sample_start),
                              np.log10(self.sample_end), self.nbr_sample)

        # Lists to store the values of s and f(s) for plotting
        f_values = []
        s_values = []

        best_sample = self.sample_start
        min_f = float('inf')

        for contour in self.contours:
            # Ensure clockwise direction using OpenCV's oriented area
            area = cv2.contourArea(contour, oriented=True)
            if area < 0:
                contour = contour[::-1]
            # Convert the contour to a list of (x, y) tuples
            points = [(point[0][0], point[0][1]) for point in contour]

            # Calculate the total arc length of the contour
            total_arc_length = self._calculate_arc_length(points)

            for s in samples:
                # Prune points based on a fraction of the total arc length
                pruned_points = self._prune_points_arc_length(
                    points, total_arc_length * s)

                # Calculate curvature based on the selected method
                curvature = self._calculate_curvature(curvature_method,
                                                      pruned_points)

                # Select high curvature points and their indices
                high_curvature_points, _ = self._select_high_curvature(
                    pruned_points, curvature, threshold=0.4)

                variance_distance = self._calculate_variance_distance(
                    high_curvature_points)

                # Calculate f(s) and store it for plotting
                a_s = alpha * len(high_curvature_points)
                b_s = beta * variance_distance
                if b_s == 0:
                    f_s = float('inf')  # Avoid division by zero
                else:
                    f_s = a_s / b_s

                f_values.append(f_s)
                s_values.append(s)

                # Update the best sample based on the minimum f(s)
                if f_s < min_f:
                    best_sample = s
                    min_f = f_s

        # Plot f(s) as a function of s if in debug mode
        if self.debug:
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
            plt.show()

        return best_sample

    def _calculate_curvature(self, curvature_method: CurvatureMethod,
                             points: List[Tuple[int, int]]) -> List[float]:
        """
        Calculate curvature based on the selected curvature method.

        Args:
            curvature_method (CurvatureMethod): The method to use for curvature calculation.
            points (List[Tuple[int, int]]): List of (x, y) points.

        Returns:
            List[float]: Curvature values.
        """
        if curvature_method == CurvatureMethod.TURNING_ANGLE:
            return self.turning_angle_curvature(points)
        elif curvature_method == CurvatureMethod.LENGTH_VARIATION:
            return self.length_variation_curvature(points)
        elif curvature_method == CurvatureMethod.STEINER_FORMULA:
            return self.steiner_formula_curvature(points)
        elif curvature_method == CurvatureMethod.OSCULATING_CIRCLE:
            return self.osculating_circle_curvature(points)
        else:
            raise ValueError("Unsupported curvature method selected.")

    # --- Curvature Calculation Methods ---

    def turning_angle_curvature(self, points: List[Tuple[int,
                                                         int]]) -> List[float]:
        """Computes curvature using the turning angle method."""
        kappa = []
        for i in range(1, len(points) - 1):
            v1 = np.array(points[i]) - np.array(points[i - 1])
            v2 = np.array(points[i + 1]) - np.array(points[i])
            angle = np.arctan2(np.cross(v1, v2), np.dot(v1, v2))
            kappa.append(abs(angle))
        return [0] + kappa + [0]

    def length_variation_curvature(
            self, points: List[Tuple[int, int]]) -> List[float]:
        """Computes curvature using the length variation method."""
        kappa = []
        for i in range(1, len(points) - 1):
            v1 = np.array(points[i]) - np.array(points[i - 1])
            v2 = np.array(points[i + 1]) - np.array(points[i])
            angle = np.arctan2(np.cross(v1, v2), np.dot(v1, v2))
            curvature = 2 * np.sin(abs(angle) / 2)
            kappa.append(curvature)
        return [0] + kappa + [0]

    def steiner_formula_curvature(
            self, points: List[Tuple[int, int]]) -> List[float]:
        """Computes curvature using Steiner's formula."""
        kappa = []
        for i in range(1, len(points) - 1):
            v1 = np.array(points[i]) - np.array(points[i - 1])
            v2 = np.array(points[i + 1]) - np.array(points[i])
            angle = np.arctan2(np.cross(v1, v2), np.dot(v1, v2))
            curvature = 2 * np.tan(abs(angle) / 2)
            kappa.append(curvature)
        return [0] + kappa + [0]

    def osculating_circle_curvature(
            self, points: List[Tuple[int, int]]) -> List[float]:
        """Computes curvature using the osculating circle method."""
        kappa = []
        for i in range(1, len(points) - 1):
            p1, p2, p3 = np.array(points[i - 1]), np.array(
                points[i]), np.array(points[i + 1])
            a = np.linalg.norm(p2 - p3)
            b = np.linalg.norm(p1 - p3)
            c = np.linalg.norm(p1 - p2)
            s = (a + b + c) / 2
            area = np.sqrt(max(s * (s - a) * (s - b) * (s - c),
                               0))  # Ensure non-negative under sqrt
            if area == 0:
                radius = float('inf')
            else:
                radius = (a * b * c) / (4 * area)
            kappa.append(1 / radius if radius != float('inf') else 0)
        return [0] + kappa + [0]

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
        if len(pruned_points) != len(curvature):
            raise ValueError(
                "Length of pruned_points and curvature must be the same.")

        curvature = np.array(curvature)
        # Find indices where curvature exceeds the threshold
        high_curvature_indices = np.where(curvature > threshold)[0]

        # Store selected high-curvature points and their indices
        selected_points = []
        selected_indices = []

        i = 0
        while i < len(high_curvature_indices):
            # Start a new group of consecutive points
            current_group = [high_curvature_indices[i]]

            # Find all consecutive indices in this group
            while (i + 1 < len(high_curvature_indices)
                   and high_curvature_indices[i + 1]
                   == high_curvature_indices[i] + 1):
                current_group.append(high_curvature_indices[i + 1])
                i += 1

            # Select the point with the highest curvature within this group
            if current_group:
                max_curvature_index = max(current_group,
                                          key=lambda idx: curvature[idx])
                selected_points.append(pruned_points[max_curvature_index])
                selected_indices.append(max_curvature_index)

            # Move to the next potential group
            i += 1

        return selected_points, selected_indices

    def _calculate_variance_distance(
            self, selected_points: List[Tuple[int, int]]) -> float:
        """
        Calculate the variance of distances between each consecutive pair of points in the selected high-curvature points.

        Args:
            selected_points (List[Tuple[int, int]]): List of (x, y) points with high curvature.

        Returns:
            float: The variance of distances between consecutive high-curvature points.
        """
        if len(selected_points) < 2:
            return 0.0  # Variance is zero if less than two points

        # Calculate distances between each consecutive pair of points
        distances = [
            np.linalg.norm(
                np.array(selected_points[i]) -
                np.array(selected_points[i + 1]))
            for i in range(len(selected_points) - 1)
        ]

        # Return the variance of these distances
        variance_distance = np.var(distances)
        return variance_distance

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
        plt.show()

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
        plt.show()

    # --- Utility Methods ---

    def _calculate_arc_length(self, points: List[Tuple[int, int]]) -> float:
        """
        Calculate the total arc length of a series of points.

        Args:
            points (List[Tuple[int, int]]): List of (x, y) points.

        Returns:
            float: Total arc length.
        """
        arc_length = sum(
            np.linalg.norm(np.array(points[i]) - np.array(points[i - 1]))
            for i in range(1, len(points)))
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
        refined_points = []
        # Convert list to set for faster lookup
        high_curv_set = set(high_curvature_indices)

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
