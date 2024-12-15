"""
This module handles the discretization in points of the image. 
It takes as input an image and returns a set of points that will be transformed in dots.
"""

import numpy as np
import cv2
import cv2.ximgproc
from dot2dot.utils import resize_for_debug, display_with_opencv
from dot2dot.dot import Dot


def find_endpoints(skeleton):
    height, width = skeleton.shape
    endpoints = []
    for y in range(height):
        for x in range(width):
            if skeleton[y, x]:
                # Count the number of neighbor skeleton pixels
                count = 0
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        if dx == 0 and dy == 0:
                            continue
                        ny = y + dy
                        nx = x + dx
                        if 0 <= ny < height and 0 <= nx < width:
                            if skeleton[ny, nx]:
                                count += 1
                if count == 1:
                    endpoints.append((y, x))
    return np.array(endpoints)


def bfs_traversal(skeleton, start_y, start_x):
    height, width = skeleton.shape
    visited = np.zeros((height, width), dtype=np.bool_)
    distances = np.full((height, width), -1, dtype=np.int32)
    predecessors = np.full((height, width, 2), -1, dtype=np.int32)

    queue_y = np.empty(height * width, dtype=np.int32)
    queue_x = np.empty(height * width, dtype=np.int32)
    q_start = 0
    q_end = 0

    queue_y[q_end] = start_y
    queue_x[q_end] = start_x
    q_end += 1
    visited[start_y, start_x] = True
    distances[start_y, start_x] = 0

    while q_start < q_end:
        y = queue_y[q_start]
        x = queue_x[q_start]
        q_start += 1

        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue
                ny = y + dy
                nx = x + dx
                if 0 <= ny < height and 0 <= nx < width:
                    if skeleton[ny, nx] and not visited[ny, nx]:
                        visited[ny, nx] = True
                        distances[ny, nx] = distances[y, x] + 1
                        predecessors[ny, nx, 0] = y
                        predecessors[ny, nx, 1] = x
                        queue_y[q_end] = ny
                        queue_x[q_end] = nx
                        q_end += 1
    return distances, predecessors


def reconstruct_path(predecessors, end_y, end_x):
    path = []
    y = end_y
    x = end_x
    while y != -1 and x != -1:
        path.append((y, x))
        py = predecessors[y, x, 0]
        px = predecessors[y, x, 1]
        y, x = py, px
    path.reverse()
    return path


