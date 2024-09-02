import cv2
import numpy as np


def retrieve_contours(image_path):
    """
    Retrieves the cropped regions of each convex contour found in the image.

    Parameters:
        image_path (str): The path to the image file.

    Returns:
        List[np.ndarray]: A list of cropped images, each containing a convex contour.
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

    return cropped_contours


# Example usage
contours = retrieve_contours('testDot.png')
for i, contour_image in enumerate(contours):
    cv2.imshow(f'Contour {i+1}', contour_image)
    cv2.waitKey(0)

cv2.destroyAllWindows()
