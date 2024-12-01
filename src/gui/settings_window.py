import tkinter as tk
from tkinter import ttk
from tkinter import filedialog, messagebox
import json


class SettingsWindow(tk.Toplevel):

    def __init__(self, parent, config):
        super().__init__(parent)
        self.parent = parent
        self.config = config

        # Configure the window
        self.title("Settings Configuration")
        self.geometry("600x600")
        self.resizable(True, True)

        # Create main frame
        self.main_frame = ttk.Frame(self, padding=10)
        self.main_frame.grid(sticky="nsew")

        # Configure layout for window
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.main_frame.columnconfigure(1, weight=1)

        # Add widgets for configuration settings
        self.create_widgets()

        # Set protocol to save settings on close
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def create_widgets(self):
        # Input Path
        self.create_entry("Input Path:", "input", row=0, browse=True)

        # Shape Detection
        self.create_combobox("Shape Detection:",
                             "shapeDetection", ["Contour", "Path"],
                             row=1)

        # Number of Points
        self.create_entry("Number of Points:", "numPoints", row=2)

        # Distance Min and Max
        self.create_entry("Distance Min:", "distance", index=0, row=3)
        self.create_entry("Distance Max:", "distance", index=1, row=4)

        # Font
        self.create_entry("Font:", "font", row=5)

        # Font Size
        self.create_entry("Font Size:", "fontSize", row=6)

        # Font Color
        self.create_entry("Font Color (RGBA):", "fontColor", row=7)

        # Dot Color
        self.create_entry("Dot Color (RGBA):", "dotColor", row=8)

        # Radius
        self.create_entry("Radius:", "radius", row=9)

        # DPI
        self.create_entry("DPI:", "dpi", row=10)

        # Epsilon
        self.create_entry("Epsilon:", "epsilon", row=11)

        # Threshold Binary Min and Max
        self.create_entry("Threshold Min:", "thresholdBinary", index=0, row=12)
        self.create_entry("Threshold Max:", "thresholdBinary", index=1, row=13)

    def create_entry(self,
                     label_text,
                     config_key,
                     row,
                     index=None,
                     browse=False):
        # Create a label and entry for a specific config key
        label = ttk.Label(self.main_frame, text=label_text)
        label.grid(row=row, column=0, padx=5, pady=5, sticky="e")

        # Use StringVar to bind the entry to the config value
        if index is not None:
            var = tk.StringVar(value=self.config[config_key][index])
            var.trace_add(
                "write",
                lambda *args: self.update_config(config_key, var, index))
        else:
            var = tk.StringVar(value=self.config[config_key])
            var.trace_add("write",
                          lambda *args: self.update_config(config_key, var))

        # Save reference for later use
        setattr(self, f"{config_key}_var", var)

        entry = ttk.Entry(self.main_frame, textvariable=var)
        entry.grid(row=row, column=1, padx=5, pady=5, sticky="ew")

        # Add browse button for file selection
        if browse:
            browse_button = ttk.Button(self.main_frame,
                                       text="Browse",
                                       command=lambda: self.browse_file(var))
            browse_button.grid(row=row, column=2, padx=5, pady=5)

    def create_combobox(self, label_text, config_key, values, row):
        # Create a label and combobox for a specific config key
        label = ttk.Label(self.main_frame, text=label_text)
        label.grid(row=row, column=0, padx=5, pady=5, sticky="e")

        var = tk.StringVar(value=self.config[config_key])
        var.trace_add("write",
                      lambda *args: self.update_config(config_key, var))
        setattr(self, f"{config_key}_var", var)

        combobox = ttk.Combobox(self.main_frame,
                                textvariable=var,
                                values=values,
                                state="readonly")
        combobox.grid(row=row, column=1, padx=5, pady=5, sticky="ew")

    def browse_file(self, var):
        # Open a file dialog to select a file and update the variable
        file_path = filedialog.askopenfilename()
        if file_path:
            var.set(file_path)

    def update_config(self, config_key, var, index=None):
        # Update the config in memory whenever a field changes
        if index is not None:
            self.config[config_key][index] = var.get()
        else:
            self.config[config_key] = var.get()

    def on_close(self):
        self.destroy()
        # # Save updated config to file when closing the window
        # try:
        #     with open("config_user.json", "w") as file:
        #         json.dump(self.config, file, indent=4)
        #     print("Settings saved successfully.")
        # except Exception as e:
        #     print(f"Failed to save settings: {e}")
        # finally:
        # self.destroy()
