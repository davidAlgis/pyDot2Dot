# edit_window.py

import tkinter as tk
from tkinter import Toplevel, Canvas, NW, Scrollbar, Frame
from PIL import Image, ImageDraw, ImageFont, ImageTk
import utils
import platform


class EditWindow:

    def __init__(self, master, dots, labels, dot_color, dot_radius, font_color,
                 font_path, font_size):
        """
        Initializes the EditWindow to allow editing of dots and labels.

        Parameters:
        - master: The parent Tkinter window.
        - dots: List of tuples [(point, dot_box), ...] where point is (x, y).
        - labels: List of tuples [(label, label_positions, color), ...]
        - dot_color: Tuple representing the RGBA color of dots.
        - font_color: Tuple representing the RGBA color of labels.
        - font_path: String path to the font file.
        - font_size: Integer size of the font.
        """
        self.master = master
        self.dots = dots
        self.labels = labels
        self.dot_color = dot_color
        self.dot_radius = dot_radius
        self.font_color = font_color
        self.font_path = font_path
        self.font_size = font_size

        # Create a new top-level window
        self.window = Toplevel(master)
        self.window.title("Edit Dots and Labels")
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)

        # Maximize the window based on the operating system
        self.maximize_window()

        # Determine canvas size based on the maximum x and y coordinates
        self.canvas_width, self.canvas_height = self.calculate_canvas_size()

        # Create a Frame to hold the canvas and scrollbars
        self.frame = Frame(self.window)
        self.frame.pack(fill="both", expand=True)

        # Create vertical and horizontal scrollbars
        self.v_scroll = Scrollbar(self.frame, orient=tk.VERTICAL)
        self.v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.h_scroll = Scrollbar(self.frame, orient=tk.HORIZONTAL)
        self.h_scroll.pack(side=tk.BOTTOM, fill=tk.X)

        # Create and pack the canvas
        self.canvas = Canvas(self.frame,
                             width=self.canvas_width,
                             height=self.canvas_height,
                             bg='white',
                             scrollregion=(0, 0, self.canvas_width,
                                           self.canvas_height),
                             xscrollcommand=self.h_scroll.set,
                             yscrollcommand=self.v_scroll.set)
        self.canvas.pack(fill="both", expand=True)

        # Configure scrollbars
        self.v_scroll.config(command=self.canvas.yview)
        self.h_scroll.config(command=self.canvas.xview)

        # Load the font
        try:
            self.font = ImageFont.truetype(self.font_path, self.font_size)
        except IOError:
            # Fallback to default font if specified font is not found
            self.font = ImageFont.load_default()
            print(
                f"Warning: Font '{self.font_path}' not found. Using default font."
            )

        # Draw the dots and labels
        self.draw_dots()
        self.draw_labels()

        # Bind the resize event to adjust the canvas if needed
        self.window.bind("<Configure>", self.on_window_resize)

    def maximize_window(self):
        """
        Maximizes the window based on the operating system.
        """
        os_name = platform.system()
        if os_name == 'Windows':
            self.window.state('zoomed')
        elif os_name == 'Darwin':  # macOS
            self.window.attributes('-zoomed', True)
        else:  # Linux and others
            screen_width = self.window.winfo_screenwidth()
            screen_height = self.window.winfo_screenheight()
            self.window.geometry(f"{screen_width}x{screen_height}+0+0")

    def calculate_canvas_size(self):
        """
        Calculates the required canvas size based on the maximum x and y coordinates of the dots and labels.

        Returns:
        - (width, height): Tuple representing the canvas size.
        """
        max_x = max([point[0] for point, _ in self.dots], default=800)
        max_y = max([point[1] for point, _ in self.dots], default=600)

        # Consider labels positions for canvas size
        for label, label_positions, _ in self.labels:
            for pos, _ in label_positions:
                max_x = max(max_x, pos[0])
                max_y = max(max_y, pos[1])

        # Add some padding
        padding = 100
        return max_x + padding, max_y + padding

    def rgba_to_hex(self, rgba):
        """
        Converts an RGBA tuple to a hexadecimal color string.

        Parameters:
        - rgba: Tuple of (R, G, B, A)

        Returns:
        - Hex color string (e.g., '#FF0000')
        """
        return '#%02x%02x%02x' % (rgba[0], rgba[1], rgba[2])

    def draw_dots(self):
        """
        Draws all the dots on the canvas.
        """
        radius = self.dot_radius  # Determine radius based on font size
        fill_color = self.rgba_to_hex(self.dot_color)

        for idx, (point, dot_box) in enumerate(self.dots):
            x, y = point
            self.canvas.create_oval(x - radius,
                                    y - radius,
                                    x + radius,
                                    y + radius,
                                    fill=fill_color,
                                    outline='')

    def draw_labels(self):
        """
        Draws all the labels on the canvas.
        """
        fill_color = self.rgba_to_hex(self.font_color)

        for idx, (label, label_positions, color) in enumerate(self.labels):
            # For exact reproduction, use the first available label position
            if label_positions:
                pos, anchor = label_positions[0]
                x, y = pos
                anchor_map = self.map_anchor(anchor)
                self.canvas.create_text(x,
                                        y,
                                        text=label,
                                        fill=fill_color,
                                        font=(self.font_path, self.font_size),
                                        anchor=anchor_map)

    def map_anchor(self, anchor_code):
        """
        Maps custom anchor codes to Tkinter anchor positions.

        Parameters:
        - anchor_code: String code ('ls', 'rs', 'ms', etc.)

        Returns:
        - Tkinter anchor string.
        """
        mapping = {
            'ls': 'sw',  # left side
            'rs': 'se',  # right side
            'ms': 'n',  # middle side (top)
            # Add more mappings as needed
        }
        return mapping.get(anchor_code, 'center')

    def on_window_resize(self, event):
        """
        Handles window resize events to adjust the canvas size if needed.
        """
        # Currently, the canvas has a fixed scrollregion based on the initial size.
        # If dynamic resizing/scaling is needed, implement it here.
        pass

    def on_close(self):
        """
        Handles the closing of the EditWindow.
        """
        self.window.destroy()
