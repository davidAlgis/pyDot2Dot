# gui/main_gui.py

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
import sys
import threading
import platform
from gui.image_canvas import ImageCanvas
import utils
from PIL import Image, ImageTk
import cv2
import matplotlib.pyplot as plt
import numpy as np
import time
from processing import process_single_image
from gui.tooltip import Tooltip
from gui.edit_window import EditWindow
from gui.multiple_contours_window import MultipleContoursWindow
from gui.error_window import ErrorWindow
from gui.test_values_window import TestValuesWindow
from gui.shape_vis_window import ShapeVisWindow
import traceback
import config
from dot import Dot
from dots_config import DotsConfig


class DotToDotGUI:

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Dot to Dot Processor")
        self.maximize_window()  # Maximize the window on startup
        self.debounce_resize_id = None  # For debouncing resize events
        self.processed_image = None  # Store the processed image
        self.combined_image = None  # Store the combined image with background
        self.display_combined = tk.BooleanVar(
            value=False)  # State of the toggle
        self.create_widgets()
        self.diagonal_length = None  # To store image diagonal
        self.image_width, self.image_height = None, None
        self.contours_windows = [
        ]  # Initialize a list to hold multiple contour windows
        self.invalid_indices = []
        self.processed_dot_radius = -1
        self.processed_font_size = -1
        self.has_edit = False
        self.has_process = False
        # the dot that will serve as the reference dot for new one
        # it will be updated when clicking on process
        self.dots_config = None
        # Bind the close event to a custom handler
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def on_close(self):
        """
        Handles the closing of the main window. If there are unsaved edits,
        warns the user that unsaved changes will be lost.
        """
        if self.has_edit or self.has_process:
            # Show a confirmation dialog
            response = messagebox.askyesnocancel(
                "Unsaved Changes",
                "You have unsaved changes. Do you want to exit without saving?",
            )
            if response:  # User chose 'Yes'
                self.root.destroy()
            elif response is None:  # User chose 'Cancel'
                return
        else:
            # No unsaved changes, proceed with closing
            self.root.destroy()

    def maximize_window(self):
        """
        Maximizes the window based on the operating system.
        """
        os_name = platform.system()
        if os_name == 'Windows':
            self.root.state('zoomed')
        elif os_name == 'Darwin':  # macOS
            self.root.attributes('-zoomed', True)
        else:  # Linux and others
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            self.root.geometry(f"{screen_width}x{screen_height}")

    def create_widgets(self):
        # Configure grid layout for the main window
        self.root.columnconfigure(0, weight=1)
        self.root.columnconfigure(1, weight=1)
        self.root.rowconfigure(0, weight=1)

        # Left Frame for Controls
        control_frame = ttk.Frame(self.root)
        control_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        control_frame.columnconfigure(0, weight=1)
        # Allow parameters frame to expand
        control_frame.rowconfigure(
            14, weight=1)  # Adjusted row index based on added widgets

        # Input Selection
        input_frame = ttk.LabelFrame(control_frame, text="Input")
        input_frame.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        input_frame.columnconfigure(0, weight=1)
        self.input_path = tk.StringVar(value=config.DEFAULTS["input"])
        self.output_path = tk.StringVar(
            value=config.DEFAULTS["output"] if config.
            DEFAULTS["output"] else 'input_dotted.png')

        self.input_entry = ttk.Entry(input_frame,
                                     textvariable=self.input_path,
                                     width=50)
        self.input_entry.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        ttk.Button(input_frame, text="Browse",
                   command=self.browse_input).grid(row=0,
                                                   column=1,
                                                   padx=5,
                                                   pady=5)

        # Add Tooltip for Input Selection
        Tooltip(
            self.input_entry,
            "Enter the path to the input image or directory containing images."
        )
        Tooltip(input_frame.children['!button'],
                "Browse to select an input image file or folder.")

        # Output Selection
        output_frame = ttk.LabelFrame(control_frame, text="Output")
        output_frame.grid(row=1, column=0, padx=5, pady=5, sticky="ew")
        output_frame.columnconfigure(0, weight=1)

        self.output_entry = ttk.Entry(output_frame,
                                      textvariable=self.output_path,
                                      width=50)
        self.output_entry.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        ttk.Button(output_frame, text="Browse",
                   command=self.browse_output).grid(row=0,
                                                    column=1,
                                                    padx=5,
                                                    pady=5)

        # Add Tooltip for Output Selection
        Tooltip(
            self.output_entry,
            "Enter the path to save the processed image or specify an output directory."
        )
        Tooltip(output_frame.children['!button'],
                "Browse to select an output folder.")

        # Parameters Frame
        params_frame = ttk.LabelFrame(control_frame, text="Parameters")
        params_frame.grid(row=2, column=0, padx=5, pady=5, sticky="ew")
        params_frame.columnconfigure(1, weight=1)

        # Shape Detection
        shape_combo_label = ttk.Label(params_frame, text="Shape Detection:")
        shape_combo_label.grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.shape_detection = tk.StringVar(
            value=config.DEFAULTS["shapeDetection"])
        shape_combo = ttk.Combobox(params_frame,
                                   textvariable=self.shape_detection,
                                   values=["Contour", "Path"],
                                   state="readonly")
        shape_combo.grid(row=0, column=1, padx=5, pady=5, sticky="w")

        # Add "Visualize" Button
        visualize_button = ttk.Button(params_frame,
                                      text="Visualize",
                                      command=self.open_shape_vis_window)
        visualize_button.grid(row=0, column=2, padx=5, pady=5, sticky="w")
        Tooltip(
            shape_combo,
            "Select the method for shape detection: 'Contour' for contour-based or 'Path' for skeleton-based detection."
        )
        Tooltip(
            shape_combo_label,
            "Select the method for shape detection: 'Contour' for contour-based or 'Path' for skeleton-based detection."
        )

        # Number of Points
        num_points_label = ttk.Label(params_frame, text="Number of Points:")
        num_points_label.grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.num_points = tk.StringVar(value=str(config.DEFAULTS["numPoints"]))
        num_points_entry = ttk.Entry(params_frame,
                                     textvariable=self.num_points)
        num_points_entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        Tooltip(
            num_points_entry,
            "Specify the desired number of points in the simplified path (can be left empty)."
        )
        Tooltip(
            num_points_label,
            "Specify the desired number of points in the simplified path (can be left empty)."
        )

        # Epsilon
        epsilon_entry_label = ttk.Label(params_frame, text="Epsilon:")
        epsilon_entry_label.grid(row=2, column=0, padx=5, pady=5, sticky="e")
        self.epsilon = tk.DoubleVar(value=config.DEFAULTS["epsilon"])
        epsilon_entry = ttk.Entry(params_frame, textvariable=self.epsilon)
        epsilon_entry.grid(row=2, column=1, padx=5, pady=5, sticky="w")
        Tooltip(
            epsilon_entry,
            "Set the epsilon for path approximation. Smaller values preserve more detail."
        )
        Tooltip(
            epsilon_entry_label,
            "Set the epsilon for path approximation. Smaller values preserve more detail."
        )

        # Add "Test Values" Button
        test_values_button = ttk.Button(params_frame,
                                        text="Test Values",
                                        command=self.open_test_values_window)
        test_values_button.grid(row=2, column=2, padx=5, pady=5, sticky="w")
        Tooltip(
            test_values_button,
            "Open a window to test different epsilon values and see their effect on sampling."
        )
        # Distance
        distance_min_label = ttk.Label(params_frame, text="Distance Min:")
        distance_min_label.grid(row=3, column=0, padx=5, pady=5, sticky="e")
        self.distance_min = tk.StringVar(value=config.DEFAULTS["distance"][0])
        distance_min_entry = ttk.Entry(params_frame,
                                       textvariable=self.distance_min)
        distance_min_entry.grid(row=3,
                                column=1,
                                padx=(5, 0),
                                pady=5,
                                sticky="w")
        Tooltip(
            distance_min_entry,
            "Define the minimum distance between points, either in pixels or as a percentage (e.g., 10% or 5)."
        )
        Tooltip(
            distance_min_label,
            "Define the minimum distance between points, either in pixels or as a percentage (e.g., 10% or 5)."
        )

        distance_max_label = ttk.Label(params_frame, text="Distance Max:")
        distance_max_label.grid(row=4, column=0, padx=5, pady=5, sticky="e")
        self.distance_max = tk.StringVar(value=config.DEFAULTS["distance"][1])
        distance_max_entry = ttk.Entry(params_frame,
                                       textvariable=self.distance_max)
        distance_max_entry.grid(row=4,
                                column=1,
                                padx=(5, 0),
                                pady=5,
                                sticky="w")
        Tooltip(
            distance_max_entry,
            "Define the maximum distance between points, either in pixels or as a percentage (e.g., 50% or 20)."
        )
        Tooltip(
            distance_max_label,
            "Define the maximum distance between points, either in pixels or as a percentage (e.g., 50% or 20)."
        )

        # Font
        font_label = ttk.Label(params_frame, text="Font:")
        font_label.grid(row=5, column=0, padx=5, pady=5, sticky="e")
        self.font = tk.StringVar(value=config.DEFAULTS["font"])
        font_entry = ttk.Entry(params_frame, textvariable=self.font)
        font_entry.grid(row=5, column=1, padx=5, pady=5, sticky="w")
        Tooltip(
            font_entry,
            "Specify the font file for labeling points (e.g., Arial.ttf). The font should be located in C:\\Windows\\Fonts."
        )
        Tooltip(
            font_label,
            "Specify the font file for labeling points (e.g., Arial.ttf). The font should be located in C:\\Windows\\Fonts."
        )

        # Font Size
        font_size_label = ttk.Label(params_frame, text="Font Size:")
        font_size_label.grid(row=6, column=0, padx=5, pady=5, sticky="e")
        self.font_size = tk.StringVar(value=config.DEFAULTS["fontSize"])
        font_size_entry = ttk.Entry(params_frame, textvariable=self.font_size)
        font_size_entry.grid(row=6, column=1, padx=5, pady=5, sticky="w")
        Tooltip(
            font_size_entry,
            "Set the font size for labels, either in pixels or as a percentage of the image diagonal (e.g., 12 or 10%)."
        )
        Tooltip(
            font_size_label,
            "Set the font size for labels, either in pixels or as a percentage of the image diagonal (e.g., 12 or 10%)."
        )

        # Font Color
        font_color_label = ttk.Label(params_frame, text="Font Color (RGBA):")
        font_color_label.grid(row=7, column=0, padx=5, pady=5, sticky="e")
        self.font_color = tk.StringVar(
            value=','.join(map(str, config.DEFAULTS["fontColor"])))
        self.font_color_entry = ttk.Entry(params_frame,
                                          textvariable=self.font_color)
        self.font_color_entry.grid(row=7,
                                   column=1,
                                   padx=(5, 0),
                                   pady=5,
                                   sticky="w")
        Tooltip(
            self.font_color_entry,
            "Set the font color for labels in RGBA format (e.g., 255,0,0,255 for red)."
        )
        Tooltip(
            font_color_label,
            "Set the font color for labels in RGBA format (e.g., 255,0,0,255 for red)."
        )

        # Add Color Box for Font Color
        self.font_color_box = tk.Label(params_frame,
                                       bg=self.get_hex_color(
                                           self.font_color.get()),
                                       width=3,
                                       relief="sunken")
        self.font_color_box.grid(row=7, column=2, padx=5, pady=5, sticky="w")
        Tooltip(self.font_color_box,
                "Visual representation of the selected font color.")

        # Trace the font_color variable to update the color box
        self.font_color.trace_add(
            'write', lambda *args: self.update_color_box(
                self.font_color, self.font_color_box))

        # Dot Color
        dot_color_label = ttk.Label(params_frame, text="Dot Color (RGBA):")
        dot_color_label.grid(row=8, column=0, padx=5, pady=5, sticky="e")
        self.dot_color = tk.StringVar(
            value=','.join(map(str, config.DEFAULTS["dotColor"])))
        self.dot_color_entry = ttk.Entry(params_frame,
                                         textvariable=self.dot_color)
        self.dot_color_entry.grid(row=8,
                                  column=1,
                                  padx=(5, 0),
                                  pady=5,
                                  sticky="w")
        Tooltip(
            self.dot_color_entry,
            "Set the color for dots in RGBA format (e.g., 0,255,0,255 for green)."
        )
        Tooltip(
            dot_color_label,
            "Set the color for dots in RGBA format (e.g., 0,255,0,255 for green)."
        )

        # Add Color Box for Dot Color
        self.dot_color_box = tk.Label(params_frame,
                                      bg=self.get_hex_color(
                                          self.dot_color.get()),
                                      width=3,
                                      relief="sunken")
        self.dot_color_box.grid(row=8, column=2, padx=5, pady=5, sticky="w")
        Tooltip(self.dot_color_box,
                "Visual representation of the selected dot color.")

        # Trace the dot_color variable to update the color box
        self.dot_color.trace_add(
            'write', lambda *args: self.update_color_box(
                self.dot_color, self.dot_color_box))

        # Radius
        radius_label = ttk.Label(params_frame, text="Radius:")
        radius_label.grid(row=9, column=0, padx=5, pady=5, sticky="e")
        self.radius = tk.StringVar(value=config.DEFAULTS["radius"])
        radius_entry = ttk.Entry(params_frame, textvariable=self.radius)
        radius_entry.grid(row=9, column=1, padx=5, pady=5, sticky="w")
        Tooltip(
            radius_entry,
            "Set the radius of the points, either in pixels or as a percentage of the image diagonal (e.g., 12 or 8%)."
        )
        Tooltip(
            radius_label,
            "Set the radius of the points, either in pixels or as a percentage of the image diagonal (e.g., 12 or 8%)."
        )

        # DPI
        dpi_label = ttk.Label(params_frame, text="DPI:")
        dpi_label.grid(row=10, column=0, padx=5, pady=5, sticky="e")
        self.dpi = tk.IntVar(value=config.DEFAULTS["dpi"])
        dpi_entry = ttk.Entry(params_frame, textvariable=self.dpi)
        dpi_entry.grid(row=10, column=1, padx=5, pady=5, sticky="w")
        Tooltip(dpi_entry, "Set the DPI (Dots Per Inch) of the output image.")
        Tooltip(dpi_label, "Set the DPI (Dots Per Inch) of the output image.")

        # Threshold Binary
        threshold_max_label = ttk.Label(params_frame,
                                        text="Threshold Binary (min max):")
        threshold_max_label.grid(row=11, column=0, padx=5, pady=5, sticky="e")
        self.threshold_min = tk.IntVar(
            value=config.DEFAULTS["thresholdBinary"][0])
        self.threshold_max = tk.IntVar(
            value=config.DEFAULTS["thresholdBinary"][1])
        threshold_min_entry = ttk.Entry(params_frame,
                                        textvariable=self.threshold_min,
                                        width=5)
        threshold_min_entry.grid(row=11,
                                 column=1,
                                 padx=(5, 0),
                                 pady=5,
                                 sticky="w")
        threshold_max_entry = ttk.Entry(params_frame,
                                        textvariable=self.threshold_max,
                                        width=5)
        threshold_max_entry.grid(row=11,
                                 column=1,
                                 padx=(60, 5),
                                 pady=5,
                                 sticky="w")
        Tooltip(
            threshold_max_label,
            "Set the minimum/maximum threshold value for binary thresholding.")
        Tooltip(threshold_min_entry,
                "Set the minimum threshold value for binary thresholding.")
        Tooltip(threshold_max_entry,
                "Set the maximum threshold value for binary thresholding.")

        # Display Output Checkbox
        self.display_output = tk.BooleanVar(
            value=config.DEFAULTS["displayOutput"])
        display_output_cb = ttk.Checkbutton(params_frame,
                                            text="Display Output",
                                            variable=self.display_output)
        display_output_cb.grid(row=12, column=0, padx=5, pady=5, sticky="w")
        Tooltip(
            display_output_cb,
            "Toggle whether to display the output image after processing.")

        # Verbose Checkbox
        self.verbose = tk.BooleanVar(value=config.DEFAULTS["verbose"])
        verbose_cb = ttk.Checkbutton(params_frame,
                                     text="Verbose",
                                     variable=self.verbose)
        verbose_cb.grid(row=13, column=0, padx=5, pady=5, sticky="w")
        Tooltip(
            verbose_cb,
            "Toggle verbose mode to display progress messages during processing."
        )

        # Process Button
        process_button = ttk.Button(control_frame,
                                    text="Process",
                                    command=self.process_threaded)
        process_button.grid(row=3, column=0, padx=5, pady=10, sticky="ew")
        Tooltip(
            process_button,
            "Click to start processing the selected image(s) with the specified parameters."
        )

        # Save Button
        self.save_button = ttk.Button(control_frame,
                                      text="Save",
                                      command=self.save_output_image,
                                      state="disabled")  # Initially disabled
        self.save_button.grid(row=4, column=0, padx=5, pady=10, sticky="ew")
        Tooltip(
            self.save_button,
            "Click to save the processed output image. Enabled after processing."
        )

        # Progress Bar
        self.progress = ttk.Progressbar(control_frame, mode='indeterminate')
        self.progress.grid(row=5, column=0, padx=5, pady=(0, 10), sticky="ew")
        Tooltip(self.progress, "Indicates the processing progress.")

        # Right Frame for Image Previews (Input and Output Side by Side)
        preview_frame = ttk.Frame(self.root)
        preview_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        preview_frame.columnconfigure(0, weight=1)
        preview_frame.columnconfigure(1, weight=1)
        preview_frame.rowconfigure(0, weight=1)

        # Input Image Preview using ImageCanvas
        input_preview = ttk.LabelFrame(preview_frame,
                                       text="Input Image Preview")
        input_preview.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        input_preview.columnconfigure(0, weight=1)
        input_preview.rowconfigure(0, weight=1)

        self.input_canvas = ImageCanvas(input_preview, bg="white")

        # Add Tooltip for Input Image Preview
        Tooltip(input_preview,
                "Displays a preview of the selected input image.")

        # Output Image Preview using ImageCanvas
        output_preview = ttk.LabelFrame(preview_frame,
                                        text="Output Image Preview")
        output_preview.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")
        output_preview.columnconfigure(0, weight=1)
        output_preview.rowconfigure(0, weight=1)

        self.output_canvas = ImageCanvas(output_preview, bg="white")

        # Add Tooltip for Output Image Preview
        Tooltip(output_preview,
                "Displays a preview of the processed output image.")

        # Initialize image attributes
        self.input_photo = None
        self.output_photo = None
        self.original_input_image = None
        self.original_output_image = None

        # Toggle Button to switch between processed and combined image
        toggle_button = ttk.Checkbutton(output_preview,
                                        text="Show Combined Image",
                                        variable=self.display_combined,
                                        command=self.toggle_image_display)
        toggle_button.pack(padx=5, pady=5, anchor="n")
        # Add Tooltip for Output Image Preview
        Tooltip(toggle_button,
                "Displays a comparison when linked above input image.")

        # Add Pencil Button with Icon
        pencil_icon_path = os.path.join(
            "src", "gui", "icons", "pencil.png")  # Adjust the path as needed
        if os.path.exists(pencil_icon_path):
            try:
                pencil_image = Image.open(pencil_icon_path).resize(
                    (24, 24), Image.Resampling.LANCZOS)
            except AttributeError:
                # For older Pillow versions
                pencil_image = Image.open(pencil_icon_path).resize(
                    (24, 24), Image.ANTIALIAS)
            self.pencil_photo = ImageTk.PhotoImage(pencil_image)
            self.edit_button = ttk.Button(
                output_preview,
                image=self.pencil_photo,
                command=self.open_edit_window,
                state="disabled"  # Initially disabled
            )
            self.edit_button.image = self.pencil_photo  # Keep a reference
            self.edit_button.place(
                relx=1.0, rely=1.0, anchor="se", x=-10,
                y=-10)  # Position at bottom-right with some padding
            Tooltip(self.edit_button, "Edit Dots and Labels")
        else:
            print(
                f"Pencil icon not found at {pencil_icon_path}. Please ensure the icon exists."
            )

        # Setup tracing for parameters to update overlay lines
        self.setup_traces()

    def toggle_image_display(self):
        """
        Toggles the output canvas between displaying the processed image and the combined image.
        """
        if self.display_combined.get() and self.combined_image is not None:
            # Display the combined image with background and lines
            self.output_canvas.load_image(Image.fromarray(self.combined_image))
        elif self.processed_image is not None:
            # Display the original processed image
            pil_image = Image.fromarray(
                cv2.cvtColor(self.processed_image, cv2.COLOR_BGRA2RGBA
                             ) if self.processed_image.shape[2] ==
                4 else cv2.cvtColor(self.processed_image, cv2.COLOR_BGR2RGB))
            self.output_canvas.load_image(pil_image)

    def open_test_values_window(self):
        """
        Opens the TestValuesWindow to allow testing different epsilon values.
        """
        # Retrieve the current input image to use as background
        if self.original_input_image:
            background_image = self.original_input_image
        else:
            messagebox.showerror("Error", "No input image available to test.")
            return

        # Retrieve the current epsilon value
        current_epsilon = self.epsilon.get()
        dot_radius = self.radius.get()
        threshold_binary = [self.threshold_min.get(), self.threshold_max.get()]
        shape_detection = self.shape_detection.get()
        input_path = self.input_path.get()
        # Initialize and open the TestValuesWindow

        TestValuesWindow(self.root,
                         input_path,
                         shape_detection,
                         threshold_binary,
                         dot_radius,
                         background_image=background_image,
                         initial_epsilon=current_epsilon,
                         main_gui=self)

    def setup_traces(self):
        """
        Sets up trace callbacks for parameters to update overlay lines when they change.
        """
        self.radius.trace_add("write",
                              lambda *args: self.update_overlay_lines())
        self.distance_min.trace_add("write",
                                    lambda *args: self.update_overlay_lines())
        self.distance_max.trace_add("write",
                                    lambda *args: self.update_overlay_lines())
        self.font_size.trace_add("write",
                                 lambda *args: self.update_overlay_lines())

    def browse_input(self):
        # Allow selecting a file or directory
        file_path = filedialog.askopenfilename(title="Select Input Image",
                                               filetypes=[
                                                   ("Image Files",
                                                    "*.png;*.jpg;*.jpeg")
                                               ])
        if file_path:
            self.input_path.set(file_path)
            # Automatically set output path based on input path
            base, ext = os.path.splitext(file_path)
            default_output = f"{base}_dotted{ext}"
            self.output_path.set(default_output)
            # Load and store the original input image
            self.original_input_image = utils.load_image(file_path)
            # Display the selected image on input canvas
            if self.original_input_image:
                self.image_width, self.image_height = self.input_canvas.load_image(
                    self.original_input_image)
                # Compute and store diagonal length based on processed_image
                self.processed_image = self.original_input_image
                image_np = np.array(self.original_input_image)
                self.diagonal_length = utils.compute_image_diagonal(image_np)
                # Update overlay lines
                self.update_overlay_lines()
            # Clear output preview when a new input is selected
            self.clear_output_image()
            # Disable the save button since new input is selected
            self.save_button.config(state="disabled")
            # Disable the edit button since new input needs to be processed
            self.edit_button.config(state="disabled")
        else:
            # If not a file, try selecting a directory
            dir_path = filedialog.askdirectory(title="Select Input Folder")
            if dir_path:
                self.input_path.set(dir_path)
                # Set output directory same as input directory
                self.output_path.set(dir_path)
                # Clear the image preview since multiple images are selected
                self.clear_input_image()
                # Clear output preview
                self.clear_output_image()
                # Disable the save button
                self.save_button.config(state="disabled")
                # Disable the edit button since new input needs to be processed
                self.edit_button.config(state="disabled")

    def browse_output(self):
        path = filedialog.askdirectory(title="Select Output Folder")
        if path:
            self.output_path.set(path)

    def process_threaded(self):
        if self.has_edit:
            # Call `on_process_after_edit` and pass a callback to continue processing
            self.on_process_after_edit(self._start_process)
        else:
            self._start_process()

    def _start_process(self):
        threading.Thread(target=self.process, daemon=True).start()

    def process(self):
        start_time = time.time()

        # Disable the process button and start the progress bar
        self.root.after(0, lambda: self.set_processing_state(True))

        try:
            # Create a mock argparse.Namespace object
            class Args:
                pass

            self.has_process = True
            # we configure dots_config directly from this main_gui instance
            self.dots_config = DotsConfig.main_gui_to_dots_config(self)
            # TODO add check here

            # Processing a single image
            self.processed_image, elapsed_time, self.processed_dots, have_multiple_contours = process_single_image(
                self.dots_config)
            if have_multiple_contours:
                self.handle_multiple_contours(input_path, self.processed_dots,
                                              labels)

            # Post-processing steps
            end_time = time.time()
            elapsed_time = end_time - start_time

            # Display results
            if self.processed_image is not None:

                # Convert the image to PIL Image for display
                self.original_output_image = utils.image_to_pil_rgb(
                    self.processed_image)
                self.root.after(
                    0, lambda: self.output_canvas.load_image(
                        self.original_output_image))
                self.root.after(
                    0, lambda: self.save_button.config(state="normal"))
                self.root.after(
                    0, lambda: self.edit_button.config(state="normal"))

            print(f"Processing completed in {elapsed_time:.2f} seconds")

        except Exception as errorGUI:
            # Capture the full stack trace
            stack_trace = traceback.format_exc()
            # Display the stack trace in a separate window using the ErrorWindow class
            self.root.after(0, lambda: ErrorWindow(self.root, stack_trace))
        finally:
            # Re-enable the process button and stop the progress bar
            self.root.after(0, lambda: self.set_processing_state(False))

    def show_warning_contours(self, contours_window):
        if messagebox.showwarning(
                "Warning",
                "Find multiple contours. We process only the largest one."
        ) == "OK":
            contours_window.window.attributes("-topmost", True)
            contours_window.window.focus_force()  # Focus on the window

    def handle_multiple_contours(self, image_path, dots, labels):

        # Open the MultipleContoursWindow to handle multiple contours
        contours_window = MultipleContoursWindow(self.root, image_path, dots)
        self.root.after(0, self.show_warning_contours(contours_window))

        # # Bring the window to the foreground
        contours_window.window.attributes("-topmost", True)
        contours_window.window.lift()
        contours_window.window.focus_force()  # Focus on the window

        self.contours_windows.append(contours_window)  # Maintain reference

    def set_processing_state(self, is_processing):
        if is_processing:
            self.root.config(cursor="wait")
            self.progress.start()
            # Disable interactive widgets to prevent user actions during processing
            for child in self.root.winfo_children():
                self.disable_widget(child)
        else:
            self.root.config(cursor="")
            self.progress.stop()
            # Re-enable interactive widgets after processing
            for child in self.root.winfo_children():
                self.enable_widget(child)

    def disable_widget(self, widget):
        """
        Recursively disables widgets that support the 'state' attribute.
        """
        try:
            widget_type = widget.winfo_class()
            if widget_type in ["Button", "Entry", "Combobox", "Checkbutton"]:
                widget.config(state='disabled')
        except tk.TclError:
            pass  # Some widgets might not support 'state'

        # Recursively disable child widgets
        for child in widget.winfo_children():
            self.disable_widget(child)

    def enable_widget(self, widget):
        """
        Recursively enables widgets that support the 'state' attribute.
        """
        try:
            widget_type = widget.winfo_class()
            if widget_type in ["Button", "Entry", "Combobox", "Checkbutton"]:
                widget.config(state='normal')
        except tk.TclError:
            pass  # Some widgets might not support 'state'

        # Recursively enable child widgets
        for child in widget.winfo_children():
            self.enable_widget(child)

    def display_image(self, image_path, is_input=True):
        """
        Displays the image in the specified canvas (input or output).
        """
        if not os.path.isfile(image_path):
            messagebox.showerror("Error",
                                 f"Image file '{image_path}' does not exist.")
            return

        pil_image = utils.load_image(image_path)
        if pil_image:
            # Get the target size based on the canvas dimensions
            canvas = self.input_canvas if is_input else self.output_canvas
            target_size = (canvas.winfo_width(), canvas.winfo_height())

            if target_size[0] == 1 and target_size[1] == 1:
                # Canvas might not be fully initialized yet
                self.root.after(
                    100,
                    lambda: self.display_image(image_path, is_input=is_input))
                return

            photo = utils.load_image_to_tk(pil_image, target_size)
            if photo:
                if is_input:
                    self.input_photo = photo  # Keep a reference to prevent garbage collection
                    self.input_canvas.canvas.delete("all")
                    self.input_canvas.canvas.create_image(
                        target_size[0] // 2,
                        target_size[1] // 2,
                        image=self.input_photo,
                        anchor="center")
                else:
                    self.output_photo = photo  # Keep a reference to prevent garbage collection
                    self.output_canvas.canvas.delete("all")
                    self.output_canvas.canvas.create_image(
                        target_size[0] // 2,
                        target_size[1] // 2,
                        image=self.output_photo,
                        anchor="center")
        else:
            if is_input:
                self.clear_input_image()
            else:
                self.clear_output_image()

    def display_pil_image(self, pil_image, is_input=True):
        """
        Displays a PIL Image on the specified canvas.
        """
        canvas = self.input_canvas if is_input else self.output_canvas
        target_size = (canvas.canvas.winfo_width(),
                       canvas.canvas.winfo_height())
        photo = utils.load_image_to_tk(pil_image, target_size)
        if photo:
            if is_input:
                self.input_photo = photo  # Keep a reference to prevent garbage collection
                self.input_canvas.canvas.delete("all")
                self.input_canvas.canvas.create_image(target_size[0] // 2,
                                                      target_size[1] // 2,
                                                      image=self.input_photo,
                                                      anchor="center")
            else:
                self.output_photo = photo  # Keep a reference to prevent garbage collection
                self.output_canvas.canvas.delete("all")
                self.output_canvas.canvas.create_image(target_size[0] // 2,
                                                       target_size[1] // 2,
                                                       image=self.output_photo,
                                                       anchor="center")

    def clear_input_image(self):
        self.input_canvas.canvas.delete("all")
        self.input_photo = None
        self.original_input_image = None
        self.diagonal_length = None
        self.input_canvas.overlay_lines.clear()

    def clear_output_image(self):
        self.output_canvas.canvas.delete("all")
        self.output_photo = None
        self.original_output_image = None
        self.processed_image = None  # Clear the processed image
        self.save_button.config(state="disabled")
        self.edit_button.config(
            state="disabled")  # Disable edit button when no image is processed

    def get_hex_color(self, rgba_str):
        """
        Converts RGBA string to HEX, ignoring the alpha channel.
        """
        return utils.rgba_to_hex(rgba_str)

    def update_color_box(self, color_var, color_box):
        """
        Updates the color box based on the RGBA value from the Entry widget.
        """
        rgba_str = color_var.get()
        hex_color = self.get_hex_color(rgba_str)
        color_box.config(bg=hex_color)

    def save_output_image(self):
        if self.processed_image is None:
            messagebox.showerror("Error", "No processed image to save.")
            return

        # Ask the user where to save the image
        save_path = filedialog.asksaveasfilename(defaultextension=".png",
                                                 filetypes=[("PNG files",
                                                             "*.png"),
                                                            ("JPEG files",
                                                             "*.jpg;*.jpeg")],
                                                 title="Save Output Image")
        if save_path:
            try:
                # Save the image using PIL
                self.original_output_image.save(save_path)

                messagebox.showinfo("Success", f"Image saved to {save_path}.")
            except Exception as errorGUI:
                # Capture the full stack trace
                stack_trace = traceback.format_exc()
                # Display the stack trace in a separate window using the ErrorWindow class
                self.root.after(0, lambda: ErrorWindow(self.root, stack_trace))

    def run(self):
        # Bind the resize event to adjust the image previews with debouncing
        self.input_canvas.canvas.bind(
            "<Configure>",
            lambda event: self.debounce_resize(event, is_input=True))
        self.output_canvas.canvas.bind(
            "<Configure>",
            lambda event: self.debounce_resize(event, is_input=False))
        self.root.mainloop()

    def debounce_resize(self, event, is_input=True):
        """
        Debounces the resize event to prevent excessive resizing.
        """
        if self.debounce_resize_id:
            self.root.after_cancel(self.debounce_resize_id)
        self.debounce_resize_id = self.root.after(
            200, lambda: self.update_image_display(event, is_input))

    def update_image_display(self, event, is_input=True):
        """
        Updates the displayed image when the canvas is resized.
        """
        image_path = self.input_path.get(
        ) if is_input else self.output_path.get()
        if os.path.isfile(image_path):
            self.original_input_image = utils.load_image(image_path)
            if self.original_input_image:
                target_size = (
                    self.input_canvas.canvas.winfo_width(),
                    self.input_canvas.canvas.winfo_height()) if is_input else (
                        self.output_canvas.canvas.winfo_width(),
                        self.output_canvas.canvas.winfo_height())
                resized_pil_image = utils.resize_image(
                    self.original_input_image, target_size)
                if is_input:
                    self.image_width, self.image_height = self.input_canvas.load_image(
                        self.original_input_image)
                    self.processed_image = self.original_input_image
                    image_np = np.array(self.original_input_image)
                    self.diagonal_length = utils.compute_image_diagonal(
                        image_np)
                    self.update_overlay_lines()
                else:
                    self.output_canvas.load_image(self.original_input_image)
        else:
            if is_input:
                self.clear_input_image()
            else:
                self.clear_output_image()

    def update_overlay_lines(self):
        """
        Reads the current parameter values, converts them to pixels, and updates the overlay lines.
        """
        if not self.original_input_image or not self.diagonal_length:
            return

        # Parse parameters
        try:
            radius_px = utils.parse_size(self.radius.get(),
                                         self.diagonal_length)
        except:
            radius_px = 10  # default value
        try:
            distance_min_px = utils.parse_size(
                self.distance_min.get(),
                self.diagonal_length) if self.distance_min.get() else 0
        except:
            distance_min_px = 0
        try:
            distance_max_px = utils.parse_size(
                self.distance_max.get(),
                self.diagonal_length) if self.distance_max.get() else 0
        except:
            distance_max_px = 0
        try:
            font_size_px = utils.parse_size(self.font_size.get(),
                                            self.diagonal_length)
        except:
            font_size_px = 10  # default value
        image_diagonal = self.diagonal_length
        canvas_diagonal = (self.input_canvas.canvas.winfo_width()**2 +
                           self.input_canvas.canvas.winfo_height()**2)**0.5

        # Call draw_overlay_lines
        self.input_canvas.draw_overlay_lines(radius_px, distance_min_px,
                                             distance_max_px, font_size_px,
                                             image_diagonal, canvas_diagonal)

    def apply_changes(self, edited_image, updated_dots):
        """
        Receives the edited image from the EditWindow and updates the output canvas.
        """
        # Update the processed_image with the edited image
        self.processed_image = np.array(edited_image)

        # Update the output canvas
        self.original_output_image = edited_image
        self.output_canvas.load_image(edited_image)

        # Optionally, enable the save button if needed
        self.save_button.config(state="normal")
        self.processed_dots = updated_dots

    def open_edit_window(self):
        if not hasattr(self,
                       'processed_image') or self.processed_image is None:
            messagebox.showerror("Error",
                                 "No processed image available to edit.")
            return

        print(f"Edit output...")
        self.has_edit = True
        # Initialize and open the EditWindow with the necessary parameters
        EditWindow(master=self.root,
                   dot_control=self.dots_config.dot_control,
                   dots=self.processed_dots,
                   image_width=self.image_width,
                   image_height=self.image_height,
                   input_image=self.original_input_image,
                   apply_callback=self.apply_changes,
                   invalid_indices=self.invalid_indices)

    def parse_rgba(self, rgba_str):
        """
        Parses an RGBA string and returns a tuple of integers.
        """
        parts = rgba_str.split(',')
        if len(parts) != 4:
            raise ValueError("RGBA must have exactly four components.")
        return tuple(int(part.strip()) for part in parts)

    def open_shape_vis_window(self):
        """
        Opens the ShapeVisWindow to visualize shape detection modes.
        """
        if not self.original_input_image:
            messagebox.showerror(
                "Error", "No input image available for visualization.")
            return

        # Retrieve the current shape detection mode and threshold binary values
        shape_detection_mode = self.shape_detection.get()
        threshold_binary = (self.threshold_min.get(), self.threshold_max.get())
        input_path = self.input_path.get()  # Path to the input image file

        # Open the ShapeVisWindow with the current settings
        ShapeVisWindow(master=self.root,
                       input_path=input_path,
                       shape_detection=shape_detection_mode,
                       threshold_binary=threshold_binary,
                       background_image=self.original_input_image,
                       main_gui=self)

    def on_process_after_edit(self, continue_callback):
        """
        Displays a confirmation dialog when editing changes will be reset by processing.
        """
        # Create a confirmation popup
        popup = tk.Toplevel(self.root)
        popup.title("Confirm Process")
        popup.transient(self.root)  # Set to be on top of the main window
        popup.grab_set()  # Make the popup modal

        # Message Label
        message_label = tk.Label(
            popup,
            text=
            "Processing will reset all unsaved edits. Do you want to continue?"
        )
        message_label.pack(padx=20, pady=20)

        # Button Frame
        button_frame = tk.Frame(popup)
        button_frame.pack(padx=20, pady=10)

        # Yes Button
        yes_button = tk.Button(
            button_frame,
            text="Yes",
            width=10,
            command=lambda:
            [popup.destroy(),
             self.reset_edit_state(),
             continue_callback()])
        yes_button.pack(side=tk.LEFT, padx=5)

        # No Button
        no_button = tk.Button(button_frame,
                              text="No",
                              width=10,
                              command=popup.destroy)
        no_button.pack(side=tk.LEFT, padx=5)

        # Wait for the popup to close before returning
        self.root.wait_window(popup)

    def reset_edit_state(self):
        """
        Resets the editing state after user confirms processing.
        """
        self.has_edit = False  # Reset the edit flag


if __name__ == "__main__":
    app = DotToDotGUI()
    app.run()
