# gui/test_values_window.py

import tkinter as tk
from tkinter import Toplevel, Canvas, Frame, Scrollbar, Button, messagebox
from tkinter import ttk
from PIL import Image, ImageFont, ImageDraw, ImageTk
import platform
import os
from image_discretization import ImageDiscretization

# Import the Tooltip class from tooltip.py
from gui.tooltip import Tooltip
import utils


class TestValuesWindow:

    def __init__(self, master, background_image, initial_epsilon=0.0001):
        """
        Initializes the TestValuesWindow to allow testing different epsilon values.

        Parameters:
        - master: The parent Tkinter window.
        - background_image: PIL Image object to be displayed as the background.
        - initial_epsilon: The initial epsilon value to display or use.
        """
        self.master = master
        self.background_image = background_image.copy().convert("RGBA")
        self.initial_epsilon = initial_epsilon

        # Initialize background opacity
        self.bg_opacity = 0.5  # Default opacity

        # image_discretization = ImageDiscretization(input_path,
        #                                            args.shapeDetection.lower(),
        #                                            args.thresholdBinary, False)
        # self.contour = image_discretization.discretize_image()

        # Determine the available resampling method
        try:
            self.resample_method = Image.Resampling.LANCZOS
        except AttributeError:
            self.resample_method = Image.ANTIALIAS  # For older Pillow versions

        # Create a new top-level window
        self.window = Toplevel(master)
        self.window.title("Test Epsilon Values")
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

        # Bind mouse events for dragging (if needed in future enhancements)
        # Currently, no draggable items

        # Draw the background image
        self.background_photo = None
        self.draw_background()

        # Create a frame for opacity slider
        controls_frame = Frame(self.main_frame,
                               bg='#b5cccc',
                               bd=2,
                               relief='groove',
                               padx=10,
                               pady=10)
        controls_frame.grid(row=1, column=0, sticky='ew', padx=10, pady=10)

        # Label for Opacity
        opacity_label = tk.Label(controls_frame,
                                 text="Opacity:",
                                 bg='#b5cccc',
                                 font=("Helvetica", 12, "bold"))
        opacity_label.pack(side=tk.TOP, anchor='w')

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

        # Label above the opacity slider (Assuming "Given" was a typo, using "Background Opacity")
        background_opacity_label = tk.Label(controls_frame,
                                            text="Background Opacity:",
                                            bg='#b5cccc',
                                            font=("Helvetica", 10, "bold"))
        background_opacity_label.pack(side=tk.TOP, anchor='w', pady=(10, 0))

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

    def update_scrollregion(self):
        """
        Updates the scroll region of the canvas based on the current scale.
        """
        scaled_width = self.canvas_width * self.scale
        scaled_height = self.canvas_height * self.scale
        self.canvas.config(scrollregion=(0, 0, scaled_width, scaled_height))

    def on_close(self):
        """
        Handles the closing of the TestValuesWindow.
        """
        self.window.destroy()
