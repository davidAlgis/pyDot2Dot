import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import networkx as nx
import matplotlib.pyplot as plt
import utils
from skimage.morphology import skeletonize


def retrieve_contours(image_path, threshold_values, debug=False):
    """
    Retrieves the contours found in the image and displays intermediate steps if debug is enabled.
    """
    image = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)

    if image is None:
        raise FileNotFoundError(
            f"Image file '{image_path}' could not be found or the path is incorrect."
        )

    image = utils.handle_alpha_channel(image, debug=debug)

    if debug:
        debug_image = utils.resize_for_debug(image)
        utils.display_with_matplotlib(debug_image, 'Original Image')

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Use the threshold values provided as arguments
    threshold_value, max_value = threshold_values
    _, binary = cv2.threshold(gray, threshold_value, max_value,
                              cv2.THRESH_BINARY_INV)

    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL,
                                   cv2.CHAIN_APPROX_NONE)

    if not contours:
        print(
            "No contours were found in the image. You can modify the binary"
            " thresholding arguments (-tb) to search contours in a wider range."
            " Use debug argument (-de) to have more information.")
        plt.show()
        exit(-3)

    if debug:
        debug_image = image.copy()
        cv2.drawContours(debug_image, contours, -1, (0, 255, 0), 1)
        debug_image = utils.resize_for_debug(debug_image)
        utils.display_with_matplotlib(debug_image, 'Contours on Image')

    return contours


def contour_to_linear_paths(contours,
                            epsilon_factor=0.001,
                            max_distance=None,
                            min_distance=None,
                            num_points=None,
                            image=None,
                            debug=False):
    """
    Converts each contour into a sequence of dominant points and inserts midpoints if needed.
    Optionally removes points that are closer than the specified minimum distance.
    Simplifies the path to the desired number of points if num_points is specified.
    Ensures that the points are ordered in a clockwise direction.
    """
    dominant_points_list = []

    for contour in contours:
        epsilon = epsilon_factor * cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, epsilon, True)

        # **Ensure clockwise direction using OpenCV's oriented area**
        area = cv2.contourArea(approx, oriented=True)
        if area < 0:
            # If area is negative, contour is counter-clockwise, reverse it
            approx = approx[::-1]

        # Convert to a list of (x, y) tuples
        points = [(point[0][0], point[0][1]) for point in approx]

        # Optionally insert midpoints
        if max_distance is not None:
            points = utils.insert_midpoints(points, max_distance)

        # Optionally filter close points
        if min_distance is not None:
            points = utils.filter_close_points(points, min_distance)

        # Optionally simplify the path
        if num_points is not None:
            points = utils.visvalingam_whyatt(points, num_points=num_points)

        dominant_points_list.append(points)

        if debug and image is not None:
            debug_image = image.copy()
            for point in points:
                cv2.circle(debug_image, point, 3, (0, 0, 255), -1)
            debug_image = utils.resize_for_debug(debug_image)
            utils.display_with_matplotlib(debug_image,
                                          'Contour Dominant Points')

    return dominant_points_list


