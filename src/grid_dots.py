import math
from collections import defaultdict

class GridDot:
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
        self.nbr_cells_x = int(math.ceil(self.grid_width / self.cell_size))
        self.nbr_cells_y = int(math.ceil(self.grid_height / self.cell_size))
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
        for row in range(max(0, cell_row - 1), min(self.nbr_cells_y, cell_row + 2)):
            for col in range(max(0, cell_col - 1), min(self.nbr_cells_x, cell_col + 2)):
                cell_index = (row, col)
                # Add dots and labels from this cell to the neighbors
                neighbors.update(self.grid_dots.get(cell_index, set()))
                neighbors.update(self.grid_labels.get(cell_index, set()))

        # Remove the object itself from the neighbors if present
        neighbors.discard(obj)

        return neighbors
