# gui/main_gui.py

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
import sys
import threading
import platform
from gui.image_canvas import ImageCanvas  # Adjusted import
import utils
from PIL import Image, ImageTk
import cv2
import matplotlib.pyplot as plt
import numpy as np
import time
from processing import process_single_image  # Import from processing.py
from gui.tooltip import Tooltip  # New import
from gui.edit_window import EditWindow  # Import EditWindow from edit_window.py


class DotToDotGUI:

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Dot to Dot Processor")
        self.maximize_window()  # Maximize the window on startup
        self.create_widgets()
        self.debounce_resize_id = None  # For debouncing resize events
        self.processed_image = None  # Store the processed image
        self.diagonal_length = None  # To store image diagonal
        self.image_width, self.image_height = None, None

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

        self.input_path = tk.StringVar(value='input.png')  # Set default input
        self.output_path = tk.StringVar(
            value='input_dotted.png')  # Set default output

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
        self.shape_detection = tk.StringVar(value="Contour")
        shape_combo = ttk.Combobox(params_frame,
                                   textvariable=self.shape_detection,
                                   values=["Contour", "Path"],
                                   state="readonly")
        shape_combo.grid(row=0, column=1, padx=5, pady=5, sticky="w")
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
        self.num_points = tk.IntVar(value=200)
        num_points_entry = ttk.Entry(params_frame,
                                     textvariable=self.num_points)
        num_points_entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        Tooltip(
            num_points_entry,
            "Specify the desired number of points in the simplified path.")
        Tooltip(
            num_points_label,
            "Specify the desired number of points in the simplified path.")

        # Distance
        distance_min_label = ttk.Label(params_frame, text="Distance Min:")
        distance_min_label.grid(row=3, column=0, padx=5, pady=5, sticky="e")
        self.distance_min = tk.StringVar(value="25")
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
        self.distance_max = tk.StringVar(value="400")
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
        self.font = tk.StringVar(value="Arial.ttf")
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
        self.font_size = tk.StringVar(value="1%")
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
        self.font_color = tk.StringVar(value="0,0,0,255")
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
        self.dot_color = tk.StringVar(value="0,0,0,255")
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
        self.radius = tk.StringVar(value="12")
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
        self.dpi = tk.IntVar(value=400)
        dpi_entry = ttk.Entry(params_frame, textvariable=self.dpi)
        dpi_entry.grid(row=10, column=1, padx=5, pady=5, sticky="w")
        Tooltip(dpi_entry, "Set the DPI (Dots Per Inch) of the output image.")
        Tooltip(dpi_label, "Set the DPI (Dots Per Inch) of the output image.")

        # Threshold Binary
        threshold_max_label = ttk.Label(params_frame,
                                        text="Threshold Binary (min max):")
        threshold_max_label.grid(row=11, column=0, padx=5, pady=5, sticky="e")
        self.threshold_min = tk.IntVar(value=100)
        self.threshold_max = tk.IntVar(value=255)
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
        self.display_output = tk.BooleanVar(value=True)
        display_output_cb = ttk.Checkbutton(params_frame,
                                            text="Display Output",
                                            variable=self.display_output)
        display_output_cb.grid(row=12, column=0, padx=5, pady=5, sticky="w")
        Tooltip(
            display_output_cb,
            "Toggle whether to display the output image after processing.")

        # Verbose Checkbox
        self.verbose = tk.BooleanVar(value=True)
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
        # Run the processing in a separate thread to keep the GUI responsive
        threading.Thread(target=self.process, daemon=True).start()

    def process(self):
        start_time = time.time()

        input_path = self.input_path.get()
        output_path = self.output_path.get()

        if not input_path:
            self.root.after(
                0, lambda: messagebox.showerror(
                    "Error", "Please select an input file or folder."))
            return

        # Disable the process button and start the progress bar
        self.root.after(0, lambda: self.set_processing_state(True))

        try:
            # Create a mock argparse.Namespace object
            class Args:
                pass

            args = Args()
            args.input = input_path
            args.output = output_path if output_path else None
            args.shapeDetection = self.shape_detection.get()

            args.numPoints = self.num_points.get()
            args.distance = [
                self.distance_min.get(),
                self.distance_max.get()
            ] if self.distance_min.get() and self.distance_max.get() else None
            args.font = self.font.get()
            args.fontSize = self.font_size.get()
            args.fontColor = [
                int(c) for c in self.font_color.get().split(',')
            ] if self.font_color.get() else [0, 0, 0, 255]
            args.dotColor = [int(c) for c in self.dot_color.get().split(',')
                             ] if self.dot_color.get() else [0, 0, 0, 255]
            args.radius = self.radius.get()
            args.dpi = self.dpi.get()
            args.debug = False  # Debug mode is disabled in GUI
            args.displayOutput = self.display_output.get()
            args.verbose = self.verbose.get()
            args.thresholdBinary = [
                self.threshold_min.get(),
                self.threshold_max.get()
            ]

            # Validate distance inputs
            if args.distance:
                if not self.validate_distance(args.distance):
                    self.root.after(
                        0, lambda: messagebox.showerror(
                            "Error",
                            "Invalid distance values. Please enter valid numbers or percentages (e.g., 10% or 0.05)."
                        ))
                    self.root.after(0,
                                    lambda: self.set_processing_state(False))
                    return

            # Validate font color and dot color
            if len(args.fontColor) != 4 or len(args.dotColor) != 4:
                self.root.after(
                    0, lambda: messagebox.showerror(
                        "Error",
                        "Font color and Dot color must have exactly 4 integer values (RGBA)."
                    ))
                self.root.after(0, lambda: self.set_processing_state(False))
                return

            # Initialize storage for dots and labels
            self.processed_dots = []  # To store dots
            self.processed_labels = []  # To store labels

            # Process images
            if os.path.isdir(input_path):
                # Processing multiple images
                output_dir = output_path if output_path else input_path
                image_files = [
                    f for f in os.listdir(input_path)
                    if f.lower().endswith(('.png', '.jpg', '.jpeg'))
                ]
                if self.verbose.get():
                    print(
                        f"Processing {len(image_files)} images in the folder {input_path}..."
                    )

                for image_file in image_files:
                    img_input_path = os.path.join(input_path, image_file)
                    # In GUI mode, we don't want to save automatically
                    img_output_image, elapsed_time, dots, labels = process_single_image(
                        img_input_path, None, args, save_output=False)
                    if img_output_image is not None:
                        # Store the processed image
                        self.processed_image = img_output_image

                        # Store dots and labels
                        self.processed_dots = dots
                        self.processed_labels = labels

                        # Compute and store diagonal length based on processed_image
                        image_np = self.processed_image
                        self.diagonal_length = utils.compute_image_diagonal(
                            image_np)
                        # Update overlay lines
                        self.update_overlay_lines()

                        # Convert the image to PIL Image for display
                        if img_output_image.shape[2] == 4:
                            pil_image = Image.fromarray(
                                cv2.cvtColor(img_output_image,
                                             cv2.COLOR_BGRA2RGBA))
                        else:
                            pil_image = Image.fromarray(
                                cv2.cvtColor(img_output_image,
                                             cv2.COLOR_BGR2RGB))

                        self.original_output_image = pil_image

                        # Display the processed image on the output canvas
                        self.root.after(0,
                                        lambda img=pil_image: self.
                                        output_canvas.load_image(img))

                        # Enable the save button
                        self.root.after(
                            0, lambda: self.save_button.config(state="normal"))

                        # Enable the edit button now that processing is done
                        self.root.after(
                            0, lambda: self.edit_button.config(state="normal"))

            elif os.path.isfile(input_path):
                # Processing a single image
                output_image, elapsed_time, dots, labels = process_single_image(
                    input_path, None, args, save_output=False)
                if output_image is not None:
                    self.processed_image = output_image
                    # Store dots and labels
                    self.processed_dots = dots
                    self.processed_labels = labels

                    # Compute and store diagonal length based on processed_image
                    image_np = self.processed_image
                    self.diagonal_length = utils.compute_image_diagonal(
                        image_np)
                    # Update overlay lines
                    self.update_overlay_lines()

                    # Convert the image to PIL Image for display
                    if output_image.shape[2] == 4:
                        pil_image = Image.fromarray(
                            cv2.cvtColor(output_image, cv2.COLOR_BGRA2RGBA))
                    else:
                        pil_image = Image.fromarray(
                            cv2.cvtColor(output_image, cv2.COLOR_BGR2RGB))
                    self.original_output_image = pil_image
                    # Display the output image on the output canvas
                    self.root.after(
                        0, lambda: self.output_canvas.load_image(pil_image))
                    # Enable the save button
                    self.root.after(
                        0, lambda: self.save_button.config(state="normal"))
                    # Enable the edit button now that processing is done
                    self.root.after(
                        0, lambda: self.edit_button.config(state="normal"))

            else:
                self.root.after(
                    0, lambda: messagebox.showerror(
                        "Error", f"Input path '{input_path}' is invalid."))
                self.root.after(0, lambda: self.set_processing_state(False))
                return

            end_time = time.time()

            elapsed_time_2 = end_time - start_time
            # self.root.after(
            #     0, lambda: messagebox.showinfo(
            #         "Success",
            #         f"Processing complete in {elapsed_time_2:.1f} seconds."))

        except Exception as errorGUI:
            self.root.after(0,
                            lambda error=errorGUI: messagebox.showerror(
                                "Error", f"An error occurred:\n{error}"))
        finally:
            # Re-enable the process button and stop the progress bar
            self.root.after(0, lambda: self.set_processing_state(False))

    def validate_distance(self, distance):
        # Validate that distance_min and distance_max are either numbers or percentages
        for d in distance:
            if d.endswith('%'):
                try:
                    float(d.strip('%'))
                except ValueError:
                    return False
            else:
                try:
                    float(d)
                except ValueError:
                    return False
        return True

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
                # Convert the image from BGRA/BGR to RGBA/RGB for correct color representation
                if self.processed_image.shape[2] == 4:
                    # BGRA to RGBA
                    image_to_save = cv2.cvtColor(self.processed_image,
                                                 cv2.COLOR_BGRA2RGBA)
                else:
                    # BGR to RGB
                    image_to_save = cv2.cvtColor(self.processed_image,
                                                 cv2.COLOR_BGR2RGB)

                # Convert NumPy array to PIL Image
                pil_image = Image.fromarray(image_to_save)

                # Save the image using PIL
                pil_image.save(save_path)

                messagebox.showinfo("Success", f"Image saved to {save_path}.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save image:\n{e}")

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

    def apply_edit_changes(self, edited_image):
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

    def open_edit_window(self):
        if not hasattr(self,
                       'processed_image') or self.processed_image is None:
            messagebox.showerror("Error",
                                 "No processed image available to edit.")
            return

        if not hasattr(self, 'processed_dots') or not self.processed_dots:
            messagebox.showerror("Error", "No dots and labels data available.")
            return

        # Extract and format the visual parameters from the GUI
        try:
            # Parse dot color
            dot_color = self.parse_rgba(self.dot_color.get())

            # Parse font color
            font_color = self.parse_rgba(self.font_color.get())

            # Get font and font size
            font_name = self.font.get()
            font_path = utils.find_font_in_windows(
                font_name)  # Use the utility function
            if font_path is None:
                raise ValueError(f"Font '{font_name}' could not be found.")

            radius_px = utils.parse_size(self.radius.get(),
                                         self.diagonal_length)
            font_size_px = int(
                utils.parse_size(self.font_size.get(), self.diagonal_length))

        except ValueError as ve:
            messagebox.showerror("Error", f"Invalid parameter format:\n{ve}")
            return

        # Get image dimensions
        # image_width, image_height = self.processed_image.size  # Assuming processed_image is a PIL Image
        print(f"Edit output...")
        # Initialize and open the EditWindow with the necessary parameters
        EditWindow(
            master=self.root,
            dots=self.processed_dots,
            labels=self.processed_labels,
            dot_color=dot_color,
            dot_radius=radius_px,
            font_color=font_color,
            font_path=font_path,
            font_size=font_size_px,
            image_width=self.image_width,
            image_height=self.image_height,
            input_image=self.original_input_image,  # Pass the callback
            apply_callback=self.apply_edit_changes)

    def parse_rgba(self, rgba_str):
        """
        Parses an RGBA string and returns a tuple of integers.
        """
        parts = rgba_str.split(',')
        if len(parts) != 4:
            raise ValueError("RGBA must have exactly four components.")
        return tuple(int(part.strip()) for part in parts)


if __name__ == "__main__":
    app = DotToDotGUI()
    app.run()