class ImageDiscretization:
    """
    This class describes the discretization in points of the image. 
    It takes as input an image and returns a set of
    points that will be transformed in dots.
    """

    def __init__(self, image_path, contour_mode, threshold_values, debug):
        self.contour_mode = contour_mode
        self.debug = debug
        self.threshold_values = threshold_values
        self.image_path = image_path
        self.image = cv2.imread(self.image_path, cv2.IMREAD_UNCHANGED)
        self.have_multiple_contours = False

        if self.image is None:
            raise FileNotFoundError(
                f"Image file '{self.image_path}' could not be found or the path is incorrect."
            )
        self.image = self._grayscale_to_rgba(self.image)

        # Handle the alpha channel and remove transparency if it exists
        self.image = self._handle_alpha_channel()

    def discretize_image(self):
        contours, gray = self.retrieve_contours()
        has_hole = self.check_multi_contour_hole()
        if self.contour_mode == 'automatic':
            if has_hole:
                self.contour_mode_to_use = 'contour'
                print(
                    "Has find a hole, use the contour method, for dots detections"
                )
            else:
                print(
                    "Hasn't find any hole, use the path method, for dots detections"
                )
                self.contour_mode_to_use = 'path'
        else:
            self.contour_mode_to_use = self.contour_mode

        if self.contour_mode_to_use == 'contour':
            if not has_hole:
                print("Warning: use contour method but no hole was detected."
                      "Path might be more convenient for dots placement.")
            return self._contours_to_dots(contours)
        elif self.contour_mode_to_use == 'path':
            if has_hole:
                print(
                    "Warning: use path method but one or more hole was detected."
                    "Contour might be more convenient for dots placement.")
            skeleton_path = self._retrieve_skeleton_path(contours, gray)
            return self._skeleton_to_dots(skeleton_path)
        else:
            raise ValueError(
                f"Invalid contour_mode '{self.contour_mode_to_use}'. Use 'automatic', 'contour' or 'path'."
            )

    def check_multi_contour_hole(self):
        """
        Checks if the image contains multiple contours and whether the largest contour has a hole.

        Returns:
            has_multiple_contours (bool): True if multiple contours are detected.
            has_hole (bool): True if the largest contour contains a hole.
        """
        # Convert the image to grayscale
        gray = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (5, 5), 0)

        # Apply thresholding
        threshold_value, max_value = self.threshold_values
        _, binary = cv2.threshold(gray, threshold_value, max_value,
                                  cv2.THRESH_BINARY_INV)

        # Morphological operations
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
        binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)

        # Find contours
        contours, hierarchy = cv2.findContours(binary, cv2.RETR_CCOMP,
                                               cv2.CHAIN_APPROX_NONE)

        # Check if any contours are found
        if not contours:
            print("No contours found in the image.")
            return False, False

        # Find the largest contour
        areas = [cv2.contourArea(c) for c in contours]
        largest_contour_index = np.argmax(areas)

        # Check if the largest contour has a hole
        # Hierarchy[0][largest_contour_index][2] != -1 indicates a hole exists
        has_hole = hierarchy[0][largest_contour_index][2] != -1

        return has_hole

    def retrieve_contours(self):
        """
        Retrieves the largest contour found in the image and displays intermediate steps if debug is enabled.
        Also checks if the largest shape has a hole or not and prints the result.
        """
        gray = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)

        threshold_value, max_value = self.threshold_values
        _, binary = cv2.threshold(gray, threshold_value, max_value,
                                  cv2.THRESH_BINARY_INV)

        _, _, largest_contour = self._find_contours_discrimate_area(binary)

        if self.debug:
            # Create a blank canvas for drawing the largest contour
            height, width = self.image.shape[:2]
            blank_canvas = np.zeros((height, width, 3),
                                    dtype=np.uint8)  # Black background

            # Draw the largest contour on the blank canvas
            cv2.drawContours(blank_canvas, [largest_contour], -1, (0, 255, 0),
                             1)  # Green contour

            # Resize for better visualization
            debug_image = resize_for_debug(blank_canvas)
            display_with_opencv(debug_image, 'Largest Contour Only')

        return largest_contour, gray

    def _contours_to_dots(self, contour):
        """
        Converts contour points to a standardized list of Dot objects.
        """
        dots = []
        for idx, point in enumerate(contour):
            # Ensure the position is always a tuple of integers
            position = (int(point[0][0]), int(point[0][1])
                        )  # Convert to (x, y)
            dots.append(Dot(position=position, dot_id=idx))
        return dots

    def _skeleton_to_dots(self, skeleton_path):
        """
        Converts skeleton path to a standardized list of Dot objects.
        """
        dots = []
        for idx, point in enumerate(skeleton_path):
            # Ensure the position is always a tuple of integers
            if isinstance(point,
                          (tuple, list, np.ndarray)) and len(point) == 2:
                position = (int(point[0]), int(point[1]))
            elif isinstance(point, np.ndarray) and point.shape == (1, 2):
                position = (int(point[0][0]), int(point[0][1]))
            else:
                raise ValueError(f"Unexpected point format: {point}")
            dots.append(Dot(position=position, dot_id=idx))
        return dots

    def _find_contours_discrimate_area(self, binary):

        # Use a retrieval mode that provides hierarchy information
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL,
                                       cv2.CHAIN_APPROX_NONE)

        if not contours:
            print(
                "No contours were found in the image. You can modify the binary"
                " thresholding arguments (-tb) to search contours in a wider range."
                " Use debug argument (-de) to have more information.")
            return None, None

        # Find the largest contour and its index
        areas = [cv2.contourArea(c) for c in contours]
        largest_contour_index = np.argmax(areas)
        largest_area = areas[largest_contour_index]
        area_threshold = 0.01 * largest_area

        filtered_contours = []

        for i in range(len(contours)):
            if areas[i] > area_threshold:
                filtered_contours.append(contours[i])

        if len(filtered_contours) > 1:
            self.have_multiple_contours = True

        largest_contour = contours[largest_contour_index]
        return contours, filtered_contours, largest_contour

    def retrieve_contours_all_contours(self):
        """
        Retrieves the largest contour found in the image and displays intermediate steps if debug is enabled.
        """
        gray = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)

        # Use the threshold values provided as arguments
        threshold_value, max_value = self.threshold_values
        _, binary = cv2.threshold(gray, threshold_value, max_value,
                                  cv2.THRESH_BINARY_INV)

        _, filtered_contours, _ = self._find_contours_discrimate_area(binary)
        if not filtered_contours:
            print(
                "No contours were found in the image. You can modify the binary"
                " thresholding arguments (-tb) to search contours in a wider range."
                " Use debug argument (-de) to have more information.")

        return filtered_contours, gray

    def _retrieve_skeleton_path(self, contour, gray):
        """
        Retrieves the skeleton path from the largest shape in the image.
        Ensures that the path is ordered in a clockwise direction.
        """

        # Create an empty mask
        mask = np.zeros_like(gray)

        # Draw the largest contour on the mask
        cv2.drawContours(mask, [contour], -1, 255, thickness=cv2.FILLED)

        # Skeletonize the shape using OpenCV ximgproc thinning
        skeleton = cv2.ximgproc.thinning(mask)

        if self.debug:
            debug_image = resize_for_debug(skeleton)
            display_with_opencv(debug_image, 'Skeletonized Image')

        ordered_skeleton_points = self._prune_skeleton_to_one_branch(skeleton)

        # Convert the list of tuples to a NumPy array with shape (N, 1, 2)
        ordered_skeleton_array = np.array(ordered_skeleton_points,
                                          dtype=np.int32).reshape(-1, 1, 2)

        return ordered_skeleton_array

    def _prune_skeleton_to_one_branch(self, skeleton):
        """
        Prunes the skeleton to retain only the longest branch.
        Uses Numba-accelerated functions to improve performance.
        """
        # Find endpoints in the skeleton
        endpoints = find_endpoints(skeleton)

        if len(endpoints) == 0:
            raise ValueError("No endpoints found in the skeleton.")

        # First BFS from an endpoint to find the farthest node (u)
        start_y, start_x = endpoints[0]
        distances1, predecessors1 = bfs_traversal(skeleton, start_y, start_x)
        u_y, u_x = np.unravel_index(np.argmax(distances1), distances1.shape)

        # Second BFS from u to find the farthest node (v)
        distances2, predecessors2 = bfs_traversal(skeleton, u_y, u_x)
        v_y, v_x = np.unravel_index(np.argmax(distances2), distances2.shape)

        # Reconstruct the longest path from u to v
        path = reconstruct_path(predecessors2, v_y, v_x)

        # Convert path to list of (x, y) tuples
        points_list = [(x, y) for y, x in path]

        return points_list

    def _handle_alpha_channel(self):
        if self.image.shape[2] == 4:
            bgr_image = self.image[:, :, :3]
            alpha_channel = self.image[:, :, 3]
            green_background = (0, 255, 0)
            mask = alpha_channel < 255
            bgr_image[mask] = green_background
            return bgr_image
        return self.image

    def _grayscale_to_rgba(self, image):
        """
        Converts a grayscale image to RGBA format.
        If the image has a single channel, it sets the alpha channel to fully opaque (255).
        If the image has two channels (grayscale with alpha), it uses the existing alpha channel.

        Parameters:
            grayscale_image (numpy.ndarray): The grayscale image to convert, 
                                             either with one channel (H, W) or two channels (H, W, 2).

        Returns:
            numpy.ndarray: The RGBA image with shape (H, W, 4). 
        """
        if len(image.shape) == 2:  # Single-channel grayscale
            height, width = image.shape
            rgba_image = np.zeros((height, width, 4), dtype=image.dtype)

            # Copy grayscale values to R, G, and B channels
            rgba_image[:, :, 0] = image  # R
            rgba_image[:, :, 1] = image  # G
            rgba_image[:, :, 2] = image  # B
            rgba_image[:, :, 3] = 255  # Alpha channel set to fully opaque

        elif len(
                image.shape
        ) == 3 and image.shape[2] == 2:  # Grayscale with alpha channel
            height, width = image.shape[:2]
            rgba_image = np.zeros((height, width, 4), dtype=image.dtype)

            # Copy grayscale values to R, G, and B channels
            rgba_image[:, :, 0] = image[:, :, 0]  # R
            rgba_image[:, :, 1] = image[:, :, 0]  # G
            rgba_image[:, :, 2] = image[:, :, 0]  # B
            rgba_image[:, :, 3] = image[:, :, 1]  # Use existing alpha channel
        else:
            return image
        return rgba_image
