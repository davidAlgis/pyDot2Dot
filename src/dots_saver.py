import json
import os
import tkinter as tk
from tkinter import filedialog, messagebox
from dot import Dot, DotLabel
from metadata import read_metadata
from dots_config import DotsConfig
import numpy as np
from gui.error_window import ErrorWindow
import traceback
import threading


class DotsSaver:

    def __init__(self, root, main_gui, config):
        self.root = root
        self.main_gui = main_gui
        self.config = config
        self.save_path = ""  # Initialize save_path as an empty string
        self.save_data = None  # Initialize save_data

    def set_save_path(self):
        """
        Ask the user where to save the .d2d file and set the save path.
        This method will be executed in the main thread (file dialog thread).
        """
        if not self.save_path:
            self.save_path = filedialog.asksaveasfilename(
                defaultextension=".d2d",
                filetypes=[("Dot2Dot files", "*.d2d")],
                title="Save Dots Data")

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

            # Wait for the user to select a file path
            if not self.set_save_path():
                return  # If the user cancels, do nothing

            # Wait for the save data to be prepared
            save_data_thread.join()

            if self.save_data:
                # Write the data to the JSON file
                with open(self.save_path, "w") as f:
                    json.dump(self.save_data, f, indent=4)

        except Exception as e:
            # Capture the full stack trace
            stack_trace = traceback.format_exc()
            # Display the stack trace in a separate window using the ErrorWindow class
            self.root.after(0, lambda: ErrorWindow(self.root, stack_trace))

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
        return {
            "dot_control": {
                "position": dots_config.dot_control.position,
                "radius": dots_config.dot_control.radius,
                "color": dots_config.dot_control.color,
                "label":
                self._dot_label_to_dict(dots_config.dot_control.label),
            },
            "input_path": dots_config.input_path,
            "output_path": dots_config.output_path,
            "dpi": dots_config.dpi,
            "threshold_binary": dots_config.threshold_binary,
            "distance_min": dots_config.distance_min,
            "distance_max": dots_config.distance_max,
            "epsilon": dots_config.epsilon,
            "shape_detection": dots_config.shape_detection,
            "nbr_dots": dots_config.nbr_dots,
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
