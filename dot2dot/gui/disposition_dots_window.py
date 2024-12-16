"""
Module to display a window to help defined the parameters for dots disposition.
"""

import threading
import tkinter as tk
from tkinter import ttk, messagebox
import numpy as np
import cv2
from dot2dot.image_discretization import ImageDiscretization
from dot2dot.gui.tooltip import Tooltip
from dot2dot.utils import compute_image_diagonal, insert_midpoints, filter_close_points
from dot2dot.gui.display_window_base import DisplayWindowBase  # Corrected import


class DispositionDotsWindow(DisplayWindowBase):
    """
    This class display a window to help defined the parameters for dots disposition.
    """

    def __init__(self, master, dots_config, background_image, main_gui=None):
        """
        Initializes the DispositionDotsWindow to allow testing different epsilon values.

        Parameters:
        - master: The parent Tkinter window.
        - dots_config: Configuration for dots.
        - background_image: PIL Image object to be displayed as the background.
        - main_gui: Reference to the main GUI (optional).
        """
        # Initialize the base class with default width and height
        super().__init__(master,
                         title="Dots Disposition",
                         width=800,
                         height=600)
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)

        self.main_gui = main_gui  # Store the reference to the main GUI
        self.dots_config = dots_config
        self.background_image = background_image.copy().convert("RGBA")
        self.bg_opacity = 0.5  # Default opacity
        # Will be defined later
        self.contour_points = None
        # Set canvas_width and canvas_height based on the background image size
        self.canvas_width, self.canvas_height = self.background_image.size
        self.update_scrollregion(self.canvas_width, self.canvas_height)

        # Create the controls frame for opacity, epsilon, and distance sliders
        self.create_controls()

        # Display "loading..." on the canvas
        self.show_loading_label()

        # Start the loading process in a separate thread
        threading.Thread(target=self.load_and_process, daemon=True).start()

    def show_loading_label(self):
        """
        Displays a "loading..." label centered on the currently visible portion of the canvas.
        """
        self.canvas.delete("all")

        # Get the visible region of the canvas
        canvas_x_start, canvas_x_end = self.canvas.xview()
        canvas_y_start, canvas_y_end = self.canvas.yview()

        # Calculate the visible width and height
        visible_width = (canvas_x_end -
                         canvas_x_start) * self.canvas_width * self.scale
        visible_height = (canvas_y_end -
                          canvas_y_start) * self.canvas_height * self.scale

        # Calculate the top-left corner of the visible region in canvas coordinates
        visible_x0 = canvas_x_start * self.canvas_width * self.scale
        visible_y0 = canvas_y_start * self.canvas_height * self.scale

        # Calculate the center of the visible region
        center_x = visible_x0 + (visible_width / 2)
        center_y = visible_y0 + (visible_height / 2)

        # Place the "loading..." text at the calculated center
        self.canvas.create_text(center_x,
                                center_y,
                                text="loading...",
                                font=("Helvetica", 24, "italic"),
                                fill="gray")

    def load_and_process(self):
        """
        Performs the time-consuming image discretization and contour processing in a separate thread.
        """
        try:
            # Initialize ImageDiscretization and compute contour
            image_discretization = ImageDiscretization(
                self.dots_config.input_path,
                self.dots_config.shape_detection.lower(),
                self.dots_config.threshold_binary, False)
            self.dots = image_discretization.discretize_image()
            self.contour = np.array([dot.position for dot in self.dots],
                                    dtype=np.int32)
            self.contour_points = [(point[0], point[1])
                                   for point in self.contour]

            # Approximate the contour based on epsilon
            approx = cv2.approxPolyDP(
                np.array(self.contour_points, dtype=np.int32),
                self.dots_config.epsilon, True)
            self.current_points = [(point[0][0], point[0][1])
                                   for point in approx]
            self.window.after(0, self.fit_canvas_to_content)

        except Exception as e:
            self.window.after(0, lambda: messagebox.showerror("Error", str(e)))
            self.window.after(0, self.window.destroy)

    def redraw_canvas(self):
        """
        Clears and redraws the canvas contents based on the current scale and opacity.
        """
        self.canvas.delete("all")
        self.draw_background()
        # Redraw the dots
        self.draw_dots(self.current_points)

    def create_controls(self):
        """
        Creates the control widgets (opacity slider, epsilon slider, distance sliders).
        """
        # Create a frame for controls (opacity, epsilon, and distance sliders)
        controls_frame = ttk.Frame(self.window, padding=10)
        controls_frame.pack(side=tk.BOTTOM, fill=tk.X)

        # -------- Background Opacity Controls --------
        # Label for Background Opacity
        background_opacity_label = ttk.Label(controls_frame,
                                             text="Background Opacity:",
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
        self.opacity_display = ttk.Label(controls_frame,
                                         text=f"{self.bg_opacity:.2f}",
                                         font=("Helvetica", 10))
        self.opacity_display.pack(side=tk.TOP, anchor='w')

        # -------- Epsilon Controls --------
        # Separator
        separator = ttk.Separator(controls_frame, orient='horizontal')
        separator.pack(fill='x', pady=10)

        # Label for Epsilon
        epsilon_label = ttk.Label(controls_frame,
                                  text="Epsilon:",
                                  font=("Helvetica", 12, "bold"))
        epsilon_label.pack(side=tk.TOP, anchor='w')

        # Frame to hold the epsilon slider and its labels
        epsilon_frame = ttk.Frame(controls_frame)
        epsilon_frame.pack(side=tk.TOP, fill='x', expand=True, pady=5)

        # Add "more dots" label on the left
        more_dots_label = ttk.Label(epsilon_frame,
                                    text="more dots",
                                    font=("Helvetica", 10))
        more_dots_label.pack(side=tk.LEFT, padx=5)

        # Epsilon slider
        self.epsilon_var = tk.DoubleVar(value=self.dots_config.epsilon)
        epsilon_slider = ttk.Scale(epsilon_frame,
                                   from_=0.1,
                                   to=100.0,
                                   orient=tk.HORIZONTAL,
                                   variable=self.epsilon_var,
                                   command=self.on_epsilon_change)
        epsilon_slider.pack(side=tk.LEFT, fill='x', expand=True)

        # Add "less dots" label on the right
        less_dots_label = ttk.Label(epsilon_frame,
                                    text="less dots",
                                    font=("Helvetica", 10))
        less_dots_label.pack(side=tk.LEFT, padx=5)

        Tooltip(epsilon_slider,
                "Adjust the epsilon value for contour approximation.")

        # Display the current epsilon value
        self.epsilon_display = ttk.Label(
            controls_frame,
            text=f"{self.dots_config.epsilon:.4f}",
            font=("Helvetica", 10))
        self.epsilon_display.pack(side=tk.TOP, anchor='w')

        # -------- Distance Controls --------
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
        self.distance_frame = ttk.Frame(controls_frame)
        if not self.enable_distance_var.get():
            self.distance_frame.pack_forget()
        else:
            self.distance_frame.pack(side=tk.TOP,
                                     fill='x',
                                     expand=True,
                                     pady=5)

        # -------------------- Minimum Distance Slider with Value Display --------------------
        min_distance_label = ttk.Label(self.distance_frame,
                                       text="Minimum Distance:",
                                       font=("Helvetica", 10))
        min_distance_label.pack(side=tk.TOP, anchor='w')

        # Frame for Minimum Distance Slider and Label
        min_distance_display_frame = ttk.Frame(self.distance_frame)
        min_distance_display_frame.pack(side=tk.TOP,
                                        fill='x',
                                        expand=True,
                                        pady=2)

        # Minimum Distance Slider
        self.min_distance_var = tk.DoubleVar(
            value=float(self.dots_config.distance_min or 0))
        min_distance_slider = ttk.Scale(min_distance_display_frame,
                                        from_=0,
                                        to=300,
                                        orient=tk.HORIZONTAL,
                                        variable=self.min_distance_var,
                                        command=self.on_distance_change)
        min_distance_slider.pack(side=tk.LEFT, fill='x', expand=True)

        # Label to Display Current Minimum Distance Value
        self.min_distance_display = ttk.Label(
            min_distance_display_frame,
            text=f"{self.min_distance_var.get():.0f}",
            font=("Helvetica", 10))
        self.min_distance_display.pack(side=tk.RIGHT, padx=5)

        # -------------------- Maximum Distance Slider with Value Display --------------------
        max_distance_label = ttk.Label(self.distance_frame,
                                       text="Maximum Distance:",
                                       font=("Helvetica", 10))
        max_distance_label.pack(side=tk.TOP, anchor='w')

        # Frame for Maximum Distance Slider and Label
        max_distance_display_frame = ttk.Frame(self.distance_frame)
        max_distance_display_frame.pack(side=tk.TOP,
                                        fill='x',
                                        expand=True,
                                        pady=2)

        # Maximum Distance Slider
        self.max_distance_var = tk.DoubleVar(
            value=float(self.dots_config.distance_max or 0))
        max_distance_slider = ttk.Scale(max_distance_display_frame,
                                        from_=10,
                                        to=500,
                                        orient=tk.HORIZONTAL,
                                        variable=self.max_distance_var,
                                        command=self.on_distance_change)
        max_distance_slider.pack(side=tk.LEFT, fill='x', expand=True)

        # Label to Display Current Maximum Distance Value
        self.max_distance_display = ttk.Label(
            max_distance_display_frame,
            text=f"{self.max_distance_var.get():.0f}",
            font=("Helvetica", 10))
        self.max_distance_display.pack(side=tk.RIGHT, padx=5)

        Tooltip(max_distance_slider,
                "Adjust the maximum distance between dots.")
        Tooltip(min_distance_slider,
                "Adjust the minimum distance between dots.")

        # Initialize the dots display
        self.current_points = []  # self.current_points  # Store current points
        self.dot_items = []
        # Adjust the initial view to show all dots and labels
        self.fit_canvas_to_content()

    def on_epsilon_change(self, value):
        """
        Callback function for the epsilon slider.
        Updates the contour approximation and redraws the dots.
        """
        epsilon_slider_value = float(value)
        self.epsilon_display.config(text=f"{epsilon_slider_value:.4f}")
        if not self.contour_points:
            return
        # Approximate the contour based on the new epsilon value
        approx = cv2.approxPolyDP(
            np.array(self.contour_points, dtype=np.int32),
            epsilon_slider_value, True)
        self.current_points = [(point[0][0], point[0][1]) for point in approx]
        # self.current_points = self.current_points

        # Redraw the dots with the new approximation
        self.draw_dots(self.current_points)

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
            self.draw_dots(
                self.current_points)  # Redraw without distance adjustments

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

            self.dot_items.extend([cross_line1, cross_line2])

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
        # Optionally, draw a line closing the contour
        if self.dots_config.shape_detection.lower() == 'contour' and len(
                points) > 1:
            x1, y1 = points[-1]
            x2, y2 = points[0]
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
        Handles the closing of the DispositionDotsWindow.
        Applies the current epsilon and distance values to the main GUI's input fields.
        """
        if self.main_gui:
            self.main_gui.dots_config.epsilon = self.epsilon_var.get()
            self.main_gui.dots_config.distance_min = self.min_distance_var.get(
            )
            self.main_gui.dots_config.distance_max = self.max_distance_var.get(
            )
        self.window.destroy()
