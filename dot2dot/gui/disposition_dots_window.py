# gui/test_values_window.py

import tkinter as tk
from tkinter import Toplevel, Canvas, Frame, Scrollbar, messagebox
from tkinter import ttk
from PIL import Image, ImageTk
import platform
import cv2
import numpy as np
from dot2dot.image_discretization import ImageDiscretization

# Import the Tooltip class from tooltip.py
from dot2dot.gui.tooltip import Tooltip
from dot2dot.utils import compute_image_diagonal, insert_midpoints, filter_close_points
from dot2dot.gui.utilities_gui import set_icon


class DispositionDotsWindow:

    def __init__(self, master, dots_config, background_image, main_gui=None):
        """
        Initializes the TestValuesWindow to allow testing different epsilon values.

        Parameters:
        - master: The parent Tkinter window.
        - dots_config: Configuration for dots.
        - background_image: PIL Image object to be displayed as the background.
        - main_gui: Reference to the main GUI (optional).
        """

        self.master = master
        self.main_gui = main_gui  # Store the reference to the main GUI
        self.background_image = background_image.copy().convert("RGBA")
        self.dots_config = dots_config

        # Initialize background opacity
        self.bg_opacity = 0.5  # Default opacity

        # Initialize ImageDiscretization and compute contour
        image_discretization = ImageDiscretization(
            self.dots_config.input_path,
            self.dots_config.shape_detection.lower(),
            self.dots_config.threshold_binary, False)
        self.dots = image_discretization.discretize_image()

        self.contour = np.array([dot.position for dot in self.dots],
                                dtype=np.int32)
        # Convert contour to (x, y) tuples
        self.contour_points = [(point[0], point[1]) for point in self.contour]

        approx = cv2.approxPolyDP(
            np.array(self.contour_points, dtype=np.int32),
            self.dots_config.epsilon, True)

        # Convert to a list of (x, y) tuples
        self.approx_contour_points = [(point[0][0], point[0][1])
                                      for point in approx]

        # Compute perimeter of the contour
        self.perimeter = cv2.arcLength(
            np.array(self.contour_points, dtype=np.float32), True)
        if self.perimeter == 0:
            messagebox.showerror("Error",
                                 "Contour perimeter is zero. Cannot proceed.")
            return

        # Compute the diagonal length of the image
        image_np = np.array(self.background_image)
        self.diagonal_length = compute_image_diagonal(image_np)

        # Initialize the list to keep track of dot items on the canvas
        self.dot_items = []

        # Determine the available resampling method
        try:
            self.resample_method = Image.Resampling.LANCZOS
        except AttributeError:
            self.resample_method = Image.ANTIALIAS  # For older Pillow versions

        # Create a new top-level window
        self.window = Toplevel(master)
        self.window.title("Test Epsilon Values")
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)
        set_icon(self.window)

        # Maximize the window based on the operating system
        self.maximize_window()

        # Use the background image dimensions to set the canvas size
        self.canvas_width, self.canvas_height = self.background_image.size

        # Configure the grid layout for the window
        self.window.rowconfigure(0, weight=1)
        self.window.columnconfigure(0, weight=1)

        # Create the main frame to hold the canvas and controls
        self.main_frame = Frame(self.window)
        self.main_frame.grid(row=0, column=0, sticky='nsew')

        # Configure the grid layout for the main frame
        self.main_frame.rowconfigure(0, weight=1)  # Canvas row
        self.main_frame.columnconfigure(0, weight=1)

        # Create a Frame to hold the canvas and scrollbars
        canvas_frame = Frame(self.main_frame)
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
        elif platform.system() == 'Darwin':
            self.canvas.bind("<MouseWheel>", self.on_zoom_mac)  # macOS
        else:
            self.canvas.bind("<Button-4>", self.on_zoom)  # Linux scroll up
            self.canvas.bind("<Button-5>", self.on_zoom)  # Linux scroll down

        # Bind mouse events for panning with right-click press
        self.bind_panning_events()

        # Bind mouse events for dragging (if needed in future enhancements)
        # Currently, no draggable items

        # Draw the background image
        self.background_photo = None
        self.draw_background()

        # Create a frame for controls (opacity and epsilon sliders)
        controls_frame = Frame(self.main_frame,
                               bg='#b5cccc',
                               bd=2,
                               relief='groove',
                               padx=10,
                               pady=10)
        controls_frame.grid(row=1, column=0, sticky='ew', padx=10, pady=10)

        # Label for Background Opacity
        background_opacity_label = tk.Label(controls_frame,
                                            text="Background Opacity:",
                                            bg='#b5cccc',
                                            font=("Helvetica", 10, "bold"))
        background_opacity_label.pack(side=tk.TOP, anchor='w')

        # Opacity slider
        self.opacity_var = tk.DoubleVar(value=self.bg_opacity)
        opacity_slider = ttk.Scale(controls_frame,
                                   from_=0.0,
                                   to=1.0,
                                   orient=tk.HORIZONTAL,
                                   variable=self.opacity_var,
                                   command=self.on_opacity_change)
        opacity_slider.pack(side=tk.TOP, fill='x', expand=True, pady=5)
        Tooltip(opacity_slider, "Adjust the background image opacity.")

        # Display the current opacity value
        self.opacity_display = tk.Label(controls_frame,
                                        text=f"{self.bg_opacity:.2f}",
                                        bg='#b5cccc',
                                        font=("Helvetica", 10))
        self.opacity_display.pack(side=tk.TOP, anchor='w')

        # Separator
        separator = ttk.Separator(controls_frame, orient='horizontal')
        separator.pack(fill='x', pady=10)

        # Label for Epsilon
        epsilon_label = tk.Label(controls_frame,
                                 text="Epsilon:",
                                 bg='#b5cccc',
                                 font=("Helvetica", 12, "bold"))
        epsilon_label.pack(side=tk.TOP, anchor='w')

        # Frame to hold the epsilon slider and its labels
        epsilon_frame = Frame(controls_frame, bg='#b5cccc')
        epsilon_frame.pack(side=tk.TOP, fill='x', expand=True, pady=5)

        # Add "more dots" label on the left
        more_dots_label = tk.Label(epsilon_frame,
                                   text="more dots",
                                   bg='#b5cccc',
                                   font=("Helvetica", 10))
        more_dots_label.pack(side=tk.LEFT, padx=5)

        # Epsilon slider
        self.epsilon_var = tk.DoubleVar(value=self.dots_config.epsilon)
        epsilon_slider = ttk.Scale(epsilon_frame,
                                   from_=1e-1,
                                   to=100,
                                   orient=tk.HORIZONTAL,
                                   variable=self.epsilon_var,
                                   command=self.on_epsilon_change)
        epsilon_slider.pack(side=tk.LEFT, fill='x', expand=True)

        # Add "less dots" label on the right
        less_dots_label = tk.Label(epsilon_frame,
                                   text="less dots",
                                   bg='#b5cccc',
                                   font=("Helvetica", 10))
        less_dots_label.pack(side=tk.LEFT, padx=5)

        Tooltip(epsilon_slider,
                "Adjust the epsilon value for contour approximation.")
        # Display the current epsilon value
        self.epsilon_display = tk.Label(controls_frame,
                                        text=f"{self.dots_config.epsilon:.4f}",
                                        bg='#b5cccc',
                                        font=("Helvetica", 10))
        self.epsilon_display.pack(side=tk.TOP, anchor='w')

        # Separator
        separator_distance = ttk.Separator(controls_frame, orient='horizontal')
        separator_distance.pack(fill='x', pady=10)

        # Toggle for enabling distance configuration
        self.enable_distance_var = tk.BooleanVar(value=bool(
            self.dots_config.distance_min or self.dots_config.distance_max))

        distance_toggle = ttk.Checkbutton(
            controls_frame,
            text="Enable Distance Between Dots Configuration:",
            variable=self.enable_distance_var,
            command=self.toggle_distance_controls)
        distance_toggle.pack(side=tk.TOP, anchor='w', pady=5)

        # Frame for Distance Sliders (initially hidden if toggle is False)
        self.distance_frame = Frame(controls_frame, bg='#b5cccc')
        if not self.enable_distance_var.get():
            self.distance_frame.pack_forget()
        else:
            self.distance_frame.pack(side=tk.TOP,
                                     fill='x',
                                     expand=True,
                                     pady=5)

        # -------------------- Minimum Distance Slider with Value Display --------------------
        min_distance_label = tk.Label(self.distance_frame,
                                      text="Minimum Distance:",
                                      bg='#b5cccc',
                                      font=("Helvetica", 10))
        min_distance_label.pack(side=tk.TOP, anchor='w')

        # Frame for Minimum Distance Slider and Label
        min_distance_display_frame = Frame(self.distance_frame, bg='#b5cccc')
        min_distance_display_frame.pack(side=tk.TOP,
                                        fill='x',
                                        expand=True,
                                        pady=2)

        # Minimum Distance Slider
        self.min_distance_var = tk.DoubleVar(
            value=float(self.dots_config.distance_min or 0))
        min_distance_slider = ttk.Scale(min_distance_display_frame,
                                        from_=0,
                                        to=100,
                                        orient=tk.HORIZONTAL,
                                        variable=self.min_distance_var,
                                        command=self.on_distance_change)
        min_distance_slider.pack(side=tk.LEFT, fill='x', expand=True)

        # Label to Display Current Minimum Distance Value
        self.min_distance_display = tk.Label(
            min_distance_display_frame,
            text=f"{self.min_distance_var.get():.0f}",
            bg='#b5cccc',
            font=("Helvetica", 10))
        self.min_distance_display.pack(side=tk.RIGHT, padx=5)

        # -------------------- Maximum Distance Slider with Value Display --------------------
        max_distance_label = tk.Label(self.distance_frame,
                                      text="Maximum Distance:",
                                      bg='#b5cccc',
                                      font=("Helvetica", 10))
        max_distance_label.pack(side=tk.TOP, anchor='w')

        # Frame for Maximum Distance Slider and Label
        max_distance_display_frame = Frame(self.distance_frame, bg='#b5cccc')
        max_distance_display_frame.pack(side=tk.TOP,
                                        fill='x',
                                        expand=True,
                                        pady=2)

        # Maximum Distance Slider
        self.max_distance_var = tk.DoubleVar(
            value=float(self.dots_config.distance_max or 0))
        max_distance_slider = ttk.Scale(max_distance_display_frame,
                                        from_=5,
                                        to=500,
                                        orient=tk.HORIZONTAL,
                                        variable=self.max_distance_var,
                                        command=self.on_distance_change)
        max_distance_slider.pack(side=tk.LEFT, fill='x', expand=True)

        # Label to Display Current Maximum Distance Value
        self.max_distance_display = tk.Label(
            max_distance_display_frame,
            text=f"{self.max_distance_var.get():.0f}",
            bg='#b5cccc',
            font=("Helvetica", 10))
        self.max_distance_display.pack(side=tk.RIGHT, padx=5)

        # Initialize the dots display
        self.current_points = self.approx_contour_points  # Store current points
        self.draw_dots(self.approx_contour_points)
        # Adjust the initial view to show all dots and labels
        self.fit_canvas_to_content()

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

    def draw_background(self):
        """
        Draws the background image on the canvas with the current opacity.
        """
        # Apply opacity to the original image for display purposes
        if self.bg_opacity < 1.0:
            # Create a copy with adjusted opacity
            bg_image = self.background_image.copy()
            alpha = bg_image.split()[3]
            alpha = alpha.point(lambda p: p * self.bg_opacity)
            bg_image.putalpha(alpha)
        else:
            bg_image = self.background_image

        # Scale the image according to the current scale
        scaled_width = int(bg_image.width * self.scale)
        scaled_height = int(bg_image.height * self.scale)
        scaled_image = bg_image.resize((scaled_width, scaled_height),
                                       self.resample_method)

        # Convert the scaled image to a PhotoImage
        self.background_photo = ImageTk.PhotoImage(scaled_image)

        # Draw the image on the canvas
        self.canvas.create_image(0,
                                 0,
                                 image=self.background_photo,
                                 anchor='nw')

    def fit_canvas_to_content(self):
        """
        Adjusts the initial zoom level so that the entire image fits within the canvas.
        """
        # Ensure all pending geometry changes are processed
        self.window.update_idletasks()

        # Get the current window size
        window_width = self.window.winfo_width()
        window_height = self.window.winfo_height()

        # Calculate the scale factor to fit the image within the window
        scale_x = window_width / self.canvas_width
        scale_y = window_height / self.canvas_height
        scale_factor = min(scale_x, scale_y) * 0.9  # 90% to add padding

        # Clamp the scale factor within the allowed range
        scale_factor = max(self.min_scale, min(self.max_scale, scale_factor))
        self.scale = scale_factor

        # Update the scroll region based on the new scale
        self.update_scrollregion()

        # Redraw the canvas with the new scale
        self.redraw_canvas()

        # Optionally, center the view (you can adjust as needed)
        self.canvas.xview_moveto(0)
        self.canvas.yview_moveto(0)

    def on_opacity_change(self, value):
        """
        Callback function for the opacity slider.
        Updates the background opacity and redraws the canvas.
        """
        self.bg_opacity = float(value)
        self.opacity_display.config(text=f"{self.bg_opacity:.2f}")
        self.redraw_canvas()

    def redraw_canvas(self):
        """
        Clears and redraws the canvas contents based on the current scale and opacity.
        """
        self.canvas.delete("all")
        self.draw_background()
        # Redraw the dots
        self.draw_dots(self.current_points)

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

    def on_zoom(self, event):
        """
        Handles zooming in and out with the mouse wheel.
        """
        # Get the mouse position in canvas coordinates
        canvas = self.canvas

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

    def on_zoom_mac(self, event):
        """
        Handles zooming for macOS which uses different event handling for the mouse wheel.
        """
        # Similar to on_zoom but might require different delta handling
        if event.delta > 0:
            scale_factor = 1.1
        elif event.delta < 0:
            scale_factor = 1 / 1.1
        else:
            return

        # Reuse the on_zoom logic
        self.on_zoom(event)

    def update_scrollregion(self):
        """
        Updates the scroll region of the canvas based on the current scale.
        """
        scaled_width = self.canvas_width * self.scale
        scaled_height = self.canvas_height * self.scale
        self.canvas.config(scrollregion=(0, 0, scaled_width, scaled_height))

    def on_epsilon_change(self, value):
        """
        Callback function for the epsilon slider.
        Updates the contour approximation and redraws the dots.
        """
        epsilon_slider_value = float(value)
        self.epsilon_display.config(text=f"{epsilon_slider_value:.4f}")

        # Calculate epsilon as a fraction of the perimeter
        # epsilon = epsilon_slider_value * self.perimeter

        approx = cv2.approxPolyDP(
            np.array(self.contour_points, dtype=np.int32),
            epsilon_slider_value, True)

        # Extract points
        approx_points = [(point[0][0], point[0][1]) for point in approx]
        # Store current points for redraw
        self.current_points = approx_points

        # Draw the dots
        self.draw_dots(approx_points)

    def on_distance_change(self, _):
        """
        Callback for distance sliders. Updates the number of points based on current values.
        Also updates the display labels for minimum and maximum distances.
        """
        min_distance = self.min_distance_var.get()
        max_distance = self.max_distance_var.get()

        # Update dots_config values
        self.dots_config.distance_min = min_distance
        self.dots_config.distance_max = max_distance

        # Update the display labels with current slider values
        self.min_distance_display.config(text=f"{min_distance:.0f}")
        self.max_distance_display.config(text=f"{max_distance:.0f}")

        # Adjust points dynamically
        approx = cv2.approxPolyDP(
            np.array(self.contour_points, dtype=np.int32),
            self.epsilon_var.get(), True)

        points = [(point[0][0], point[0][1]) for point in approx]

        # Insert midpoints for max distance
        if max_distance > 0:
            points = insert_midpoints(points, max_distance)

        # Filter close points for min distance
        if min_distance > 0:
            points = filter_close_points(points, min_distance)

        self.current_points = points
        # self.redraw_canvas()
        self.draw_dots(points)

    def toggle_distance_controls(self):
        """
        Toggles the visibility of distance configuration sliders.
        """
        if self.enable_distance_var.get():
            self.distance_frame.pack(side=tk.TOP,
                                     fill='x',
                                     expand=True,
                                     pady=5)
        else:
            self.distance_frame.pack_forget()
            # Reset distances if toggle is off
            self.dots_config.distance_min = ''
            self.dots_config.distance_max = ''
            self.min_distance_var.set(0)
            self.max_distance_var.set(0)

    def draw_dots(self, points):
        """
        Draws crosses on the canvas at the given points and red lines between each successive pair of points.
        """
        # Clear previous dots and lines
        for item in self.dot_items:
            self.canvas.delete(item)
        self.dot_items.clear()

        # Define cross properties
        cross_size = self.dots_config.dot_control.radius
        cross_color = "black"  # You can make this customizable if needed
        line_color = "red"  # Color for the lines between points

        for point in points:
            x, y = point
            # Apply scaling
            x_scaled = x * self.scale
            y_scaled = y * self.scale

            # Draw the cross
            cross_line1 = self.canvas.create_line(x_scaled - cross_size,
                                                  y_scaled,
                                                  x_scaled + cross_size,
                                                  y_scaled,
                                                  fill=cross_color)
            cross_line2 = self.canvas.create_line(x_scaled,
                                                  y_scaled - cross_size,
                                                  x_scaled,
                                                  y_scaled + cross_size,
                                                  fill=cross_color)

            self.dot_items.append(cross_line1)
            self.dot_items.append(cross_line2)

        # Draw lines between successive points
        for i in range(len(points) - 1):
            x1, y1 = points[i]
            x2, y2 = points[i + 1]
            # Apply scaling
            x1_scaled = x1 * self.scale
            y1_scaled = y1 * self.scale
            x2_scaled = x2 * self.scale
            y2_scaled = y2 * self.scale

            line = self.canvas.create_line(x1_scaled,
                                           y1_scaled,
                                           x2_scaled,
                                           y2_scaled,
                                           fill=line_color)
            self.dot_items.append(line)

    def on_close(self):
        """
        Handles the closing of the TestValuesWindow.
        Applies the current epsilon value to the main GUI's input field for epsilon.
        """
        # Apply the current epsilon value to the main GUI's input field for epsilon
        self.dots_config.epsilon = self.epsilon_var.get()
        if self.enable_distance_var.get():
            self.dots_config.distance_max = self.max_distance_var.get()
            self.dots_config.distance_min = self.min_distance_var.get()

        # Close the TestValuesWindow
        self.window.destroy()
