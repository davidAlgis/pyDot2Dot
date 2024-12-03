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
from gui.popup_2_buttons import Popup2Buttons
from gui.menu_bar import MenuBar
import traceback
from dot import Dot
from dots_config import DotsConfig
from dots_saver import DotsSaver


class DotToDotGUI:

    def __init__(self, config):
        self.config = config
        self.root = tk.Tk()
        self.root.title("Dot to Dot - Unknown")
        self.maximize_window()  # Maximize the window on startup
        self.debounce_resize_id = None  # For debouncing resize events
        self.processed_image = None  # Store the processed image
        self.combined_image = None  # Store the combined image with background
        self.display_combined = tk.BooleanVar(value=False)
        self.diagonal_length = None  # To store image diagonal
        self.image_width, self.image_height = None, None
        self.contours_windows = []
        self.has_edit = False
        self.has_process = False
        # the dot that will serve as the reference dot for new one
        # it will be updated when clicking on process
        self.dots_config = DotsConfig.default_dots_config(self.config)
        self.processed_dots = []
        self.dots_saver = DotsSaver(self.root, self, self.config)
        self.create_widgets()
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

        # Create the menu bar
        self.menu_bar = MenuBar(self.root, self, self.config, self.dots_saver)
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

        # Parameters Frame
        params_frame = ttk.LabelFrame(control_frame, text="Parameters")
        params_frame.grid(row=2, column=0, padx=5, pady=5, sticky="ew")
        params_frame.columnconfigure(1, weight=1)

        # Shape Detection
        shape_combo_label = ttk.Label(params_frame, text="Shape Detection:")
        shape_combo_label.grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.shape_detection = tk.StringVar(
            value=self.config["shapeDetection"])
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
        tooltip_shape_str = "Select the method for shape detection: 'Contour' for contour-based or 'Path' for skeleton-based detection."
        Tooltip(shape_combo, tooltip_shape_str)
        Tooltip(shape_combo_label, tooltip_shape_str)
        self.shape_detection.trace_add(
            'write', lambda *args: setattr(self.dots_config, "shape_detection",
                                           self.shape_detection.get()))

        # Number of Points
        num_points_label = ttk.Label(params_frame, text="Number of Points:")
        num_points_label.grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.num_points = tk.StringVar(value=str(self.config["numPoints"]))
        num_points_entry = ttk.Entry(params_frame,
                                     textvariable=self.num_points)
        num_points_entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        tooltip_num_points_str = "Specify the desired number of points in the simplified path (can be left empty)."
        self.num_points.trace_add(
            'write', lambda *args: setattr(self.dots_config, "nbr_dots",
                                           self.num_points.get()))

        Tooltip(num_points_entry, tooltip_num_points_str)
        Tooltip(num_points_label, tooltip_num_points_str)

        # Epsilon
        epsilon_entry_label = ttk.Label(params_frame, text="Epsilon:")
        epsilon_entry_label.grid(row=2, column=0, padx=5, pady=5, sticky="e")
        self.epsilon = tk.DoubleVar(value=self.config["epsilon"])
        epsilon_entry = ttk.Entry(params_frame, textvariable=self.epsilon)
        self.epsilon.trace_add(
            'write', lambda *args: setattr(self.dots_config, "epsilon",
                                           self.epsilon.get()))
        epsilon_entry.grid(row=2, column=1, padx=5, pady=5, sticky="w")
        tooltip_epsilon_str = "Set the epsilon for path approximation. Smaller values preserve more detail."
        Tooltip(epsilon_entry, tooltip_epsilon_str)
        Tooltip(epsilon_entry_label, tooltip_epsilon_str)

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
        self.distance_min = tk.StringVar(value=self.config["distance"][0])
        distance_min_entry = ttk.Entry(params_frame,
                                       textvariable=self.distance_min)
        distance_min_entry.grid(row=3,
                                column=1,
                                padx=(5, 0),
                                pady=5,
                                sticky="w")
        tooltip_distance_min_str = "Define the minimum distance between points in pixels"
        Tooltip(distance_min_entry, tooltip_distance_min_str)
        Tooltip(distance_min_label, tooltip_distance_min_str)

        distance_max_label = ttk.Label(params_frame, text="Distance Max:")
        distance_max_label.grid(row=4, column=0, padx=5, pady=5, sticky="e")
        self.distance_max = tk.StringVar(value=self.config["distance"][1])
        distance_max_entry = ttk.Entry(params_frame,
                                       textvariable=self.distance_max)
        distance_max_entry.grid(row=4,
                                column=1,
                                padx=(5, 0),
                                pady=5,
                                sticky="w")
        tooltip_distance_max_str = "Define the maximum distance between points, in pixels."
        Tooltip(distance_max_entry, tooltip_distance_max_str)
        Tooltip(distance_max_label, tooltip_distance_max_str)

        # DPI
        # dpi_label = ttk.Label(params_frame, text="DPI:")
        # dpi_label.grid(row=10, column=0, padx=5, pady=5, sticky="e")
        # self.dpi = tk.IntVar(value=self.config["dpi"])
        # dpi_entry = ttk.Entry(params_frame, textvariable=self.dpi)
        # dpi_entry.grid(row=10, column=1, padx=5, pady=5, sticky="w")
        # Tooltip(dpi_entry, "Set the DPI (Dots Per Inch) of the output image.")
        # Tooltip(dpi_label, "Set the DPI (Dots Per Inch) of the output image.")

        # Threshold Binary
        threshold_max_label = ttk.Label(params_frame,
                                        text="Threshold Binary (min max):")
        threshold_max_label.grid(row=11, column=0, padx=5, pady=5, sticky="e")
        self.threshold_min = tk.IntVar(value=self.config["thresholdBinary"][0])
        self.threshold_max = tk.IntVar(value=self.config["thresholdBinary"][1])
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

        # Process Button
        process_button = ttk.Button(control_frame,
                                    text="Process",
                                    command=self.process_threaded)
        process_button.grid(row=3, column=0, padx=5, pady=10, sticky="ew")
        Tooltip(
            process_button,
            "Click to start processing the selected image(s) with the specified parameters."
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
        self.original_input_image = None
        self.original_output_image = None

        # Toggle Button to switch between processed and combined image
        toggle_button = ttk.Checkbutton(output_preview,
                                        text="Show link between dots",
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
        dot_radius = self.dots_config.dot_control.radius
        threshold_binary = [self.threshold_min.get(), self.threshold_max.get()]
        shape_detection = self.shape_detection.get()
        input_path = self.dots_config.input_path
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
        self.distance_min.trace_add("write",
                                    lambda *args: self.update_overlay_lines())
        self.distance_max.trace_add("write",
                                    lambda *args: self.update_overlay_lines())

    def set_output_image(self):
        if self.processed_image is not None:
            # Convert the image to PIL Image for display
            self.original_output_image = utils.image_to_pil_rgb(
                self.processed_image)
            self.root.after(
                0, lambda: self.output_canvas.load_image(
                    self.original_output_image))
            self.root.after(0, lambda: self.edit_button.config(state="normal"))

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

            self.has_process = True

            # Processing a single image
            self.processed_image, self.combined_image, elapsed_time, self.processed_dots, have_multiple_contours = process_single_image(
                self.dots_config)
            if have_multiple_contours:
                self.handle_multiple_contours(input_path, self.processed_dots,
                                              labels)

            # Post-processing steps
            end_time = time.time()
            elapsed_time = end_time - start_time
            self.set_output_image()
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
                self.set_widget_active(child, False)
        else:
            self.root.config(cursor="")
            self.progress.stop()
            # Re-enable interactive widgets after processing
            for child in self.root.winfo_children():
                self.set_widget_active(child, True)

    def set_widget_active(self, widget, set_active):
        """
        Recursively disables widgets that support the 'state' attribute.
        """
        try:
            widget_type = widget.winfo_class()
            if widget_type in ["Button", "Entry", "Combobox", "Checkbutton"]:
                if set_active:
                    widget.config(state='normal')
                else:
                    widget.config(state='disabled')
        except tk.TclError:
            pass  # Some widgets might not support 'state'

        # Recursively disable child widgets
        for child in widget.winfo_children():
            self.set_widget_active(child, set_active)

    def clear_input_image(self):
        self.input_canvas.canvas.delete("all")
        self.original_input_image = None
        self.diagonal_length = None
        self.input_canvas.overlay_lines.clear()

    def clear_output_image(self):
        self.output_canvas.canvas.delete("all")
        self.original_output_image = None
        self.processed_image = None
        self.edit_button.config(
            state="disabled")  # Disable edit button when no image is processed

    def update_color_box(self, color_var, color_box):
        """
        Updates the color box based on the RGBA value from the Entry widget.
        """
        rgba_str = color_var.get()
        hex_color = utils.rgba_to_hex(rgba_str)
        color_box.config(bg=hex_color)

    def run(self):
        # Bind the resize event to adjust the image previews with debouncing
        self.input_canvas.canvas.bind(
            "<Configure>", lambda event: self.debounce_resize(event))
        self.root.mainloop()

    def debounce_resize(self, event):
        """
        Debounces the resize event to prevent excessive resizing.
        """
        if self.debounce_resize_id:
            self.root.after_cancel(self.debounce_resize_id)
        self.debounce_resize_id = self.root.after(
            200, lambda: self.set_input_image())

    def set_input_image(self):
        """
        Updates the displayed image when the canvas is resized.
        """
        if os.path.isfile(self.dots_config.input_path):
            self.original_input_image = utils.load_image(
                self.dots_config.input_path)
            if self.original_input_image:
                target_size = (self.input_canvas.canvas.winfo_width(),
                               self.input_canvas.canvas.winfo_height())
                resized_pil_image = utils.resize_image(
                    self.original_input_image, target_size)
                self.image_width, self.image_height = self.input_canvas.load_image(
                    self.original_input_image)

                self.update_overlay_lines()
        else:
            self.clear_input_image()

    def update_overlay_lines(self):
        """
        Reads the current parameter values, converts them to pixels, and updates the overlay lines.
        """
        if not self.original_input_image or not self.diagonal_length:
            return

        # Parse parameters
        try:
            radius_px = int(self.radius.get())
        except:
            radius_px = 10  # default value
        try:
            distance_min_px = int(
                self.distance_min.get()) if self.distance_min.get() else 0
        except:
            distance_min_px = 0
        try:
            distance_max_px = int(
                self.distance_max.get()) if self.distance_max.get() else 0
        except:
            distance_max_px = 0
        try:
            font_size_px = int(self.font_size.get())
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
                   apply_callback=self.apply_changes)

    def open_shape_vis_window(self):
        """
        Opens the ShapeVisWindow to visualize shape detection modes.
        """
        if not self.original_input_image:
            messagebox.showerror(
                "Error", "No input image available for visualization.")
            return

        # Retrieve the current shape detection mode and threshold binary values
        # shape_detection_mode = self.shape_detection.get()
        shape_detection_mode = self.dots_config.shape_detection
        # threshold_binary = (self.threshold_min.get(), self.threshold_max.get())
        threshold_binary = self.dots_config.threshold_binary
        input_path = self.dots_config.input_path  # Path to the input image file

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

        def yes_action():
            self.has_edit = False
            continue_callback()

        Popup2Buttons(
            self.root, "Confirm Process",
            "Processing will reset all unsaved edits. Do you want to continue?",
            "Yes", yes_action, "No")