def retrieve_skeleton_path(image_path,
                           epsilon_factor=0.001,
                           max_distance=None,
                           min_distance=None,
                           num_points=None,
                           debug=False):
    """
    Retrieves the skeleton path from the largest shape in the image.
    Ensures that the path is ordered in a clockwise direction.
    """
    image = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)

    if image is None:
        raise FileNotFoundError(
            f"Image file '{image_path}' could not be found or the path is incorrect."
        )

    image = utils.handle_alpha_channel(image, debug=debug)

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Threshold the image to obtain a binary image
    _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY_INV)

    # Find contours in the binary image
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL,
                                   cv2.CHAIN_APPROX_SIMPLE)

    if not contours:
        print(
            "No contours were found in the image. You can modify the binary"
            " thresholding arguments (-tb) to search contours in a wider range."
            " Use debug argument (-de) to have more information.")
        exit(-3)

    # Create an empty mask
    mask = np.zeros_like(gray)

    # Find the largest contour by area
    largest_contour = max(contours, key=cv2.contourArea)

    # Draw the largest contour on the mask
    cv2.drawContours(mask, [largest_contour], -1, 255, thickness=cv2.FILLED)

    # Skeletonize the shape
    skeleton = skeletonize(mask / 255)  # Convert to binary image (0 and 1)

    if debug:
        debug_image = utils.resize_for_debug((skeleton * 255).astype(np.uint8))
        utils.display_with_matplotlib(debug_image, 'Skeletonized Image')

    ordered_skeleton_points = prune_skeleton_to_one_branch(skeleton)
    ordered_skeleton_points = ensure_clockwise_order(ordered_skeleton_points)
    # Simplify the skeleton path
    simplified_skeleton = simplify_path(ordered_skeleton_points,
                                        epsilon_factor=epsilon_factor,
                                        max_distance=max_distance,
                                        min_distance=min_distance,
                                        num_points=num_points)

    if debug and image is not None:
        debug_image = image.copy()
        for point in simplified_skeleton:
            cv2.circle(debug_image, (point[0], point[1]), 3, (0, 0, 255), -1)
        debug_image = utils.resize_for_debug(debug_image)
        utils.display_with_matplotlib(debug_image,
                                      'Simplified Skeleton Points')

    # Return as a list containing one path (to be consistent with existing code)
    return [simplified_skeleton]


def ensure_clockwise_order(points):
    """
    Ensures that the given set of points forms a path in clockwise order.
    Points should be a list of (x, y) tuples.
    """

    def signed_area(points):
        """
        Compute the signed area of the polygon formed by the points.
        Positive area indicates clockwise ordering, negative indicates counter-clockwise.
        """
        area = 0
        n = len(points)
        for i in range(n):
            x1, y1 = points[i]
            x2, y2 = points[(i + 1) % n]
            area += (x2 - x1) * (y2 + y1)
        return area

    # Compute the signed area of the points
    area = signed_area(points)

    # If the area is negative, the points are in counter-clockwise order
    if area > 0:
        return points[::-1]  # Reverse the points to make them clockwise

    # Otherwise, the points are already in clockwise order
    return points


def prune_skeleton_to_one_branch(skeleton,
                                 epsilon_factor=0.001,
                                 max_distance=None,
                                 min_distance=None,
                                 num_points=None):
    """
    Prunes the skeleton to retain only the longest branch. This method ensures that only the main structure remains,
    discarding minor branches.
    """
    y_coords, x_coords = np.nonzero(skeleton)
    skeleton_coords = list(zip(x_coords, y_coords))

    # Create graph of the skeleton
    G = nx.Graph()
    for x, y in skeleton_coords:
        G.add_node((x, y))
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx != 0 or dy != 0:
                    nx_ = x + dx
                    ny_ = y + dy
                    if (0 <= nx_ < skeleton.shape[1]
                            and 0 <= ny_ < skeleton.shape[0]
                            and skeleton[ny_, nx_]):
                        G.add_edge((x, y), (nx_, ny_))

    # Find endpoints (degree 1 nodes)
    endpoints = [node for node in G.nodes() if G.degree(node) == 1]

    if len(endpoints) < 2:
        start = next(iter(G.nodes()))
        longest_path = list(nx.dfs_preorder_nodes(G, source=start))
    else:
        longest_path = find_longest_path(G, endpoints)

    # Simplify the longest path
    simplified_skeleton = simplify_path(longest_path, epsilon_factor,
                                        max_distance, min_distance, num_points)

    return simplified_skeleton


def find_longest_path(G, endpoints):
    """
    Finds the longest path between any two endpoints in the skeleton graph.
    """
    max_length = 0
    longest_path = []

    for i in range(len(endpoints)):
        for j in range(i + 1, len(endpoints)):
            try:
                path = nx.shortest_path(G,
                                        source=endpoints[i],
                                        target=endpoints[j])
                length = path_length(path)
                if length > max_length:
                    max_length = length
                    longest_path = path
            except nx.NetworkXNoPath:
                continue
    return longest_path


def path_length(path):
    """Calculate the Euclidean length of a path."""
    return sum(
        utils.point_distance(path[i], path[i + 1])
        for i in range(len(path) - 1))


