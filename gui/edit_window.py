# edit_window.py

import tkinter as tk
from tkinter import Toplevel, Canvas, Frame, Scrollbar, Button
from PIL import Image, ImageFont
import utils
import platform
import io


class EditWindow:

    def __init__(self,
                 master,
                 dots,
                 labels,
                 dot_color,
                 dot_radius,
                 font_color,
                 font_path,
                 font_size,
                 apply_callback=None):
        """
        Initializes the EditWindow to allow editing of dots and labels.

        Parameters:
        - master: The parent Tkinter window.
        - dots: List of tuples [(point, dot_box), ...] where point is (x, y).
        - labels: List of tuples [(label, label_positions, color), ...]
        - dot_color: Tuple representing the RGBA color of dots.
        - dot_radius: Radius of the dots.
        - font_color: Tuple representing the RGBA color of labels.
        - font_path: String path to the font file.
        - font_size: Integer size of the font.
        - apply_callback: Function to call when 'Apply' is clicked.
        """
        self.master = master
        self.dots = dots
        self.labels = labels
        self.dot_color = dot_color
        self.dot_radius = dot_radius
        self.font_color = font_color
        self.font_path = font_path
        self.font_size = font_size
        self.apply_callback = apply_callback  # Callback to main GUI
        self.anchor_mapping = {
            'ls': 'sw',  # left, descender (bottom-left)
            'rs': 'se',  # right, descender (bottom-right)
            'ms': 's',  # middle, descender (bottom-center)
            # Add more mappings if needed
        }

        # Create a new top-level window
        self.window = Toplevel(master)
        self.window.title("Edit Dots and Labels")
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)

        # Maximize the window based on the operating system
        self.maximize_window()

        # Determine canvas size based on the maximum x and y coordinates
        self.canvas_width, self.canvas_height = self.calculate_canvas_size()

        # Configure the grid layout for the window
        self.window.rowconfigure(0, weight=1)
        self.window.columnconfigure(0, weight=1)

        # Create the main frame to hold the canvas and buttons
        main_frame = Frame(self.window)
        main_frame.grid(row=0, column=0, sticky='nsew')

        # Configure the grid layout for the main frame
        main_frame.rowconfigure(0, weight=1)  # Canvas frame row
        main_frame.rowconfigure(1, weight=0)  # Button frame row
        main_frame.columnconfigure(0, weight=1)

        # Create a Frame to hold the canvas and scrollbars
        canvas_frame = Frame(main_frame)
        canvas_frame.grid(row=0, column=0, sticky='nsew')

        # Create vertical and horizontal scrollbars
        self.v_scroll = Scrollbar(canvas_frame, orient=tk.VERTICAL)
        self.v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.h_scroll = Scrollbar(canvas_frame, orient=tk.HORIZONTAL)
        self.h_scroll.pack(side=tk.BOTTOM, fill=tk.X)

        # Create and pack the canvas
        self.canvas = Canvas(
            canvas_frame,
            bg='white',
            scrollregion=(0, 0, 1000, 1000),  # Set a default scroll region
            xscrollcommand=self.h_scroll.set,
            yscrollcommand=self.v_scroll.set)
        self.canvas.pack(side=tk.LEFT, fill="both", expand=True)

        # Configure scrollbars
        self.v_scroll.config(command=self.canvas.yview)
        self.h_scroll.config(command=self.canvas.xview)

        # Initialize scaling factors
        self.scale = 1.0
        self.min_scale = 0.1
        self.max_scale = 5.0

        # Bind mouse events for zooming
        if platform.system() == 'Windows':
            self.canvas.bind("<MouseWheel>", self.on_zoom)  # Windows
        else:
            self.canvas.bind("<Button-4>", self.on_zoom)  # Linux scroll up
            self.canvas.bind("<Button-5>", self.on_zoom)  # Linux scroll down

        # Bind mouse events for panning with right-click press
        self.bind_panning_events()

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
        self.redraw_canvas()

        # Bind the resize event to adjust the canvas if needed
        self.window.bind("<Configure>", self.on_window_resize)

        # Add bottom button bar with 'Cancel' and 'Apply' buttons
        self.add_bottom_buttons(main_frame)

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
        scaled_radius = self.dot_radius * self.scale
        fill_color = self.rgba_to_hex(self.dot_color)

        for idx, (point, dot_box) in enumerate(self.dots):
            x, y = point
            x = x * self.scale
            y = y * self.scale
            self.canvas.create_oval(x - scaled_radius,
                                    y - scaled_radius,
                                    x + scaled_radius,
                                    y + scaled_radius,
                                    fill=fill_color,
                                    outline='')

    def draw_labels(self):
        """
        Draws all the labels on the canvas.
        """
        fill_color = self.rgba_to_hex(self.font_color)
        scaled_font_size = max(int(self.font_size * self.scale),
                               1)  # Minimum font size of 1

        # Use negative font size to specify size in points
        font = (self.font_path, -scaled_font_size)  # Negative size for points

        for idx, (label, label_positions, color) in enumerate(self.labels):
            if label_positions:
                pos, anchor = label_positions[0]
                x, y = pos
                x = x * self.scale
                y = y * self.scale
                anchor_map = self.map_anchor(anchor)
                self.canvas.create_text(x,
                                        y,
                                        text=label,
                                        fill=fill_color,
                                        font=font,
                                        anchor=anchor_map)

    def map_anchor(self, anchor_code):
        """
        Maps custom anchor codes to Tkinter anchor positions.

        Parameters:
        - anchor_code: String code ('ls', 'rs', 'ms', etc.)

        Returns:
        - Tkinter anchor string.
        """
        return self.anchor_mapping.get(anchor_code, 'center')

    def on_zoom(self, event):
        """
        Handles zooming in and out with the mouse wheel.
        """
        # Get the mouse position in canvas coordinates
        canvas = self.canvas
        x = canvas.canvasx(event.x)
        y = canvas.canvasy(event.y)

        if platform.system() == 'Windows':
            if event.delta > 0:
                scale_factor = 1.1
            elif event.delta < 0:
                scale_factor = 1 / 1.1
            else:
                return
        else:
            if event.num == 4:
                scale_factor = 1.1
            elif event.num == 5:
                scale_factor = 1 / 1.1
            else:
                return

        # Update the scale factor
        new_scale = self.scale * scale_factor
        new_scale = max(self.min_scale, min(self.max_scale, new_scale))
        scale_factor = new_scale / self.scale
        if scale_factor == 1:
            return  # No change

        self.scale = new_scale

        # Adjust the scroll region to the new scale
        self.update_scrollregion()

        # Adjust the canvas view to keep the mouse at the same position
        # before and after the scaling
        canvas_width = self.canvas_width * self.scale
        canvas_height = self.canvas_height * self.scale

        # Redraw the canvas contents
        self.redraw_canvas()

        # Calculate the new scroll region
        self.canvas.config(scrollregion=(0, 0, canvas_width, canvas_height))

        # Adjust the view to center around the cursor
        # Calculate the ratio of the cursor position to the canvas size
        rx = x / (canvas_width / scale_factor)
        ry = y / (canvas_height / scale_factor)

        # Adjust the view to center around the cursor
        self.canvas.xview_moveto((x * scale_factor - event.x) / canvas_width)
        self.canvas.yview_moveto((y * scale_factor - event.y) / canvas_height)

    def update_scrollregion(self):
        """
        Updates the scroll region of the canvas based on the current scale.
        """
        scaled_width = self.canvas_width * self.scale
        scaled_height = self.canvas_height * self.scale
        self.canvas.config(scrollregion=(0, 0, scaled_width, scaled_height))

    def redraw_canvas(self):
        """
        Clears and redraws the canvas contents based on the current scale.
        """
        self.canvas.delete("all")
        self.draw_dots()
        self.draw_labels()

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

    def bind_panning_events(self):
        """
        Binds mouse events for panning with right-click press.
        """
        if platform.system(
        ) == 'Darwin':  # macOS might use Button-2 for right-click
            self.canvas.bind('<ButtonPress-2>', self.on_pan_start)
            self.canvas.bind('<B2-Motion>', self.on_pan_move)
        else:
            self.canvas.bind('<ButtonPress-3>', self.on_pan_start)
            self.canvas.bind('<B3-Motion>', self.on_pan_move)

    def on_pan_start(self, event):
        """
        Records the starting position for panning.
        """
        self.canvas.scan_mark(event.x, event.y)

    def on_pan_move(self, event):
        """
        Handles the panning motion.
        """
        self.canvas.scan_dragto(event.x, event.y, gain=1)

    def add_bottom_buttons(self, parent_frame):
        """
        Adds a frame at the bottom with 'Cancel' and 'Apply' buttons.
        """
        button_frame = Frame(parent_frame)
        button_frame.grid(row=1, column=0, sticky='ew', padx=5, pady=5)

        # Configure the grid for the button frame
        button_frame.columnconfigure(0, weight=1)
        button_frame.columnconfigure(1, weight=1)

        apply_button = Button(button_frame,
                              text="Apply",
                              command=self.on_apply)
        apply_button.grid(row=0, column=0, sticky='e', padx=5)

        cancel_button = Button(button_frame,
                               text="Cancel",
                               command=self.on_close)
        cancel_button.grid(row=0, column=1, sticky='e', padx=5)

    def on_apply(self):
        """
        Handles the 'Apply' button click.
        Saves the canvas content as an image and updates the main GUI.
        """
        # Save the canvas content as an image
        canvas_image = self.get_canvas_image()

        if canvas_image is not None and self.apply_callback:
            # Call the callback function provided by the main GUI
            self.apply_callback(canvas_image)

        # Close the EditWindow
        self.window.destroy()

    def get_canvas_image(self):
        """
        Captures the canvas content and returns it as a PIL Image.
        """
        # Update the canvas to ensure all items are drawn
        self.canvas.update()

        # Get the canvas content as PostScript
        ps_data = self.canvas.postscript(colormode='color')

        # Use PIL to convert PostScript to an image
        try:
            # Read the PostScript data into an Image
            image = Image.open(io.BytesIO(ps_data.encode('utf-8')))
            # Convert to RGBA for consistency
            image = image.convert('RGBA')
            return image
        except Exception as e:
            print(f"Error capturing canvas image: {e}")
            return None
