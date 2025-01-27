# gui/shape_vis_window.py

import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import numpy as np
from dot2dot.image_discretization import ImageDiscretization
import threading
from dot2dot.gui.tooltip import Tooltip
from dot2dot.utils import filter_close_points
from dot2dot.gui.utilities_gui import set_icon
from dot2dot.gui.display_window_base import DisplayWindowBase  # Corrected import
import platform


class ShapeVisWindow(DisplayWindowBase):

    def __init__(self,
                 master,
                 input_path,
                 shape_detection,
                 threshold_binary,
                 background_image,
                 config,
                 main_gui=None):
        """
        Initializes the ShapeVisWindow to allow visualizing different shape detection modes.

        Parameters:
        - master: The parent Tkinter window.
        - input_path: Path to the input image.
        - shape_detection: Method for shape detection ('Contour' or 'Path').
        - threshold_binary: Tuple (min, max) for binary thresholding.
        - background_image: PIL Image object to be displayed as the background.
        - main_gui: Reference to the main GUI instance (optional).
        """
        super().__init__(master,
                         title="Shape Visualization",
                         width=800,
                         height=600,
                         config=config)

        self.window.protocol("WM_DELETE_WINDOW", self.on_close)
        self.main_gui = main_gui
        self.input_path = input_path
        self.threshold_binary = threshold_binary
        self.shape_detection = shape_detection
        self.background_image = background_image.copy().convert("RGBA")

        # Set canvas dimensions
        self.canvas_width, self.canvas_height = self.background_image.size
        self.update_scrollregion(self.canvas_width, self.canvas_height)

        # Initialize variables
        self.bg_opacity = 0.5
        self.image_discretization = None
        self.dots = []
        self.contour = []
        self.filtered_points = []
        self.min_distance = 20  # Minimum distance for point filtering

        # Create controls for opacity and shape detection
        self.create_controls()

        # Start the loading and processing in a separate thread
        self.set_loading_state(True)
        self.load_and_process()

    def load_and_process(self):
        """Load and process the image and shape detection in a separate thread."""
        # Display "Loading..." on the canvas
        self.canvas.delete("all")
        self.canvas.create_text(self.canvas_width / 2,
                                self.canvas_height / 2,
                                text="Loading...",
                                font=("Helvetica", 24, "bold"),
                                fill="gray")

        def process_in_thread():
            try:
                # Heavy initialization
                self.image_discretization = ImageDiscretization(
                    self.input_path, self.shape_detection.lower(),
                    self.threshold_binary, False)
                self.dots = self.image_discretization.discretize_image()
                self.contour = np.array([dot.position for dot in self.dots],
                                        dtype=np.int32)

                points = [(point[0], point[1]) for point in self.contour]
                self.filtered_points = filter_close_points(
                    points, self.min_distance)

                # Once processed, schedule canvas redraw on the main thread
                self.window.after(0, self.redraw_canvas)
                self.window.after(0, self.fit_canvas_to_content)
            except Exception as e:
                self.window.after(
                    0, lambda: messagebox.showerror(
                        "Error",
                        f"Failed to process shape visualization: {str(e)}"))
            finally:
                # Stop progress bar after processing
                self.window.after(0, lambda: self.set_loading_state(False))

        # Start the processing thread
        threading.Thread(target=process_in_thread, daemon=True).start()

    def create_controls(self):
        """
        Creates the control widgets (opacity slider, shape detection dropdown, progress bar).
        """
        # Create a frame for controls (opacity and shape detection sliders)
        controls_frame = ttk.Frame(self.window, padding=10)
        controls_frame.pack(side=tk.BOTTOM, fill=tk.X)

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
                                         text=f"{self.bg_opacity:.2f}")
        self.opacity_display.pack(side=tk.TOP, anchor='w')

        # Dropdown for shape detection mode
        shape_mode_label = ttk.Label(controls_frame,
                                     text="Shape Detection Mode:",
                                     font=("Helvetica", 10, "bold"))
        shape_mode_label.pack(side=tk.TOP, anchor='w')

        self.shape_mode_var = tk.StringVar(value=self.shape_detection)
        shape_mode_dropdown = ttk.Combobox(
            controls_frame,
            textvariable=self.shape_mode_var,
            values=["Automatic", "Contour", "Path"],
            state="readonly")
        shape_mode_dropdown.pack(side=tk.TOP, fill='x', expand=True, pady=5)
        shape_mode_dropdown.bind("<<ComboboxSelected>>",
                                 self.on_shape_mode_change)
        Tooltip(shape_mode_dropdown,
                "Select shape detection mode to visualize.")

        # Create a progress bar in the controls frame
        self.progress_bar = ttk.Progressbar(controls_frame,
                                            mode='indeterminate')
        self.progress_bar.pack(fill="x", padx=10, pady=(5, 15))
        Tooltip(self.progress_bar, "Indicates the processing progress.")

    def redraw_canvas(self):
        """
        Clears and redraws the canvas contents based on the current scale and opacity.
        """
        self.canvas.delete("all")
        self.draw_background()
        self.draw_contour()

    def on_shape_mode_change(self, event):
        """ Callback to handle changes in the shape detection mode. """
        self.shape_detection = self.shape_mode_var.get()
        self.set_loading_state(True)  # Start loading state

        # Start a new thread to run process_and_redraw
        threading.Thread(target=self.process_and_redraw_threaded,
                         daemon=True).start()

    def process_and_redraw_threaded(self):
        """Run the processing and redraw in a separate thread."""
        self.update_contour(
        )  # Process the contour based on the new shape mode

        # Schedule the redraw and loading state reset on the main thread
        self.window.after(0, self.redraw_canvas)
        self.window.after(0, lambda: self.set_loading_state(False))

    def update_contour(self):
        """Update the contour based on the current shape detection mode."""
        self.image_discretization = ImageDiscretization(
            self.input_path, self.shape_detection.lower(),
            self.threshold_binary, False)
        self.dots = self.image_discretization.discretize_image()
        self.contour = np.array([dot.position for dot in self.dots],
                                dtype=np.int32)

        points = [(point[0], point[1])
                  for point in self.contour]  # Simplify to list of tuples
        self.filtered_points = filter_close_points(points, self.min_distance)

    def draw_contour(self):
        """
        Draws lines connecting each successive point in the filtered contour.
        Closes the contour if 'Contour' mode is selected.
        """
        for i in range(len(self.filtered_points) - 1):
            x1, y1 = int(self.filtered_points[i][0] * self.scale), int(
                self.filtered_points[i][1] * self.scale)
            x2, y2 = int(self.filtered_points[i + 1][0] * self.scale), int(
                self.filtered_points[i + 1][1] * self.scale)
            self.canvas.create_line(x1, y1, x2, y2, fill="red", width=2)

        # Close the contour if in 'Contour' mode
        if self.image_discretization.contour_mode_to_use.lower(
        ) == 'contour' and len(self.filtered_points) > 1:
            x1, y1 = int(self.filtered_points[-1][0] * self.scale), int(
                self.filtered_points[-1][1] * self.scale)
            x2, y2 = int(self.filtered_points[0][0] * self.scale), int(
                self.filtered_points[0][1] * self.scale)
            self.canvas.create_line(x1, y1, x2, y2, fill="red", width=2)

    def set_loading_state(self, is_loading):
        """ Start or stop the progress bar animation. """
        if is_loading:
            self.progress_bar.start()  # Start loading animation
        else:
            self.progress_bar.stop()  # Stop loading animation

    def on_close(self):
        """Handle the closing of the ShapeVisWindow."""
        if self.main_gui:
            self.main_gui.shape_detection.set(self.shape_detection)
        self.window.destroy()