def order_skeleton_points(skeleton):
    """
    Orders skeleton points into a path using graph traversal.
    """
    # Get skeleton coordinates
    y_coords, x_coords = np.nonzero(skeleton)
    skeleton_coords = list(zip(x_coords, y_coords))

    # Create a graph where each skeleton pixel is a node
    G = nx.Graph()
    for x, y in skeleton_coords:
        G.add_node((x, y))
        # Check 8-connected neighborhood
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if (dx != 0 or dy != 0):
                    nx_ = x + dx
                    ny_ = y + dy
                    if (0 <= nx_ < skeleton.shape[1]
                            and 0 <= ny_ < skeleton.shape[0]):
                        if skeleton[ny_, nx_]:
                            G.add_edge((x, y), (nx_, ny_))

    # Find endpoints (nodes with degree 1)
    endpoints = [node for node in G.nodes() if G.degree(node) == 1]

    if len(endpoints) >= 2:
        # Choose one endpoint as start and the other as end
        start, end = endpoints[:2]
        # Find the shortest path between start and end
        path = nx.shortest_path(G, source=start, target=end)
    else:
        # For closed loops or if no endpoints, pick an arbitrary node as start
        start = next(iter(G.nodes()))
        path = list(nx.dfs_preorder_nodes(G, source=start))

    # Convert path to numpy array
    ordered_points = np.array(path)

    return ordered_points


def simplify_path(points,
                  epsilon_factor=0.001,
                  max_distance=None,
                  min_distance=None,
                  num_points=None):
    """
    Simplifies the path using the Visvalingam–Whyatt algorithm and other optional parameters.
    """
    # Convert points to the required format (list of tuples)
    points_list = [(int(p[0]), int(p[1])) for p in points]

    # Optionally approximate the path (for skeletons, this might not be necessary)
    if epsilon_factor is not None:
        points_array = np.array(points_list, dtype=np.int32)
        epsilon = epsilon_factor * cv2.arcLength(points_array, False)
        approx = cv2.approxPolyDP(points_array, epsilon, False)
        points_list = [(int(p[0][0]), int(p[0][1])) for p in approx]

    # Optionally insert midpoints
    if max_distance is not None:
        points_list = utils.insert_midpoints(points_list, max_distance)

    # Optionally filter close points
    if min_distance is not None:
        points_list = utils.filter_close_points(points_list, min_distance)

    # Simplify the path using the Visvalingam–Whyatt algorithm
    if num_points is not None:
        points_list = utils.visvalingam_whyatt(points_list,
                                               num_points=num_points)

    return points_list


def draw_points_on_image(image_size,
                         linear_paths,
                         radius,
                         dot_color,
                         font_path,
                         font_size,
                         font_color,
                         debug=False):
    """
    Draws points at the vertices of each linear path and labels each point with a number on a transparent image.
    Labels are anchored based on their position (left, right, or center).
    Adds two additional positions directly above and below the dot, with labels justified in the center.
    Displays a debug image with lines connecting consecutive points only if debug=True.
    Returns only the main output image with dots and labels.
    """
    # Create the main output image with a transparent background
    blank_image_np, blank_image_pil, draw_pil, font = create_blank_image(
        image_size, font_path, font_size, transparent=True)

    # Step 1: Calculate potential positions for dots and labels
    dots, labels = calculate_dots_and_labels(linear_paths, radius, font,
                                             draw_pil, font_color)

    # Step 2: Check for overlaps and adjust positions
    labels = adjust_label_positions(labels, dots, draw_pil, font, image_size)

    # Step 3: Draw the dots and labels on the image
    final_image = draw_dots_and_labels(blank_image_np, dots, labels, radius,
                                       dot_color, font)

    # Step 4: Handle debug visualization if required
    if debug:
        display_debug_image_with_lines(blank_image_np, linear_paths, dots,
                                       labels, radius, dot_color, font)

    return final_image


