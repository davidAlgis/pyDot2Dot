# dots_selection.py

import cv2
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
import utils
from typing import List, Tuple, Optional
from enum import Enum


class CurvatureMethod(Enum):
    TURNING_ANGLE = 1
    LENGTH_VARIATION = 2
    STEINER_FORMULA = 3
    OSCULATING_CIRCLE = 4


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

    def plot_different_curvature(self):
        if self.contours is None:
            raise ValueError(
                "Contours must be set before calling contour_to_linear_paths.")

        dominant_points_list = []

        for contour in self.contours:
            # Define the start, end, and number of samples
            start = 0.0005
            end = 0.5
            N = 10  # Number of samples

            # Generate the logarithmically spaced samples
            samples = np.logspace(np.log10(start), np.log10(end), N)
            for s in samples:
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
                    points, total_arc_length * s)

                turning_angle_curvature = self.turning_angle_curvature(
                    pruned_points)
                self.plot_curvature(pruned_points, turning_angle_curvature,
                                    f"Turning Angle Curvature {s}")

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

            # Prune points based on a fraction of the total arc length
            pruned_points = self._prune_points_arc_length(
                points, total_arc_length * 0.0025)

            # Calculate curvature based on the selected method
            if curvature_method == CurvatureMethod.TURNING_ANGLE:
                curvature = self.turning_angle_curvature(pruned_points)
            elif curvature_method == CurvatureMethod.LENGTH_VARIATION:
                curvature = self.length_variation_curvature(pruned_points)
            elif curvature_method == CurvatureMethod.STEINER_FORMULA:
                curvature = self.steiner_formula_curvature(pruned_points)
            elif curvature_method == CurvatureMethod.OSCULATING_CIRCLE:
                curvature = self.osculating_circle_curvature(pruned_points)
            else:
                raise ValueError("Unsupported curvature method selected.")

            # Calculate derivative of curvature
            derivative_curvature = self._calculate_derivative_curvature(
                curvature)

            high_curvature_points = self._select_high_curvature(pruned_points,
                                                                curvature,
                                                                threshold=0.4)

            # Plot curvature if debug mode is enabled
            if self.debug:
                self._plot_curvature(pruned_points, curvature)
                # self._plot_pruned_points(pruned_points)
                # self._plot_derivative_curvature(pruned_points,
                # derivative_curvature)
                # self._plot_signed_changed_derivative_curvature(
                # pruned_points, derivative_curvature, threshold=0.05)
                self._plot_high_curvature_points(pruned_points,
                                                 high_curvature_points)
                # self.plot_all_curvatures(pruned_points)

            # Insert midpoints and filter close points if needed
            if self.max_distance is not None:
                pruned_points = self.insert_midpoints(pruned_points,
                                                      self.max_distance)

            if self.min_distance is not None:
                pruned_points = self.filter_close_points(
                    pruned_points, self.min_distance)

            if self.num_points is not None:
                pruned_points = self.visvalingam_whyatt(
                    pruned_points, num_points=self.num_points)

            dominant_points_list.append(pruned_points)

        return dominant_points_list

    def _select_high_curvature(self, pruned_points: List[Tuple[int, int]],
                               curvature: List[float],
                               threshold: float) -> List[Tuple[int, int]]:
        """
        Selects points with curvature above a certain threshold and removes consecutive points,
        keeping only the one with the highest curvature in each consecutive sequence.

        Args:
            pruned_points (List[Tuple[int, int]]): Pruned list of (x, y) points.
            curvature (List[float]): Curvature values corresponding to each point.
            threshold (float): Minimum curvature value to consider a point as high-curvature.

        Returns:
            List[Tuple[int, int]]: Filtered list of high-curvature points.
        """
        if len(pruned_points) != len(curvature):
            raise ValueError(
                "Length of pruned_points and curvature must be the same.")
        curvature = np.array(curvature)
        # Find indices where curvature exceeds the threshold
        high_curvature_indices = np.where(curvature > threshold)[0]

        # Store selected high-curvature points
        selected_points = []

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

            # Move to the next potential group
            i += 1

        return selected_points

    def calculate_mean_distance(
            self, selected_points: List[Tuple[int, int]]) -> float:
        """
        Calculate the mean distance between each consecutive pair of points in the selected high-curvature points.

        Args:
            selected_points (List[Tuple[int, int]]): List of (x, y) points with high curvature.

        Returns:
            float: The mean distance between consecutive high-curvature points.
        """
        if len(selected_points) < 2:
            raise ValueError(
                "At least two points are required to calculate mean distance.")

        # Calculate distances between each consecutive pair of points
        distances = [
            np.linalg.norm(
                np.array(selected_points[i]) -
                np.array(selected_points[i + 1]))
            for i in range(len(selected_points) - 1)
        ]

        # Return the mean of these distances
        mean_distance = np.var(distances)
        return mean_distance

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

    def _calculate_derivative_curvature(self,
                                        curvature: List[float]) -> List[float]:
        """
        Calculate the derivative of curvature using central differences.

        Args:
            curvature (List[float]): List of curvature values.

        Returns:
            List[float]: Derivative of curvature values.
        """
        derivative = [0]  # Derivative at the first point is set to 0

        for i in range(1, len(curvature) - 1):
            dc = curvature[i + 1] - curvature[i - 1]
            derivative.append(dc / 2.0)

        derivative.append(0)  # Derivative at the last point is set to 0

        return derivative

    def _plot_curvature(self, pruned_points: List[Tuple[int, int]],
                        curvature: List[float]) -> None:
        """
        Plot the pruned contour points with a color gradient representing curvature.

        Args:
            pruned_points (List[Tuple[int, int]]): Pruned list of (x, y) points.
            curvature (List[float]): Curvature values corresponding to each point.
        """
        if len(pruned_points) != len(curvature):
            raise ValueError(
                "Length of pruned_points and curvature must be the same.")

        # Convert points to numpy array for easier manipulation
        points = np.array(pruned_points)
        curvature = np.array(curvature)

        # Create segments between consecutive points
        segments = np.stack([points[:-1], points[1:]], axis=1)

        # Compute average curvature for each segment
        avg_curvature = (curvature[:-1] + curvature[1:]) / 2

        # Normalize curvature for colormap
        norm = plt.Normalize(avg_curvature.min(), avg_curvature.max())

        # Create a LineCollection with the segments colored by curvature
        lc = LineCollection(segments, cmap='viridis', norm=norm)
        lc.set_array(avg_curvature)
        lc.set_linewidth(2)

        plt.figure(figsize=(8, 6))
        plt.gca().add_collection(lc)
        plt.colorbar(lc, label='Curvature')

        # Optionally, plot the points as well
        plt.scatter(points[:, 0],
                    points[:, 1],
                    c=curvature,
                    cmap='viridis',
                    s=10)

        plt.title('Contour Colored by Curvature')
        plt.xlabel('X-coordinate')
        plt.ylabel('Y-coordinate')
        plt.gca().invert_yaxis()  # Invert y-axis to match image coordinates
        plt.axis('equal')  # Ensure equal scaling
        # plt.show()

    def _plot_derivative_curvature(self, pruned_points: List[Tuple[int, int]],
                                   derivative_curvature: List[float]) -> None:
        """
        Plot the pruned contour points with a color gradient representing the derivative of curvature.

        Args:
            pruned_points (List[Tuple[int, int]]): Pruned list of (x, y) points.
            derivative_curvature (List[float]): Derivative of curvature values corresponding to each point.
        """
        if len(pruned_points) != len(derivative_curvature):
            raise ValueError(
                "Length of pruned_points and derivative_curvature must be the same."
            )

        # Convert points to numpy array for easier manipulation
        points = np.array(pruned_points)
        derivative_curvature = np.array(derivative_curvature)

        # Create segments between consecutive points
        segments = np.stack([points[:-1], points[1:]], axis=1)

        # Compute average derivative of curvature for each segment
        avg_derivative = (derivative_curvature[:-1] +
                          derivative_curvature[1:]) / 2

        # Normalize derivative curvature for colormap
        norm = plt.Normalize(avg_derivative.min(), avg_derivative.max())

        # Create a LineCollection with the segments colored by derivative curvature
        lc = LineCollection(segments, cmap='coolwarm', norm=norm)
        lc.set_array(avg_derivative)
        lc.set_linewidth(2)

        plt.figure(figsize=(8, 6))
        plt.gca().add_collection(lc)
        plt.colorbar(lc, label='Derivative of Curvature')

        # Optionally, plot the points as well
        plt.scatter(points[:, 0],
                    points[:, 1],
                    c=derivative_curvature,
                    cmap='coolwarm',
                    s=10)

        plt.title('Contour Colored by Derivative of Curvature')
        plt.xlabel('X-coordinate')
        plt.ylabel('Y-coordinate')
        plt.gca().invert_yaxis()  # Invert y-axis to match image coordinates
        plt.axis('equal')  # Ensure equal scaling
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
        # plt.show()  # Uncomment this line to display the plot

    def _plot_signed_changed_derivative_curvature(
            self,
            pruned_points: List[Tuple[int, int]],
            derivative_curvature: List[float],
            threshold: float = 1e-5) -> None:
        """
        Plot the pruned contour points and highlight points where the derivative of curvature changes sign
        beyond a specified threshold.

        Args:
            pruned_points (List[Tuple[int, int]]): Pruned list of (x, y) points.
            derivative_curvature (List[float]): Derivative of curvature values corresponding to each point.
            threshold (float): Minimum absolute value of derivative to consider a sign change significant.
        """
        if len(pruned_points) != len(derivative_curvature):
            raise ValueError(
                "Length of pruned_points and derivative_curvature must be the same."
            )

        # Convert lists to numpy arrays for easier manipulation
        points = np.array(pruned_points)
        derivative_curvature = np.array(derivative_curvature)

        # Initialize a list to hold indices where sign changes occur
        sign_change_indices = []

        # Iterate through derivative_curvature to find sign changes
        for i in range(1, len(derivative_curvature)):
            prev = derivative_curvature[i - 1]
            current = derivative_curvature[i]
            # Check for sign change
            if (prev * current) < 0:
                # Check if the change is significant
                if abs(prev) >= threshold and abs(current) >= threshold:
                    sign_change_indices.append(i)

        # Extract the points where sign changes occur
        sign_change_points = points[sign_change_indices]

        # Plot the contour
        plt.figure(figsize=(8, 6))
        plt.plot(points[:, 0],
                 points[:, 1],
                 'k--',
                 alpha=0.5,
                 label='Pruned Contour')

        # Highlight the sign change points
        if sign_change_points.size > 0:
            plt.scatter(sign_change_points[:, 0],
                        sign_change_points[:, 1],
                        c='red',
                        s=50,
                        marker='x',
                        label='Sign Change Points')

        plt.title(
            'Contour with Significant Derivative of Curvature Sign Changes')
        plt.xlabel('X-coordinate')
        plt.ylabel('Y-coordinate')
        plt.legend()
        plt.gca().invert_yaxis()  # Invert y-axis to match image coordinates
        plt.axis('equal')  # Ensure equal scaling
        # plt.show()

    def _plot_pruned_points(self, pruned_points: List[Tuple[int,
                                                            int]]) -> None:
        """
        Plot the pruned points on a Matplotlib figure.

        Args:
            pruned_points (List[Tuple[int, int]]): List of pruned (x, y) points.
        """
        # Convert points to numpy array for easier manipulation
        points = np.array(pruned_points)

        plt.figure(figsize=(8, 6))
        plt.plot(points[:, 0],
                 points[:, 1],
                 'o',
                 markersize=5,
                 color='blue',
                 label='Pruned Points')

        plt.title('Pruned Points')
        plt.xlabel('X-coordinate')
        plt.ylabel('Y-coordinate')
        plt.gca().invert_yaxis()  # Invert y-axis to match image coordinates
        plt.axis('equal')  # Ensure equal scaling
        plt.legend()
        # plt.show()  # Uncomment this line if you want to display the plot in an interactive environment

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

    def insert_midpoints(self, points, max_distance):
        """
        Inserts midpoints between consecutive points if the distance between them exceeds max_distance.
        Ensures that points remain in sequential order after midpoint insertion.

        Args:
            points (List[Tuple[int, int]]): List of (x, y) points.
            max_distance (float): Maximum allowable distance between consecutive points.

        Returns:
            List[Tuple[int, int]]: Refined list of points with inserted midpoints.
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

        Args:
            points (List[Tuple[int, int]]): List of (x, y) points.
            min_distance (float): Minimum allowable distance between points.

        Returns:
            List[Tuple[int, int]]: Filtered list of points.
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

        Args:
            points (List[Tuple[int, int]]): List of (x, y) points.
            num_points (Optional[int]): Desired number of points after simplification.
            threshold (Optional[float]): Area threshold to stop simplification.

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
            area = np.sqrt(s * (s - a) * (s - b) * (s - c))
            radius = (a * b * c) / (4 * area) if area != 0 else float('inf')
            kappa.append(1 / radius if radius != float('inf') else 0)
        return [0] + kappa + [0]

    def plot_curvature(self, points: List[Tuple[int, int]],
                       curvature: List[float], title: str) -> None:
        """Plots the curvature along the contour."""
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

    # Example usage for each curvature calculation:
    def plot_all_curvatures(self, points: List[Tuple[int, int]]) -> None:
        """Plots all curvature methods for comparison."""
        turning_angle_curvature = self.turning_angle_curvature(points)
        self.plot_curvature(points, turning_angle_curvature,
                            "Turning Angle Curvature")

        length_variation_curvature = self.length_variation_curvature(points)
        self.plot_curvature(points, length_variation_curvature,
                            "Length Variation Curvature")

        steiner_formula_curvature = self.steiner_formula_curvature(points)
        self.plot_curvature(points, steiner_formula_curvature,
                            "Steiner Formula Curvature")

        osculating_circle_curvature = self.osculating_circle_curvature(points)
        self.plot_curvature(points, osculating_circle_curvature,
                            "Osculating Circle Curvature")
