import tkinter as tk
from tkinter import ttk
from tkinter import filedialog, messagebox
from gui.popup_2_buttons import Popup2Buttons


class SettingsWindow(tk.Toplevel):

    def __init__(self, parent, config_loader):
        super().__init__(parent)
        self.parent = parent
        self.config_loader = config_loader
        self.config = config_loader.get_config()

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
        # Add a label at the top
        top_label = ttk.Label(
            self.main_frame,
            text=
            "Change the default settings used by each new project when the executable is opened:",
            font=("Arial", 12),
            wraplength=500  # Adjust wrap length to fit nicely in the window
        )
        top_label.grid(row=0,
                       column=0,
                       columnspan=3,
                       padx=10,
                       pady=10,
                       sticky="ew")

        # Input Path
        self.create_entry("Input Path:", "input", row=1, browse=True)

        # Shape Detection
        self.create_combobox("Shape Detection:",
                             "shapeDetection", ["Contour", "Path"],
                             row=2)

        # Distance Min and Max
        self.create_entry("Distance Min:", "distance", index=0, row=4)
        self.create_entry("Distance Max:", "distance", index=1, row=5)

        # Font
        self.create_entry("Font:", "font", row=6)

        # Font Size
        self.create_entry("Font Size:", "fontSize", row=7)

        # Font Color
        self.create_entry("Font Color (RGBA):", "fontColor", row=8)

        # Dot Color
        self.create_entry("Dot Color (RGBA):", "dotColor", row=9)

        # Radius
        self.create_entry("Radius:", "radius", row=10)

        # DPI
        self.create_entry("DPI:", "dpi", row=11)

        # Epsilon
        self.create_entry("Epsilon:", "epsilon", row=12)

        # Threshold Binary Min and Max
        self.create_entry("Threshold Min:", "thresholdBinary", index=0, row=13)
        self.create_entry("Threshold Max:", "thresholdBinary", index=1, row=14)

        # Reset Button
        reset_button = ttk.Button(self.main_frame,
                                  text="Reset to Default",
                                  command=self.confirm_reset)
        reset_button.grid(row=15, column=0, columnspan=3, pady=10, sticky="ew")

    def create_entry(self,
                     label_text,
                     config_key,
                     row,
                     index=None,
                     browse=False):
        label = ttk.Label(self.main_frame, text=label_text)
        label.grid(row=row, column=0, padx=5, pady=5, sticky="e")

        var = tk.StringVar()
        if index is not None:
            var.set(self.config[config_key][index])
            var.trace_add(
                "write", lambda *args: self.config_loader.set_config_value(
                    config_key, var.get(), index))
        else:
            var.set(self.config[config_key])
            var.trace_add(
                "write", lambda *args: self.config_loader.set_config_value(
                    config_key, var.get()))

        entry = ttk.Entry(self.main_frame, textvariable=var)
        entry.grid(row=row, column=1, padx=5, pady=5, sticky="ew")

        if browse:
            browse_button = ttk.Button(self.main_frame,
                                       text="Browse",
                                       command=lambda: self.browse_file(var))
            browse_button.grid(row=row, column=2, padx=5, pady=5)

    def create_combobox(self, label_text, config_key, values, row):
        label = ttk.Label(self.main_frame, text=label_text)
        label.grid(row=row, column=0, padx=5, pady=5, sticky="e")

        var = tk.StringVar(value=self.config[config_key])
        var.trace_add(
            "write", lambda *args: self.config_loader.set_config_value(
                config_key, var.get()))

        combobox = ttk.Combobox(self.main_frame,
                                textvariable=var,
                                values=values,
                                state="readonly")
        combobox.grid(row=row, column=1, padx=5, pady=5, sticky="ew")

    def browse_file(self, var):
        file_path = filedialog.askopenfilename()
        if file_path:
            var.set(file_path)

    def update_ui(self):
        """Update the UI fields with the current configuration."""
        for key, var_name in self.__dict__.items():
            if key.endswith("_var"):
                field_key = key[:-4]  # Remove '_var' to get the config key
                if isinstance(self.config[field_key], list):
                    index = int(
                        key.split("_")[-2])  # Get the index for list keys
                    getattr(self, key).set(self.config[field_key][index])
                else:
                    getattr(self, key).set(self.config[field_key])

    def confirm_reset(self):
        """Display a confirmation popup and reset the configuration if confirmed."""

        def reset_action():
            # Reset the configuration using LoadConfig's method
            self.config_loader.reset_config_user()
            # Update the local config and UI
            self.config = self.config_loader.get_config()
            self.update_ui()
            messagebox.showinfo("Reset Successful",
                                "Settings have been reset to default values.")

        Popup2Buttons(
            root=self,
            title="Confirm Reset",
            main_text=
            "Are you sure you want to reset the settings to their default values? This action cannot be undone.",
            button1_text="Yes",
            button1_action=reset_action,
            button2_text="No")

    def on_close(self):
        # Save configuration through LoadConfig when closing the window
        self.config_loader.save_config()
        self.destroy()
