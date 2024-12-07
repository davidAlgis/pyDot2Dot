import json
import os
import tkinter as tk
from tkinter import filedialog, messagebox
from dot import Dot, DotLabel
from metadata import read_metadata
from dots_config import DotsConfig
import numpy as np
from gui.error_window import ErrorWindow
from image_creation import ImageCreation
import traceback
import cv2
import threading


class DotsSaver:

    def __init__(self, root, main_gui, config):
        self.root = root
        self.main_gui = main_gui
        self.config = config
        self.save_path = ""  # Initialize save_path as an empty string
        self.save_data = None  # Initialize save_data
        self.save_name = "Unknown *"

    def set_save_path(self, file_types):
        """
        Ask the user where to save the file (either .d2d or image) and set the save path.
        This method will be executed in the main thread (file dialog thread).
        """
        if not self.save_path:
            self.save_path = filedialog.asksaveasfilename(
                defaultextension=file_types[0][1],
                filetypes=file_types,
                title="Save Dots Data or Image")

        # If the user cancels the save dialog, return early
        if not self.save_path:
            self.save_path = None  # Reset save path in case of cancel
            return False

        return True

    def create_save_data(self, dots, dots_config):
        """
        Create the data to be saved, ensuring it's serializable.
        This method will be executed in a separate thread.
        """
        try:
            # Fetch metadata
            metadata = read_metadata()

            # Prepare the data to save
            save_data = {
                "metadata": metadata,
                "dots_config": self._dots_config_to_dict(dots_config),
                "dots": [self._dot_to_dict(dot) for dot in dots]
            }

            # Apply conversion to ensure everything is serializable
            save_data = DotsSaver.convert_to_serializable(save_data)

            self.save_data = save_data  # Store the prepared save data

        except Exception as e:
            # Capture the full stack trace
            stack_trace = traceback.format_exc()
            # Display the stack trace in a separate window using the ErrorWindow class
            self.root.after(0, lambda: ErrorWindow(self.root, stack_trace))

    def save_d2d_as(self, dots, dots_config):
        # Reset save path as none
        self.save_path = None
        self.save_d2d(dots, dots_config)

    def save_d2d(self, dots, dots_config):
        """
        Save the current state (metadata + dots config + list of dots) into a .d2d file.
        This method coordinates the save process by calling set_save_path and create_save_data in parallel.
        """
        try:
            # Start a background thread to prepare the save data
            save_data_thread = threading.Thread(target=self.create_save_data,
                                                args=(dots, dots_config))
            save_data_thread.start()

            # Ask the user where to save and what format (e.g., .d2d or .png)
            file_types = [("Dot2Dot files", "*.d2d"), ("PNG files", "*.png"),
                          ("JPEG files", "*.jpg;*.jpeg")]
            if not self.set_save_path(file_types):
                return  # If the user cancels, do nothing

            # Wait for the save data to be prepared
            save_data_thread.join()

            # Check the file extension and save accordingly
            if self.save_path.endswith(".d2d"):
                if self.save_data:
                    # Write the data to the JSON file
                    with open(self.save_path, "w") as f:
                        json.dump(self.save_data, f, indent=4)
                    self.update_main_window_name()
                    self.main_gui.needs_save = False
            elif self.save_path.endswith((".png", ".jpg", ".jpeg")):
                # Save the image using PIL (if it's an image file)
                self.main_gui.original_output_image.save(self.save_path)
                # Reset save_path in a way that next time it save it ask again
                self.save_path = None
            else:
                messagebox.showerror("Error",
                                     "Unsupported file format selected.")

        except Exception as e:
            # Capture the full stack trace
            stack_trace = traceback.format_exc()
            # Display the stack trace in a separate window using the ErrorWindow class
            self.root.after(0, lambda: ErrorWindow(self.root, stack_trace))

    def update_main_window_name(self):
        self.save_name = os.path.splitext(os.path.basename(self.save_path))[0]
        self.root.title(f"Dot to Dot - {self.save_name}")

    @staticmethod
    def convert_to_serializable(data):
        """
        Recursively convert NumPy data types to native Python types (int, float, etc.).
        """
        if isinstance(data, dict):
            return {
                key: DotsSaver.convert_to_serializable(value)
                for key, value in data.items()
            }
        elif isinstance(data, list):
            return [DotsSaver.convert_to_serializable(item) for item in data]
        elif isinstance(data, tuple):  # Added case for tuples
            return tuple(
                DotsSaver.convert_to_serializable(item) for item in data)
        elif isinstance(data, np.ndarray):
            return data.tolist()  # Convert numpy arrays to lists
        elif isinstance(data, np.generic
                        ):  # Catch any NumPy scalar type (intc, float64, etc.)
            return data.item(
            )  # Converts NumPy scalar to a native Python type (int, float, etc.)
        return data  # Return the data as is if it's already serializable

    def _dots_config_to_dict(self, dots_config):
        """
        Convert a DotsConfig object to a dictionary for saving to a JSON file.
        """
        if dots_config.output_path:
            dots_config.output_path = os.path.abspath(dots_config.output_path)
        return {
            "dot_control": {
                "position": dots_config.dot_control.position,
                "radius": dots_config.dot_control.radius,
                "color": dots_config.dot_control.color,
                "label":
                self._dot_label_to_dict(dots_config.dot_control.label),
            },
            "input_path": os.path.abspath(dots_config.input_path),
            "output_path": dots_config.output_path,
            "dpi": dots_config.dpi,
            "threshold_binary": dots_config.threshold_binary,
            "distance_min": dots_config.distance_min,
            "distance_max": dots_config.distance_max,
            "epsilon": dots_config.epsilon,
            "shape_detection": dots_config.shape_detection,
        }

    def _dot_label_to_dict(self, dot_label):
        """
        Convert a DotLabel object to a dictionary.
        """
        if not dot_label:
            return None
        return {
            "position": dot_label.position,
            "color": dot_label.color,
            "font_path": dot_label.font_path,
            "font_size": dot_label.font_size,
            "anchor": dot_label.anchor,
        }

    def _dot_to_dict(self, dot):
        """
        Convert a Dot object to a dictionary.
        """
        return {
            "dot_id": dot.dot_id,
            "position": dot.position,
            "color": dot.color,
            "radius": dot.radius,
            "label": self._dot_label_to_dict(dot.label),
        }

    def export_output_image(self):
        if self.main_gui.processed_image is None:
            messagebox.showerror("Error", "No processed image to save.")
            return

        # Ask the user where to save the image
        self.save_path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("JPEG files", "*.jpg;*.jpeg")],
            title="Save Output Image")

        if self.save_path:
            try:
                # Save the image using PIL
                self.main_gui.original_output_image.save(self.save_path)

                messagebox.showinfo("Success",
                                    f"Image saved to {self.save_path}.")
            except Exception as errorGUI:
                # Capture the full stack trace
                stack_trace = traceback.format_exc()
                # Display the stack trace in a separate window using the ErrorWindow class
                self.root.after(0, lambda: ErrorWindow(self.root, stack_trace))

    def redraw_image(self, dots):
        try:
            # Load the corrected image for processing
            original_image = cv2.imread(self.main_gui.dots_config.input_path)

            image_height, image_width = original_image.shape[:2]
            # Create an instance of ImageCreation with required parameters
            image_creation = ImageCreation(
                image_size=(image_height, image_width),
                dots=dots,
                dot_control=self.main_gui.dots_config.dot_control,
                debug=False,
                reset_label=False)

            # Draw the points on the image with a transparent background
            output_image_with_dots, updated_dots, combined_image_np, invalid_indices = image_creation.draw_points_on_image(
                self.main_gui.dots_config.input_path, set_label=False)

            return output_image_with_dots, combined_image_np
        except Exception as errorGUI:
            # Capture the full stack trace
            stack_trace = traceback.format_exc()
            # Display the stack trace in a separate window using the ErrorWindow class
            self.root.after(0, lambda: ErrorWindow(self.root, stack_trace))

    def load_input(self):
        """
        Open a file dialog to load .d2d, .png, or .jpeg files. If it's a .png or .jpeg file, 
        the image is loaded into the main GUI. If it's a .d2d file, the dots and configuration 
        are loaded and returned.
        """
        # Open a file dialog to select a file
        file_path = filedialog.askopenfilename(filetypes=[
            ("All files", "*.*"), ("Dot2Dot files", "*.d2d"),
            ("PNG files", "*.png"), ("JPEG files", "*.jpg;*.jpeg")
        ],
                                               title="Load Dots Data or Image")

        if not file_path:
            return

        # Check the file extension and load accordingly
        if file_path.endswith((".png", ".jpg", ".jpeg")):
            # For image files, set the input image in the main GUI
            self.main_gui.dots_config.input_path = file_path
            self.main_gui.set_input_image()
            return

        elif file_path.endswith(".d2d"):
            print(f"Load {file_path}...")
            # For .d2d files, read the data
            try:
                with open(file_path, "r") as f:
                    data = json.load(f)

                # Extract dots and configuration from the .d2d file
                dots_config_data = data.get("dots_config")
                dots_data = data.get("dots")

                dot_control_data = dots_config_data["dot_control"]
                dot_control_label_data = dot_control_data["label"]
                dot_control = Dot(dot_control_data["position"], 0)
                dot_control.radius = int(dot_control_data["radius"])
                dot_control.color = tuple(dot_control_data["color"])
                dot_control.set_label(tuple(dot_control_label_data["color"]),
                                      dot_control_label_data["font_path"],
                                      int(dot_control_label_data["font_size"]))
                dot_control.label.position = dot_control_label_data["position"]
                dot_control.label.anchor = dot_control_label_data["anchor"]

                try:
                    data = self.check_file_path_load_d2d(data, file_path)
                except FileNotFoundError:
                    print(
                        "Warning: couldn't find the input image while loading the path. We continue the loading but all features might not work."
                    )

                # Create the dots_config object
                dots_config = DotsConfig(
                    dot_control=dot_control,
                    input_path=dots_config_data["input_path"],
                    output_path=dots_config_data["output_path"],
                    dpi=dots_config_data["dpi"],
                    threshold_binary=dots_config_data["threshold_binary"],
                    distance_min=dots_config_data["distance_min"],
                    distance_max=dots_config_data["distance_max"],
                    epsilon=dots_config_data["epsilon"],
                    shape_detection=dots_config_data["shape_detection"].lower(
                    ))
                dots = []
                for dot_data in dots_data:
                    dot = Dot(position=tuple(dot_data["position"]),
                              dot_id=dot_data["dot_id"])
                    dot.radius = dot_data["radius"]
                    dot.color = tuple(dot_data["color"])
                    dots.append(dot)

                # Set the label for each dot
                for dot, dot_data in zip(dots, dots_data):
                    label_data = dot_data.get("label")
                    if label_data:
                        dot.label = DotLabel(dot.position, dot.radius,
                                             tuple(label_data["color"]),
                                             label_data["font_path"],
                                             label_data["font_size"],
                                             dot_data["dot_id"])
                        position = label_data["position"]
                        position_tuple = (np.int32(position[0]),
                                          np.int32(position[1]))
                        dot.label.position = position_tuple
                        dot.label.anchor = label_data["anchor"]

                self.main_gui.processed_dots = dots
                self.main_gui.dots_config = dots_config
                self.main_gui.set_input_image()
                # defined output image
                self.main_gui.processed_image, self.main_gui.combined_image = self.redraw_image(
                    dots)
                # self.main_gui.update_image_display(None, False)
                self.main_gui.set_output_image()
                self.save_path = file_path
                self.update_main_window_name()
                print("Finish loading.")

            except Exception as e:
                # Handle any errors that occur while reading the .d2d file
                stack_trace = traceback.format_exc()
                self.root.after(0, lambda: ErrorWindow(self.root, stack_trace))
                return

        else:
            # If the file type is not supported
            messagebox.showerror("Error", "Unsupported file format.")

    def check_file_path_load_d2d(self, data, d2d_file_path):
        """
        Checks if the input image path in data["dots_config"] exists.
        If it doesn't, prompts the user to select a new image file and updates the path.
        The updated data is written back to the .d2d file.
        """
        dots_config_data = data.get("dots_config", {})
        input_path = dots_config_data.get("input_path", "")
        if not os.path.exists(input_path):
            # Open a popup to warn the user and allow them to select a new image file
            popup = tk.Toplevel(self.root)
            popup.title("Input Image Not Found")
            message = tk.Label(popup,
                               text=("The input image file was not found:\n"
                                     f"{input_path}\n\n"
                                     "Please select a new input image file."),
                               justify="left")
            message.pack(padx=20, pady=20)

            # Variable to store whether a new path was selected
            new_path_selected = [False]

            # Function to handle browsing for a new image
            def browse_new_image():
                new_file_path = filedialog.askopenfilename(
                    title="Select New Input Image",
                    filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.bmp")])
                if new_file_path:
                    dots_config_data["input_path"] = new_file_path
                    data["dots_config"] = dots_config_data
                    # Set the flag
                    new_path_selected[0] = True
                    # Close the popup
                    popup.destroy()

            # Browse Button
            browse_button = tk.Button(popup,
                                      text="Browse...",
                                      command=browse_new_image)
            browse_button.pack(pady=(0, 20))

            # Wait for the popup to close
            self.root.wait_window(popup)

            # If the user selected a new path, write the updated data back to the .d2d file
            if new_path_selected[0]:
                try:
                    with open(d2d_file_path, "w") as f:
                        json.dump(data, f, indent=4)
                    messagebox.showinfo(
                        "Success",
                        f"The {d2d_file_path} file has been updated with the new input image path."
                    )
                except Exception as e:
                    messagebox.showerror(
                        "Error", f"Failed to update .d2d file: {str(e)}")
            else:
                # If the user did not select a new path, abort the loading process
                messagebox.showerror(
                    "Error",
                    "No valid input image selected. Loading has been aborted.")
                raise FileNotFoundError(
                    "Input image file not found and no new file selected.")

        return data
