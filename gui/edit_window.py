# edit_window.py

import tkinter as tk
from tkinter import Toplevel, Canvas, Frame, Scrollbar, Button
from PIL import Image, ImageFont, ImageDraw
import utils
import platform


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
                 image_width,
                 image_height,
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
        - image_width: Width of the image.
        - image_height: Height of the image.
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
        self.image_width = image_width
        self.image_height = image_height
        self.anchor_mapping = {
            'ls': 'sw',  # left, baseline
            'rs': 'se',  # right, baseline
            'ms': 's',  # center, baseline
            # Add more mappings if needed
        }

        # Create a new top-level window
        self.window = Toplevel(master)
        self.window.title("Edit Dots and Labels")
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)

        # Maximize the window based on the operating system
        self.maximize_window()

        # Use the provided image_width and image_height to set the canvas size
        self.canvas_width = image_width
        self.canvas_height = image_height

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
        self.canvas = Canvas(canvas_frame,
                             bg='white',
                             scrollregion=(0, 0, self.canvas_width,
                                           self.canvas_height),
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

        # Bind mouse events for dragging dots
        self.canvas.bind('<ButtonPress-1>', self.on_left_button_press)
        self.canvas.bind('<B1-Motion>', self.on_mouse_move)
        self.canvas.bind('<ButtonRelease-1>', self.on_left_button_release)

        # Initialize variables for dragging
        self.selected_dot_index = None  # Index of the dot being moved
        self.offset_x = 0  # Offset from the dot's center to the mouse click position
        self.offset_y = 0
        self.label_offsets = [((0, 0), None) for _ in self.labels
                              ]  # To keep track of label offsets

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

        # Adjust the initial view to show all dots and labels
        self.fit_canvas_to_content()

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
        self.dot_items = []  # List to store canvas item IDs for the dots

        for idx, (point, dot_box) in enumerate(self.dots):
            x, y = point
            x = x * self.scale
            y = y * self.scale
            item_id = self.canvas.create_oval(x - scaled_radius,
                                              y - scaled_radius,
                                              x + scaled_radius,
                                              y + scaled_radius,
                                              fill=fill_color,
                                              outline='')
            self.dot_items.append(item_id)

    def draw_labels(self):
        """
        Draws all the labels on the canvas.
        """
        fill_color = self.rgba_to_hex(self.font_color)
        scaled_font_size = max(int(self.font_size * self.scale),
                               1)  # Minimum font size of 1

        # Create a new font with the scaled size
        try:
            font = (self.font_path, scaled_font_size)
        except IOError:
            font = (None, scaled_font_size)  # Use default font

        self.label_items = []  # List to store canvas item IDs for labels

        for idx, (label, label_positions, color) in enumerate(self.labels):
            if label_positions:
                pos, anchor = label_positions[0]
                x, y = pos
                x = x * self.scale
                y = y * self.scale
                anchor_map = self.map_anchor(anchor)
                item_id = self.canvas.create_text(x,
                                                  y,
                                                  text=label,
                                                  fill=fill_color,
                                                  font=font,
                                                  anchor=anchor_map)
                self.label_items.append(item_id)
            else:
                self.label_items.append(None)  # No label

    def map_anchor(self, anchor_code):
        """
        Maps custom anchor codes to Tkinter anchor positions.

        Parameters:
        - anchor_code: String code ('ls', 'rs', 'ms', etc.)

        Returns:
        - Tkinter anchor string.
        """
        return self.anchor_mapping.get(anchor_code, 'center')

    def map_pil_anchor(self, anchor_code):
        """
        Maps custom anchor codes to PIL anchor positions.

        Parameters:
        - anchor_code: String code ('ls', 'rs', 'ms', etc.)

        Returns:
        - PIL anchor string.
        """
        mapping = {
            'ls': 'ls',  # left, baseline
            'rs': 'rs',  # right, baseline
            'ms': 'ms',  # center, baseline
            # Add more mappings if needed
        }
        return mapping.get(anchor_code, 'mm')  # default to middle center

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

        # Redraw the canvas contents
        self.redraw_canvas()

        # Update the scroll region
        canvas.config(scrollregion=(0, 0, self.canvas_width * self.scale,
                                    self.canvas_height * self.scale))

        # Adjust the view to keep the mouse position consistent
        # Calculate the new position after scaling
        self.canvas.xview_moveto(
            (x * scale_factor - event.x) / (self.canvas_width * self.scale))
        self.canvas.yview_moveto(
            (y * scale_factor - event.y) / (self.canvas_height * self.scale))

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
        # Optionally implement dynamic resizing behavior here
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
        Generates the image with the dots and labels and updates the main GUI.
        """
        # Generate the image
        canvas_image = self.generate_image()

        if canvas_image is not None and self.apply_callback:
            # Call the callback function provided by the main GUI
            self.apply_callback(canvas_image)

        # Close the EditWindow
        self.window.destroy()

    def generate_image(self):
        """
        Generates a PIL Image of the specified size and draws the dots and labels onto it.
        """
        # Create a blank image with the desired dimensions
        image = Image.new("RGBA",
                          (int(self.canvas_width), int(self.canvas_height)),
                          (255, 255, 255, 0))
        draw = ImageDraw.Draw(image)

        # Draw the dots
        for idx, (point, dot_box) in enumerate(self.dots):
            x, y = point
            radius = self.dot_radius
            fill_color = self.dot_color  # Should be a tuple (R, G, B, A)
            upper_left = (x - radius, y - radius)
            bottom_right = (x + radius, y + radius)
            draw.ellipse([upper_left, bottom_right], fill=fill_color)

        # Draw the labels
        font = self.font  # Should be a PIL ImageFont object
        for idx, (label, label_positions, color) in enumerate(self.labels):
            if label_positions:
                pos, anchor = label_positions[0]
                x, y = pos
                anchor_map = self.map_pil_anchor(anchor)
                fill_color = self.font_color  # Should be a tuple (R, G, B, A)
                draw.text((x, y),
                          label,
                          font=font,
                          fill=fill_color,
                          anchor=anchor_map)

        return image

    def fit_canvas_to_content(self):
        """
        Adjusts the initial zoom level and pan position so that all dots and labels are visible.
        """
        # Calculate bounding box for all dots and labels
        min_x, min_y, max_x, max_y = self.calculate_bounding_box()

        # Calculate the required scale to fit all content within the canvas
        canvas_display_width = self.canvas.winfo_width(
        ) if self.canvas.winfo_width() > 1 else 800
        canvas_display_height = self.canvas.winfo_height(
        ) if self.canvas.winfo_height() > 1 else 600

        content_width = max_x - min_x
        content_height = max_y - min_y

        # Determine scale factors for width and height
        scale_x = canvas_display_width / content_width if content_width > 0 else 1.0
        scale_y = canvas_display_height / content_height if content_height > 0 else 1.0

        # Choose the smaller scale to fit both dimensions
        initial_scale = min(scale_x, scale_y) * 0.9  # 90% to add padding

        # Clamp the scale within min and max
        initial_scale = max(self.min_scale, min(self.max_scale, initial_scale))
        self.scale = initial_scale

        # Update scroll region based on new scale
        self.update_scrollregion()

        # Redraw canvas with new scale
        self.redraw_canvas()

        # Center the view on the bounding box
        center_x = (min_x + max_x) / 2 * self.scale
        center_y = (min_y + max_y) / 2 * self.scale

        # Calculate the visible area
        visible_width = self.canvas.winfo_width()
        visible_height = self.canvas.winfo_height()

        # Calculate the scroll fractions
        x_fraction = (center_x - visible_width / 2) / (self.canvas_width *
                                                       self.scale)
        y_fraction = (center_y - visible_height / 2) / (self.canvas_height *
                                                        self.scale)

        # Clamp fractions between 0 and 1
        x_fraction = max(0, min(1, x_fraction))
        y_fraction = max(0, min(1, y_fraction))

        # Set the view
        self.canvas.xview_moveto(x_fraction)
        self.canvas.yview_moveto(y_fraction)

    def calculate_bounding_box(self):
        """
        Calculates the bounding box that contains all dots and labels.

        Returns:
        - (min_x, min_y, max_x, max_y): Tuple representing the bounding box.
        """
        # Initialize min and max values
        min_x = min([point[0] for point, _ in self.dots], default=0)
        min_y = min([point[1] for point, _ in self.dots], default=0)
        max_x = max([point[0] for point, _ in self.dots], default=0)
        max_y = max([point[1] for point, _ in self.dots], default=0)

        # Include labels in the bounding box
        for label, label_positions, _ in self.labels:
            for pos, _ in label_positions:
                min_x = min(min_x, pos[0])
                min_y = min(min_y, pos[1])
                max_x = max(max_x, pos[0])
                max_y = max(max_y, pos[1])

        return min_x, min_y, max_x, max_y

    def on_left_button_press(self, event):
        """
        Handles left mouse button press events.
        """
        # Get the mouse position in canvas coordinates
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)

        # Adjust for scaling
        scaled_radius = self.dot_radius * self.scale

        # Iterate over the dots to see if the click is near any dot
        for idx, (point, dot_box) in enumerate(self.dots):
            dot_x, dot_y = point
            dot_x_scaled = dot_x * self.scale
            dot_y_scaled = dot_y * self.scale

            # Calculate distance between mouse click and dot center
            distance = ((x - dot_x_scaled)**2 + (y - dot_y_scaled)**2)**0.5

            if distance <= scaled_radius:
                # Click is within the dot
                self.selected_dot_index = idx
                # Store offset between mouse position and dot center
                self.offset_x = dot_x_scaled - x
                self.offset_y = dot_y_scaled - y
                break  # Stop checking after finding the first dot

    def on_mouse_move(self, event):
        """
        Handles mouse movement while holding the left mouse button.
        """
        if self.selected_dot_index is not None:
            # Get the new mouse position in canvas coordinates
            x = self.canvas.canvasx(event.x)
            y = self.canvas.canvasy(event.y)

            # Adjust for offset
            new_x = x + self.offset_x
            new_y = y + self.offset_y

            # Convert back to original coordinate system (before scaling)
            dot_x = new_x / self.scale
            dot_y = new_y / self.scale

            # Update the dot's position in self.dots
            self.dots[self.selected_dot_index] = ((
                dot_x, dot_y), self.dots[self.selected_dot_index][1])

            # Update the position of the dot on the canvas
            scaled_radius = self.dot_radius * self.scale
            # Get the canvas item ID
            item_id = self.dot_items[self.selected_dot_index]
            # Move the dot to the new position
            self.canvas.coords(item_id, new_x - scaled_radius,
                               new_y - scaled_radius, new_x + scaled_radius,
                               new_y + scaled_radius)

            # Update label position if label exists
            if self.labels[self.selected_dot_index]:
                label_item_id = self.label_items[self.selected_dot_index]
                if label_item_id:
                    # Get the label data
                    label, label_positions, color = self.labels[
                        self.selected_dot_index]

                    # Compute the offset if not already done
                    offset, anchor = self.label_offsets[
                        self.selected_dot_index]
                    if anchor is None:
                        label_pos, anchor = label_positions[0]
                        label_x, label_y = label_pos
                        offset_x = label_x - self.dots[
                            self.selected_dot_index][0][0]
                        offset_y = label_y - self.dots[
                            self.selected_dot_index][0][1]
                        self.label_offsets[self.selected_dot_index] = ((
                            offset_x, offset_y), anchor)
                    else:
                        offset_x, offset_y = offset

                    # Update label position
                    label_x = dot_x + offset_x
                    label_y = dot_y + offset_y

                    # Update label in self.labels
                    self.labels[self.selected_dot_index] = (label, [
                        ((label_x, label_y), anchor)
                    ], color)

                    # Update label on canvas
                    # Get scaled positions
                    label_x_scaled = label_x * self.scale
                    label_y_scaled = label_y * self.scale
                    self.canvas.coords(label_item_id, label_x_scaled,
                                       label_y_scaled)

    def on_left_button_release(self, event):
        """
        Handles the left mouse button release event.
        """
        self.selected_dot_index = None
