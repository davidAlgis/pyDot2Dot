# gui/test_values_window.py

import tkinter as tk
from tkinter import Toplevel, Canvas, Frame, Scrollbar, Button, messagebox
from tkinter import ttk
from PIL import Image, ImageFont, ImageDraw, ImageTk
import platform
import os
import cv2
import numpy as np
from image_discretization import ImageDiscretization
import threading
# Import the Tooltip class from tooltip.py
from gui.tooltip import Tooltip
import utils
from typing import List, Tuple


class ShapeVisWindow:

    def __init__(self,
                 master,
                 input_path,
                 shape_detection,
                 threshold_binary,
                 background_image,
                 main_gui=None):
        """
        Initializes the TestValuesWindow to allow testing different epsilon values.

        Parameters:
        - master: The parent Tkinter window.
        - input_path: Path to the input image.
        - shape_detection: Method for shape detection ('Contour' or 'Path').
        - threshold_binary: Tuple (min, max) for binary thresholding.
        - dot_radius: Radius of the dots to be displayed (can be a number or percentage string).
        - background_image: PIL Image object to be displayed as the background.
        - initial_epsilon: The initial epsilon value to display or use.
        """
        print("Open shape visualization windows...")

        self.master = master
        self.main_gui = main_gui
        self.input_path = input_path
        self.threshold_binary = threshold_binary
        self.shape_detection = shape_detection
        self.background_image = background_image.copy().convert("RGBA")

        # Initialize background opacity
        self.bg_opacity = 0.5  # Default opacity

        # Initialize ImageDiscretization and compute contour
        image_discretization = ImageDiscretization(input_path,
                                                   shape_detection.lower(),
                                                   threshold_binary, False)
        self.dots = image_discretization.discretize_image()
        self.contour = np.array([dot.position for dot in self.dots],
                                dtype=np.int32)

        # Create a new top-level window
        self.window = Toplevel(master)
        self.window.title("Shape visualization")
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)

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

        # Determine the available resampling method
        try:
            self.resample_method = Image.Resampling.LANCZOS
        except AttributeError:
            self.resample_method = Image.ANTIALIAS  # For older Pillow versions

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

        # Dropdown for shape detection mode
        shape_mode_label = tk.Label(controls_frame,
                                    text="Shape Detection Mode:",
                                    bg='#b5cccc',
                                    font=("Helvetica", 10, "bold"))
        shape_mode_label.pack(side=tk.TOP, anchor='w')

        self.shape_mode_var = tk.StringVar(value=shape_detection)
        shape_mode_dropdown = ttk.Combobox(controls_frame,
                                           textvariable=self.shape_mode_var,
                                           values=["Contour", "Path"],
                                           state="readonly")
        shape_mode_dropdown.pack(side=tk.TOP, fill='x', expand=True, pady=5)
        shape_mode_dropdown.bind("<<ComboboxSelected>>",
                                 self.on_shape_mode_change)
        Tooltip(shape_mode_dropdown,
                "Select shape detection mode to visualize.")

        # Create a progress bar in the controls frame
        self.progress_bar = ttk.Progressbar(controls_frame,
                                            mode='indeterminate')
        self.progress_bar.place(x=30, y=60, width=500)
        self.progress_bar.pack(fill="x", padx=10, pady=(5, 15))

        # Simplify to list of tuples
        points = [(point[0], point[1]) for point in self.contour]

        # Adjust this value to control the minimum distance between points
        self.min_distance = 20
        self.filtered_points = utils.filter_close_points(
            points, self.min_distance)

        self.draw_contour()
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
        scale_factor = min(scale_x, scale_y) * 0.8  # 90% to add padding

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
        self.draw_contour()

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

    def update_contour(self):
        image_discretization = ImageDiscretization(
            self.input_path, self.shape_detection.lower(),
            self.threshold_binary, False)
        self.dots = image_discretization.discretize_image()
        self.contour = np.array([dot.position for dot in self.dots],
                                dtype=np.int32)

        points = [(point[0], point[1])
                  for point in self.contour]  # Simplify to list of tuples
        self.filtered_points = utils.filter_close_points(
            points, self.min_distance)

    def draw_contour(self):
        """
        Draws lines connecting each successive point in the filtered contour.
        Closes the contour if 'Contour' mode is selected.
        """
        # Scale and draw each line segment between successive points
        for i in range(len(self.filtered_points) - 1):
            x1, y1 = int(self.filtered_points[i][0] * self.scale), int(
                self.filtered_points[i][1] * self.scale)
            x2, y2 = int(self.filtered_points[i + 1][0] * self.scale), int(
                self.filtered_points[i + 1][1] * self.scale)
            self.canvas.create_line(x1, y1, x2, y2, fill="red", width=2)

        # Close the contour if in 'Contour' mode
        if self.shape_detection.lower() == 'contour' and len(
                self.filtered_points) > 1:
            x1, y1 = int(self.filtered_points[-1][0] * self.scale), int(
                self.filtered_points[-1][1] * self.scale)
            x2, y2 = int(self.filtered_points[0][0] * self.scale), int(
                self.filtered_points[0][1] * self.scale)
            self.canvas.create_line(x1, y1, x2, y2, fill="red", width=2)

    def on_shape_mode_change(self, event):
        """ Callback to handle changes in the shape detection mode. """
        self.shape_detection = self.shape_mode_var.get()
        self.set_loading_state(True)  # Start loading state

        # Start a new thread to run process_and_redraw
        threading.Thread(target=self.process_and_redraw_threaded).start()

    def process_and_redraw_threaded(self):
        """Run the processing and redraw in a separate thread."""
        self.update_contour(
        )  # Process the contour based on the new shape mode

        # Schedule the redraw and loading state reset on the main thread
        self.window.after(0, self.redraw_canvas)
        self.window.after(0, lambda: self.set_loading_state(False))

    def on_close(self):
        self.main_gui.shape_detection.set(self.shape_detection)
        self.window.destroy()

    def set_loading_state(self, is_loading):
        """ Start or stop the progress bar animation. """
        if is_loading:
            self.progress_bar.start()  # Start loading animation
        else:
            self.progress_bar.stop()  # Stop loading animation