def create_blank_image(image_size, font_path, font_size, transparent=False):
    """
    Creates a blank image using PIL and sets up the drawing context with the specified font.
    The image can be either transparent or with a solid color background.
    """
    if transparent:
        blank_image_pil = Image.new(
            # Transparent
            "RGBA",
            (image_size[1], image_size[0]),
            (255, 255, 255, 0))
    else:
        blank_image_pil = Image.new(
            # White background
            "RGB",
            (image_size[1], image_size[0]),
            (255, 255, 255))
    draw_pil = ImageDraw.Draw(blank_image_pil)
    font = ImageFont.truetype(font_path, font_size)
    blank_image_np = np.array(blank_image_pil)
    return blank_image_np, blank_image_pil, draw_pil, font


def calculate_dots_and_labels(linear_paths, radius, font, draw_pil,
                              font_color):
    """
    Calculate the positions for dots and potential label positions based on the dot positions.
    """
    dots = []
    labels = []
    distance_from_dots = 1.2 * radius
    global_point_index = 1  # Global counter for labeling across all paths

    for path_index, path in enumerate(linear_paths):
        for point_index, point in enumerate(path):
            dot_box = (point[0] - radius, point[1] - radius, point[0] + radius,
                       point[1] + radius)
            dots.append((point, dot_box))
            label = str(global_point_index)
            global_point_index += 1

            # Define possible label positions around the dot
            label_positions = [
                ((point[0] + distance_from_dots,
                  point[1] - distance_from_dots), "ls"),  # top-right
                ((point[0] + distance_from_dots,
                  point[1] + distance_from_dots), "ls"),  # bottom-right
                ((point[0] - distance_from_dots,
                  point[1] - distance_from_dots), "rs"),  # top-left
                ((point[0] - distance_from_dots,
                  point[1] + distance_from_dots), "rs"),  # bottom-left
                ((point[0], point[1] - 2 * distance_from_dots),
                 "ms"),  # directly above
                ((point[0], point[1] + 3 * distance_from_dots), "ms"
                 )  # directly below
            ]
            labels.append((label, label_positions, font_color))

    return dots, labels


def get_label_box(position, text, anchor, draw_pil, font):
    """Returns the bounding box of the label (x_min, y_min, x_max, y_max) depending on anchor."""
    bbox = draw_pil.textbbox(position, text, font=font, anchor=anchor)
    return bbox


def adjust_label_positions(labels, dots, draw_pil, font, image_size):
    """
    Check for overlaps between labels and dots and adjust the positions of the labels.
    Ensure that labels are not placed outside the image boundaries.
    """

    def does_overlap(box1, box2):
        """Check if two bounding boxes overlap."""
        return not (box1[2] < box2[0] or box1[0] > box2[2] or box1[3] < box2[1]
                    or box1[1] > box2[3])

    def is_within_bounds(box, image_size):
        """Check if the bounding box is within the image boundaries."""
        return (
            0 <= box[0] <= image_size[1] and  # x_min >= 0 and within width
            0 <= box[1] <= image_size[0] and  # y_min >= 0 and within height
            0 <= box[2] <= image_size[1] and  # x_max within width
            0 <= box[3] <= image_size[0])  # y_max within height

    # Step 1: Precompute all label bounding boxes
    precomputed_label_boxes = []
    for idx, (label, positions, color) in enumerate(labels):
        position_boxes = []
        for pos, anchor in positions:
            box = get_label_box(pos, label, anchor, draw_pil, font)
            position_boxes.append(box)
        precomputed_label_boxes.append(position_boxes)

    # Step 2: Precompute all current label bounding boxes to check overlaps
    current_label_boxes = [boxes[0] for boxes in precomputed_label_boxes
                           ]  # Assuming first position initially

    # Step 3: Iterate through each label and adjust positions
    for i, (label, positions, color) in enumerate(labels):
        valid_positions = []
        all_positions_info = []

        for pos_idx, (pos, anchor) in enumerate(positions):
            label_box = precomputed_label_boxes[i][pos_idx]
            # Check overlap with dots
            overlaps_with_dots = any(
                does_overlap(label_box, dot[1]) for dot in dots)
            # Check overlap with other labels
            overlaps_with_labels = any(
                does_overlap(label_box, current_label_boxes[j])
                for j in range(len(labels)) if j != i)
            overlaps = overlaps_with_dots or overlaps_with_labels

            within_bounds = is_within_bounds(label_box, image_size)

            distance = ((pos[0] - dots[i][0][0])**2 +
                        (pos[1] - dots[i][0][1])**2)**0.5
            all_positions_info.append((pos, distance, overlaps, anchor))

            if not overlaps and within_bounds:
                valid_positions.append((pos, anchor, pos_idx))

        if valid_positions:
            # Choose the closest non-overlapping position
            best_position, best_anchor, best_pos_idx = min(
                valid_positions,
                key=lambda p: all_positions_info[p[2]][1]  # Sort by distance
            )
            labels[i] = (label, [(best_position, best_anchor)], color)
            current_label_boxes[i] = precomputed_label_boxes[i][best_pos_idx]
        else:
            print(
                f"Warning: Label {label} overlaps at all positions or is out of bounds"
            )
            # Red color for all positions in case of overlap or out-of-bounds
            labels[i] = (label, positions, (255, 0, 0))

    return labels


