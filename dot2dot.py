import cv2
import numpy as np

# Load the image
image = cv2.imread('testDot.png')

# Check if the image was loaded successfully
if image is None:
    raise FileNotFoundError(
        "Image file 'testDot.png' could not be found or the path is incorrect.")

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

# Filter and save each contour as a separate image
for i, contour in enumerate(contours):
    # Create a mask for the current contour
    mask = np.zeros_like(gray)
    cv2.drawContours(mask, [contour], -1, 255, thickness=cv2.FILLED)

    # Extract the bounding box of the contour
    x, y, w, h = cv2.boundingRect(contour)

    # Extract the region of interest (ROI) using the mask
    roi = cv2.bitwise_and(image, image, mask=mask)
    roi_cropped = roi[y:y+h, x:x+w]

    # Save the ROI as a separate image
    cv2.imwrite(f'contour_{i+1}.png', roi_cropped)

cv2.destroyAllWindows()
