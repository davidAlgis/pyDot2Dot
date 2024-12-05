import numpy as np
from collections import defaultdict
import utils
from dot import Dot
from dot_label import DotLabel


class GridDots:

    def __init__(self, grid_width, grid_height, cell_size, dots):
        """
        Initializes the grid with given dimensions and cell size,
        and populates it with the provided dots and their labels.

        Parameters:
        - grid_width: Width of the grid (e.g., image width).
        - grid_height: Height of the grid (e.g., image height).
        - cell_size: Size of each cell in the grid.
        - dots: List of Dot objects to be added to the grid.
        """
        self.cell_size = cell_size
        self.grid_width = grid_width
        self.grid_height = grid_height
        self.nbr_cells_x = int(np.ceil(self.grid_width / self.cell_size))
        self.nbr_cells_y = int(np.ceil(self.grid_height / self.cell_size))
        self.nbr_tot_cells = self.nbr_cells_x * self.nbr_cells_y

        # Grid cells for dots and labels
        # Each cell is identified by (cell_row, cell_col)
        # The value is a set of objects (dots or labels)
        self.grid_dots = defaultdict(set)
        self.grid_labels = defaultdict(set)

        # Populate the grid with the dots and labels
        for dot in dots:
            self.add_dot_to_grid(dot)
            if dot.label:
                self.add_label_to_grid(dot.label)

    def retrieve_cell_index(self, position):
        """
        Retrieves the cell indices (cell_row, cell_col) for a given position.

        Parameters:
        - position: Tuple (x, y) representing the position.

        Returns:
        - (cell_row, cell_col): Indices of the cell in the grid.
        """
        x, y = position
        cell_col = int(x // self.cell_size)
        cell_row = int(y // self.cell_size)
        # Clamp indices to grid boundaries
        cell_col = max(0, min(cell_col, self.nbr_cells_x - 1))
        cell_row = max(0, min(cell_row, self.nbr_cells_y - 1))
        return (cell_row, cell_col)

    def add_dot_to_grid(self, dot):
        """
        Adds a dot to the grid based on its position.

        Parameters:
        - dot: Dot object to be added.
        """
        cell_index = self.retrieve_cell_index(dot.position)
        self.grid_dots[cell_index].add(dot)

    def add_label_to_grid(self, label):
        """
        Adds a label to the grid based on its position.

        Parameters:
        - label: DotLabel object to be added.
        """
        cell_index = self.retrieve_cell_index(label.position)
        self.grid_labels[cell_index].add(label)

    def remove_dot_from_grid(self, dot):
        """
        Removes a dot from its current grid cell.

        Parameters:
        - dot: Dot object to be removed.
        """
        cell_index = self.retrieve_cell_index(dot.position)
        if dot in self.grid_dots[cell_index]:
            self.grid_dots[cell_index].remove(dot)

    def remove_label_from_grid(self, label):
        """
        Removes a label from its current grid cell.

        Parameters:
        - label: DotLabel object to be removed.
        """
        cell_index = self.retrieve_cell_index(label.position)
        if label in self.grid_labels[cell_index]:
            self.grid_labels[cell_index].remove(label)

    def move_dot_and_label(self, dot):
        """
        Updates the grid when a dot (and its label) has moved to a new position.

        Parameters:
        - dot: Dot object that has moved.
        """
        # Remove from old cell
        self.remove_dot_from_grid(dot)
        if dot.label:
            self.remove_label_from_grid(dot.label)

        # Add to new cell
        self.add_dot_to_grid(dot)
        if dot.label:
            self.add_label_to_grid(dot.label)

    def move_label(self, label):
        """
        Updates the grid when a label has moved to a new position.

        Parameters:
        - label: DotLabel object that has moved.
        """
        # Remove from old cell
        self.remove_label_from_grid(label)
        # Add to new cell
        self.add_label_to_grid(label)

    def find_neighbors(self, obj):
        """
        Finds and returns the neighboring dots and labels of the given object.

        Parameters:
        - obj: The object (Dot or DotLabel) for which to find neighbors.

        Returns:
        - neighbors: A set of neighboring objects (dots and labels).
        """
        neighbors = set()

        # Get the cell indices of the object's position
        cell_row, cell_col = self.retrieve_cell_index(obj.position)

        # Define the range of cells to search (including neighboring cells)
        for row in range(max(0, cell_row - 1),
                         min(self.nbr_cells_y, cell_row + 2)):
            for col in range(max(0, cell_col - 1),
                             min(self.nbr_cells_x, cell_col + 2)):
                cell_index = (row, col)
                # Add dots and labels from this cell to the neighbors
                neighbors.update(self.grid_dots.get(cell_index, set()))
                neighbors.update(self.grid_labels.get(cell_index, set()))

        # Remove the object itself from the neighbors if present
        neighbors.discard(obj)

        return neighbors

    def do_overlap(self, obj):
        """
        Checks if the given object (dot or label) overlaps with any of its neighbors.

        Parameters:
        - obj: The object (Dot or DotLabel) to check for overlap.

        Returns:
        - True if the object overlaps with any neighbor, False otherwise.
        """
        # Find neighbors
        neighbors = self.find_neighbors(obj)

        # Iterate through neighbors and check for overlap
        for neighbor in neighbors:
            if self.check_overlap(obj, neighbor):
                return True  # Overlap found
        return False  # No overlap

    def check_overlap(self, obj1, obj2):
        """
        Checks if obj1 and obj2 overlap.

        Parameters:
        - obj1, obj2: The objects to check (Dot or DotLabel).

        Returns:
        - True if the objects overlap, False otherwise.
        """
        # Determine the types of obj1 and obj2
        if isinstance(obj1, Dot):
            if isinstance(obj2, Dot):
                return self.dots_overlap(obj1, obj2)
            elif isinstance(obj2, DotLabel):
                return self.dot_label_overlap(obj1, obj2)
        elif isinstance(obj1, DotLabel):
            if isinstance(obj2, Dot):
                return self.dot_label_overlap(obj2, obj1)  # Reverse parameters
            elif isinstance(obj2, DotLabel):
                return self.labels_overlap(obj1, obj2)
        return False  # If types are unrecognized

    def dots_overlap(self, dot1, dot2):
        """
        Checks if two dots overlap.

        Returns:
        - True if the dots overlap, False otherwise.
        """
        pos1 = np.array(dot1.position)
        pos2 = np.array(dot2.position)
        r1 = dot1.radius
        r2 = dot2.radius
        distance_sq = np.sum((pos1 - pos2)**2)
        radii_sum = r1 + r2
        return distance_sq < radii_sum**2

    def dot_label_overlap(self, dot, label):
        """
        Checks if a dot and a label overlap.

        Returns:
        - True if the dot and label overlap, False otherwise.
        """
        # Get dot parameters
        center = np.array(dot.position)
        radius = dot.radius

        # Get label bounding box
        x_min, y_min, x_max, y_max = self.get_label_bbox(label)

        # Find closest point on rectangle to circle's center
        closest_x = np.clip(center[0], x_min, x_max)
        closest_y = np.clip(center[1], y_min, y_max)
        closest_point = np.array([closest_x, closest_y])

        # Compute distance to circle's center
        distance_sq = np.sum((center - closest_point)**2)

        return distance_sq < radius**2

    def labels_overlap(self, label1, label2):
        """
        Checks if two labels overlap.

        Returns:
        - True if the labels overlap, False otherwise.
        """
        x1_min, y1_min, x1_max, y1_max = self.get_label_bbox(label1)
        x2_min, y2_min, x2_max, y2_max = self.get_label_bbox(label2)

        # Check for rectangle overlap
        # If one rectangle is on the left side of the other
        if x1_max <= x2_min or x2_max <= x1_min:
            return False
        # If one rectangle is above the other
        if y1_max <= y2_min or y2_max <= y1_min:
            return False
        return True  # Rectangles overlap

    def get_label_bbox(self, label):
        """
        Computes the bounding box of a label, adjusted to be slightly smaller
        to avoid false positives in overlap detection.

        Parameters:
        - label: DotLabel object.

        Returns:
        - bbox: (x_min, y_min, x_max, y_max) tuple representing the adjusted bounding box.
        """
        # Get the size of the text
        text = label.text
        font = label.font

        # Use font.getsize() or font.getbbox()
        try:
            # For newer versions of PIL
            bbox = font.getbbox(text)
            width = bbox[2] - bbox[0]
            height = bbox[3] - bbox[1]
        except AttributeError:
            # For older versions of PIL
            width, height = font.getsize(text)

        x, y = label.position

        # Adjust the position based on anchor
        # Define anchor adjustments
        # Assuming default is 'ls' (left, baseline)
        anchor_adjustments = {
            'ls': (0, -height),  # Left side
            'rs': (-width, -height),  # Right side
            'ms': (-width / 2, -height),  # Middle side
            # Add more mappings if needed
        }
        dx, dy = anchor_adjustments.get(label.anchor, (0, -height))
        x_min = x + dx
        y_min = y + dy
        x_max = x_min + width
        y_max = y_min + height

        # Adjust the bounding box to be slightly smaller
        shrink_margin = height * 0.1
        new_width = max(width - 2 * shrink_margin, 1)
        new_height = max(height - 2 * shrink_margin, 1)
        x_min += (width - new_width) / 2
        y_min += (height - new_height) / 2
        x_max = x_min + new_width
        y_max = y_min + new_height

        return (x_min, y_min, x_max, y_max)

    def find_all_overlaps(self):
        """
        Finds all dots and labels that are overlapping in the grid.

        Returns:
        - overlaps: A set of objects (dots and labels) that are overlapping with at least one other object.
        """
        overlaps = set()

        # Get all unique cell indices that contain dots or labels
        all_cells = set(self.grid_dots.keys()) | set(self.grid_labels.keys())

        # For each cell in the grid
        for cell_index in all_cells:
            # Get all objects in this cell
            cell_objects = set()
            cell_objects.update(self.grid_dots.get(cell_index, set()))
            cell_objects.update(self.grid_labels.get(cell_index, set()))

            # Convert to list for indexing
            cell_objects = list(cell_objects)
            num_objects = len(cell_objects)

            # Check each pair of objects in the cell
            for i in range(num_objects):
                obj1 = cell_objects[i]
                if obj1 in overlaps:
                    continue  # Already identified as overlapping
                # Find neighbors in the same cell starting from i+1 to avoid duplicate checks
                for j in range(i + 1, num_objects):
                    obj2 = cell_objects[j]
                    if obj2 in overlaps:
                        continue  # Already identified as overlapping
                    if self.check_overlap(obj1, obj2):
                        overlaps.add(obj1)
                        overlaps.add(obj2)
                # Also check neighbors in neighboring cells
                neighbors = self.find_neighbors(obj1)
                for neighbor in neighbors:
                    if neighbor in overlaps:
                        continue  # Already identified as overlapping
                    if self.check_overlap(obj1, neighbor):
                        overlaps.add(obj1)
                        overlaps.add(neighbor)

        return overlaps