def draw_dots_and_labels(blank_image_np, dots, labels, radius, dot_color,
                         font):
    """
    Draws dots and labels on the main image using PIL for both.
    """
    # Convert the NumPy array to a PIL image
    blank_image_pil = Image.fromarray(blank_image_np)
    draw_pil = ImageDraw.Draw(blank_image_pil)

    # Draw the dots using PIL
    for point, _ in dots:
        # Draw an ellipse as a dot (PIL equivalent of a circle)
        upper_left = (point[0] - radius, point[1] - radius)
        bottom_right = (point[0] + radius, point[1] + radius)
        draw_pil.ellipse([upper_left, bottom_right], fill=dot_color)

    # Draw the labels using PIL
    for label, positions, color in labels:
        if color == (255, 0, 0):  # If it's a red label (overlap warning)
            for pos, anchor in positions:
                draw_pil.text(pos, label, font=font, fill=color, anchor=anchor)
        else:
            draw_pil.text(positions[0][0],
                          label,
                          font=font,
                          fill=color,
                          anchor=positions[0][1])

    # Convert back to NumPy array for the final image
    return np.array(blank_image_pil)


def display_debug_image_with_lines(blank_image_np, linear_paths, dots, labels,
                                   radius, dot_color, font):
    """
    Displays a debug image with lines connecting consecutive points, dots, and labels.
    Alternates line color: odd lines are red, even lines are blue.
    Uses PIL for drawing both the dots and the labels.
    """
    # Convert the NumPy array to a PIL image for consistent drawing
    debug_image_pil = Image.fromarray(blank_image_np)
    draw_debug_pil = ImageDraw.Draw(debug_image_pil)

    # Draw lines between consecutive points on the debug image
    for path in linear_paths:
        for i, point in enumerate(path):
            if i > 0:
                prev_point = path[i - 1]
                # Alternate colors: red for odd, blue for even
                line_color = (255, 0, 0) if (i % 2 == 1) else (
                    0, 0, 255)  # Red for odd, blue for even
                # Draw line between prev_point and point
                draw_debug_pil.line([prev_point, point],
                                    fill=line_color,
                                    width=2)

    # Draw dots on the debug image using PIL
    for point, _ in dots:
        upper_left = (point[0] - radius, point[1] - radius)
        bottom_right = (point[0] + radius, point[1] + radius)
        draw_debug_pil.ellipse([upper_left, bottom_right], fill=dot_color)

    # Add labels to the debug image
    for label, positions, color in labels:
        if color == (255, 0, 0):  # If it's a red label (overlap warning)
            for pos, anchor in positions:
                draw_debug_pil.text(pos,
                                    label,
                                    font=font,
                                    fill=color,
                                    anchor=anchor)
        else:
            draw_debug_pil.text(positions[0][0],
                                label,
                                font=font,
                                fill=color,
                                anchor=positions[0][1])

    # Convert the PIL image back to a NumPy array for display
    final_debug_image = np.array(debug_image_pil)

    # Display the debug image with lines, dots, and labels
    utils.display_with_matplotlib(final_debug_image,
                                  'Debug Image with Dots, Lines, and Labels')
