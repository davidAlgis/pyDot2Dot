# gui/edit_window.py

import tkinter as tk
from tkinter import Toplevel, Canvas, Frame, Scrollbar, Button, messagebox
from tkinter import ttk
from PIL import Image, ImageFont, ImageDraw, ImageTk
import platform
import os

# Import the Tooltip class from tooltip.py
from gui.tooltip import Tooltip


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
        self.dots = dots.copy()
        self.labels = []
        for label_text, label_positions, color in labels:
            # Initialize label_moved to False
            self.labels.append((label_text, label_positions, color, False))

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

        # Bind mouse events for dragging dots and labels
        self.canvas.bind('<ButtonPress-1>', self.on_left_button_press)
        self.canvas.bind('<B1-Motion>', self.on_mouse_move)
        self.canvas.bind('<ButtonRelease-1>', self.on_left_button_release)

        # Initialize variables for dragging
        self.selected_dot_index = None  # Index of the dot being moved
        self.selected_label_index = None  # Index of the label being moved
        self.offset_x = 0  # Offset from the dot's center to the mouse click position
        self.offset_y = 0
        self.selected_label_offset_x = 0  # Offset for label dragging
        self.selected_label_offset_y = 0

        # Load the font
        try:
            self.font = ImageFont.truetype(self.font_path, self.font_size)
        except IOError:
            # Fallback to default font if specified font is not found
            self.font = ImageFont.load_default()
            print(
                f"Warning: Font '{self.font_path}' not found. Using default font."
            )

        # Load the plus and minus icons
        self.load_plus_icon()
        self.load_minus_icon()

        # Draw the dots and labels
        self.redraw_canvas()

        # Adjust the initial view to show all dots and labels
        self.fit_canvas_to_content()

        # Bind the resize event to adjust the canvas if needed
        self.window.bind("<Configure>", self.on_window_resize)

        # Add bottom button bar with 'Cancel', 'Apply', 'Add Dot', and 'Remove Dot' buttons
        self.add_bottom_buttons(main_frame)

    def load_plus_icon(self):
        """
        Loads the plus icon from 'gui/icons/plus.png'.
        Handles compatibility between different Pillow versions.
        """
        try:
            icon_path = os.path.join('gui', 'icons', 'plus.png')
            if not os.path.exists(icon_path):
                raise FileNotFoundError(f"Plus icon not found at {icon_path}.")

            # Attempt to use Image.Resampling.LANCZOS (Pillow >=10)
            try:
                resample_mode = Image.Resampling.LANCZOS
            except AttributeError:
                # Fallback for older Pillow versions
                resample_mode = Image.ANTIALIAS

            # Open, resize, and convert the image for Tkinter
            plus_image = Image.open(icon_path).resize((24, 24),
                                                      resample=resample_mode)
            self.plus_photo = ImageTk.PhotoImage(plus_image)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load plus icon: {e}")
            self.plus_photo = None

    def load_minus_icon(self):
        """
        Loads the minus icon from 'gui/icons/minus.png'.
        Handles compatibility between different Pillow versions.
        """
        try:
            icon_path = os.path.join('gui', 'icons', 'minus.png')
            if not os.path.exists(icon_path):
                raise FileNotFoundError(
                    f"Minus icon not found at {icon_path}.")

            # Attempt to use Image.Resampling.LANCZOS (Pillow >=10)
            try:
                resample_mode = Image.Resampling.LANCZOS
            except AttributeError:
                # Fallback for older Pillow versions
                resample_mode = Image.ANTIALIAS

            # Open, resize, and convert the image for Tkinter
            minus_image = Image.open(icon_path).resize((24, 24),
                                                       resample=resample_mode)
            self.minus_photo = ImageTk.PhotoImage(minus_image)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load minus icon: {e}")
            self.minus_photo = None

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

        for idx, (label, label_positions, color,
                  label_moved) in enumerate(self.labels):
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
        Adds a frame at the bottom with 'Cancel', 'Apply', 'Add Dot', and 'Remove Dot' buttons.
        """
        button_frame = Frame(parent_frame)
        button_frame.grid(row=1, column=0, sticky='ew', padx=5, pady=5)

        # Configure the grid for the button frame
        button_frame.columnconfigure(0, weight=1)
        button_frame.columnconfigure(1, weight=1)
        button_frame.columnconfigure(2, weight=1)
        button_frame.columnconfigure(
            3, weight=1)  # Additional column for Remove button

        # Apply Button
        apply_button = Button(button_frame,
                              text="Apply",
                              command=self.on_apply)
        apply_button.grid(row=0, column=0, sticky='e', padx=5)

        # Cancel Button
        cancel_button = Button(button_frame,
                               text="Cancel",
                               command=self.on_close)
        cancel_button.grid(row=0, column=1, sticky='e', padx=5)

        # Add Dot Button with Plus Icon
        if hasattr(self, 'plus_photo') and self.plus_photo:
            add_dot_button = Button(button_frame,
                                    image=self.plus_photo,
                                    command=self.open_add_dot_popup)
            add_dot_button.image = self.plus_photo  # Keep a reference
            Tooltip(add_dot_button, "Add a New Dot")
        else:
            add_dot_button = Button(button_frame,
                                    text="+",
                                    command=self.open_add_dot_popup)
            Tooltip(add_dot_button, "Add a New Dot")
        add_dot_button.grid(row=0, column=2, sticky='w', padx=5)

        # Remove Dot Button with Minus Icon
        if hasattr(self, 'minus_photo') and self.minus_photo:
            remove_dot_button = Button(button_frame,
                                       image=self.minus_photo,
                                       command=self.open_remove_dot_popup)
            remove_dot_button.image = self.minus_photo  # Keep a reference
            Tooltip(remove_dot_button, "Remove a Dot")
        else:
            remove_dot_button = Button(button_frame,
                                       text="-",
                                       command=self.open_remove_dot_popup)
            Tooltip(remove_dot_button, "Remove a Dot")
        remove_dot_button.grid(row=0, column=3, sticky='w', padx=5)

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
        for idx, (label, label_positions, color,
                  label_moved) in enumerate(self.labels):
            if label_positions:
                pos, anchor = label_positions[0]
                x, y = pos
                anchor_map = self.map_pil_anchor(anchor)
                fill_color = self.font_color  # Should be a tuple (R, G, B, A)
                draw.text((x, y),
                          label,
                          font=self.font,
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

        if content_width == 0 or content_height == 0:
            initial_scale = 1.0
        else:
            # Determine scale factors for width and height
            scale_x = canvas_display_width / content_width
            scale_y = canvas_display_height / content_height

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
        for label, label_positions, color, label_moved in self.labels:
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

        # First, check if the click is within any label's bounding box
        for idx, label_item_id in enumerate(self.label_items):
            if label_item_id:
                # Get the label's bounding box
                bbox = self.canvas.bbox(label_item_id)
                if bbox:
                    x1, y1, x2, y2 = bbox
                    if x1 <= x <= x2 and y1 <= y <= y2:
                        # Click is within the label's bounding box
                        self.selected_label_index = idx
                        # Store offset between mouse position and label position
                        label_x, label_y = self.canvas.coords(label_item_id)
                        self.selected_label_offset_x = label_x - x
                        self.selected_label_offset_y = label_y - y
                        return  # Stop checking after finding the first label

        # If no label was selected, check if the click is near any dot
        scaled_radius = self.dot_radius * self.scale
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
                return  # Stop checking after finding the first dot

        # If no dot or label was selected, do nothing
        self.selected_dot_index = None
        self.selected_label_index = None

    def on_mouse_move(self, event):
        """
        Handles mouse movement while holding the left mouse button.
        """
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)

        if self.selected_label_index is not None:
            # Moving a label
            new_x = x + self.selected_label_offset_x
            new_y = y + self.selected_label_offset_y

            # Convert back to original coordinate system (before scaling)
            label_x = new_x / self.scale
            label_y = new_y / self.scale

            # Update the label's position in self.labels
            label, label_positions, color, _ = self.labels[
                self.selected_label_index]
            anchor = label_positions[0][1]
            self.labels[self.selected_label_index] = (label, [
                ((label_x, label_y), anchor)
            ], color, True)

            # Update label on canvas
            label_item_id = self.label_items[self.selected_label_index]
            self.canvas.coords(label_item_id, new_x, new_y)

        elif self.selected_dot_index is not None:
            # Moving a dot
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

            # Update label position if label exists and hasn't been moved independently
            if self.selected_dot_index < len(self.labels):
                label, label_positions, color, label_moved = self.labels[
                    self.selected_dot_index]
                if not label_moved and label_positions:
                    label_item_id = self.label_items[self.selected_dot_index]
                    if label_item_id:
                        # Get the label data
                        label_text, label_positions, color, label_moved = self.labels[
                            self.selected_dot_index]
                        pos, anchor = label_positions[0]
                        # Calculate distance from dot to label as per calculate_dots_and_labels
                        distance_from_dots = 1.2 * self.dot_radius
                        # Define label position on top-right
                        label_x = dot_x + distance_from_dots
                        label_y = dot_y - distance_from_dots

                        # Update label in self.labels
                        self.labels[self.selected_dot_index] = (label_text, [
                            ((label_x, label_y), "ls")
                        ], color, label_moved)

                        # Update label on canvas
                        # Get scaled positions
                        label_x_scaled = label_x * self.scale
                        label_y_scaled = label_y * self.scale
                        self.canvas.coords(label_item_id, label_x_scaled,
                                           label_y_scaled)

        else:
            # No dot or label is selected
            pass

    def on_left_button_release(self, event):
        """
        Handles the left mouse button release event.
        """
        self.selected_dot_index = None
        self.selected_label_index = None

    def open_add_dot_popup(self):
        """
        Opens a popup window to add a new dot after a selected dot number.
        """
        if not self.dots:
            messagebox.showerror("Error", "No dots available to add after.")
            return

        popup = Toplevel(self.window)
        popup.title("Add a New Dot")
        popup.grab_set()  # Make the popup modal

        # Message Label
        message_label = tk.Label(popup, text="Add a dot after dot number:")
        message_label.pack(padx=10, pady=10)

        # Dropdown (Combobox) with dot numbers
        dot_numbers = [f"Dot {i+1}" for i in range(len(self.dots))]
        self.selected_dot_var = tk.StringVar()
        self.selected_dot_var.set(dot_numbers[0])  # Default selection
        dropdown = ttk.Combobox(popup,
                                textvariable=self.selected_dot_var,
                                values=dot_numbers,
                                state='readonly')
        dropdown.pack(padx=10, pady=5)

        # Button Frame
        button_frame = tk.Frame(popup)
        button_frame.pack(padx=10, pady=10)

        # Cancel Button
        cancel_button = tk.Button(button_frame,
                                  text="Cancel",
                                  command=popup.destroy)
        cancel_button.pack(side=tk.LEFT, padx=5)

        # Add Button
        add_button = tk.Button(button_frame,
                               text="Add",
                               command=lambda: self.add_dot(popup))
        add_button.pack(side=tk.LEFT, padx=5)

    def add_dot(self, popup):
        """
        Adds a new dot and its associated label after the selected dot number.

        Parameters:
        - popup: The popup window to close after adding.
        """
        selected_dot_text = self.selected_dot_var.get()
        selected_index = int(
            selected_dot_text.split()[1]) - 1  # Convert to 0-based index

        # Determine the position for the new dot
        if selected_index + 1 < len(self.dots):
            # There is a next dot; place the new dot in the middle between selected and next dot
            selected_dot = self.dots[selected_index][0]
            next_dot = self.dots[selected_index + 1][0]
            new_dot_x = (selected_dot[0] + next_dot[0]) / 2
            new_dot_y = (selected_dot[1] + next_dot[1]) / 2
        else:
            # No next dot; place the new dot with a default offset from the selected dot
            selected_dot = self.dots[selected_index][0]
            offset = 20  # pixels
            new_dot_x = selected_dot[0] + offset
            new_dot_y = selected_dot[1] + offset

        # Insert the new dot after the selected index
        self.dots.insert(selected_index + 1, ((new_dot_x, new_dot_y), None))

        # Calculate distance_from_dots based on the current dot radius
        distance_from_dots = 1.2 * self.dot_radius

        # Create an associated label on the top-right of the new dot
        new_label_text = f"{selected_index + 2}"
        new_label_position = (new_dot_x + distance_from_dots,
                              new_dot_y - distance_from_dots
                              )  # Top-right position
        new_label_anchor = 'ls'  # Anchor code for top-right as per calculate_dots_and_labels
        self.labels.insert(selected_index + 1, (new_label_text, [
            (new_label_position, new_label_anchor)
        ], self.font_color, False))

        # Update existing labels to maintain consistency (e.g., renaming to avoid duplication)
        for idx in range(selected_index + 2, len(self.labels)):
            old_label, positions, color, label_moved = self.labels[idx]
            new_label_text = f"{idx + 1}"
            self.labels[idx] = (new_label_text, positions, color, label_moved)

        # Redraw the canvas to reflect the new dot and label
        self.redraw_canvas()

        # Close the popup
        popup.destroy()

    def open_remove_dot_popup(self):
        """
        Opens a popup window to remove a selected dot number.
        """
        if not self.dots:
            messagebox.showerror("Error", "No dots available to remove.")
            return

        popup = Toplevel(self.window)
        popup.title("Remove a Dot")
        popup.grab_set()  # Make the popup modal

        # Message Label
        message_label = tk.Label(popup, text="Remove the dot number:")
        message_label.pack(padx=10, pady=10)

        # Dropdown (Combobox) with dot numbers
        dot_numbers = [f"Dot {i+1}" for i in range(len(self.dots))]
        self.remove_dot_var = tk.StringVar()
        self.remove_dot_var.set(dot_numbers[0])  # Default selection
        dropdown = ttk.Combobox(popup,
                                textvariable=self.remove_dot_var,
                                values=dot_numbers,
                                state='readonly')
        dropdown.pack(padx=10, pady=5)

        # Button Frame
        button_frame = tk.Frame(popup)
        button_frame.pack(padx=10, pady=10)

        # Cancel Button
        cancel_button = tk.Button(button_frame,
                                  text="Cancel",
                                  command=popup.destroy)
        cancel_button.pack(side=tk.LEFT, padx=5)

        # Remove Button
        remove_button = tk.Button(button_frame,
                                  text="Remove",
                                  command=lambda: self.remove_dot(popup))
        remove_button.pack(side=tk.LEFT, padx=5)

    def remove_dot(self, popup):
        """
        Removes the selected dot and its associated label.

        Parameters:
        - popup: The popup window to close after removing.
        """
        selected_dot_text = self.remove_dot_var.get()
        selected_index = int(
            selected_dot_text.split()[1]) - 1  # Convert to 0-based index

        # Confirm removal
        confirm = messagebox.askyesno(
            "Confirm Removal",
            f"Are you sure you want to remove {selected_dot_text}?")
        if not confirm:
            return

        # Remove the dot
        try:
            del self.dots[selected_index]
        except IndexError:
            messagebox.showerror("Error", "Selected dot does not exist.")
            popup.destroy()
            return

        # Remove the associated label
        try:
            del self.labels[selected_index]
        except IndexError:
            messagebox.showerror("Error", "Associated label does not exist.")
            # Continue even if label is missing

        # Update existing labels to maintain consistency (e.g., renaming to avoid duplication)
        for idx in range(selected_index, len(self.labels)):
            old_label, positions, color, label_moved = self.labels[idx]
            new_label_text = f"{idx + 1}"
            self.labels[idx] = (new_label_text, positions, color, label_moved)

        # Redraw the canvas to reflect the removed dot and label
        self.redraw_canvas()

        # Close the popup
        popup.destroy()
