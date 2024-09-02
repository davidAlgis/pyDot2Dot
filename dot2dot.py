import cv2
import numpy as np


def retrieve_contours(image_path):
    """
    Retrieves the cropped regions of each convex contour found in the image.

    Parameters:
        image_path (str): The path to the image file.

    Returns:
        List[np.ndarray]: A list of cropped images, each containing a convex contour.
        List[np.ndarray]: A list of contours found in the image.
    """
    # Load the image
    image = cv2.imread(image_path)

    # Check if the image was loaded successfully
    if image is None:
        raise FileNotFoundError(
            f"Image file '{image_path}' could not be found or the path is incorrect.")

    # Convert the image to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Apply a binary threshold to the image
    _, binary = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)

    # Find contours in the binary image
    contours, _ = cv2.findContours(
        binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Check if any contours were found
    if not contours:
        raise ValueError("No contours were found in the image.")

    # List to store cropped contour images
    cropped_contours = []

    # Filter and retrieve each contour as a cropped image
    for contour in contours:
        # Create a mask for the current contour
        mask = np.zeros_like(gray)
        cv2.drawContours(mask, [contour], -1, 255, thickness=cv2.FILLED)

        # Extract the bounding box of the contour
        x, y, w, h = cv2.boundingRect(contour)

        # Extract the region of interest (ROI) using the mask
        roi = cv2.bitwise_and(image, image, mask=mask)
        roi_cropped = roi[y:y+h, x:x+w]

        # Add the cropped ROI to the list
        cropped_contours.append(roi_cropped)

    return cropped_contours, contours


def contour_to_linear_paths(contours, epsilon_factor=0.01):
    """
    Converts each contour into a sequence of linear paths by approximating the contour with fewer points.

    Parameters:
        contours (List[np.ndarray]): A list of contours.
        epsilon_factor (float): The approximation accuracy as a percentage of the contour's perimeter.

    Returns:
        List[List[Tuple[int, int]]]: A list of linear paths, each represented as a list of (x, y) points.
    """
    linear_paths = []

    for contour in contours:
        # Approximate the contour with a polygon
        epsilon = epsilon_factor * cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, epsilon, True)

        # Convert the approximated contour to a list of (x, y) points
        path = [(point[0][0], point[0][1]) for point in approx]
        linear_paths.append(path)

    return linear_paths


def draw_paths_on_image(image, linear_paths):
    """
    Draws linear paths on an image.

    Parameters:
        image (np.ndarray): The original image where paths will be drawn.
        linear_paths (List[List[Tuple[int, int]]]): A list of paths, where each path is a list of (x, y) points.

    Returns:
        np.ndarray: The image with paths drawn.
    """
    # Copy the original image to draw on it
    output_image = image.copy()

    # Draw each path on the image
    for path in linear_paths:
        for i in range(len(path)):
            # Draw line between consecutive points
            start_point = path[i]
            # Loop back to the start for closed contours
            end_point = path[(i + 1) % len(path)]
            cv2.line(output_image, start_point, end_point, (0, 0, 255), 2)

    return output_image


# Example usage
image_path = 'testDot.png'
cropped_contours, contours = retrieve_contours(image_path)
linear_paths = contour_to_linear_paths(contours)

# Load the original image for drawing
original_image = cv2.imread(image_path)

# Draw the paths on the image
output_image_with_paths = draw_paths_on_image(original_image, linear_paths)

# Display the image with paths
cv2.imshow('Image with Paths', output_image_with_paths)
cv2.waitKey(0)
cv2.destroyAllWindows()
