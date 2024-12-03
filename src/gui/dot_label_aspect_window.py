import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from dot_label import DotLabel
from gui.tooltip import Tooltip
from gui.popup_2_buttons import Popup2Buttons
import utils


class DotLabelAspectWindow(tk.Toplevel):

    def __init__(self, parent, dots_config, general_config):
        super().__init__(parent)
        self.parent = parent
        self.dots_config = dots_config
        self.general_config = general_config
        self.config = general_config.get_config()

        # Configure the window
        self.title("Dot Label Aspect Configuration")
        self.geometry("600x600")
        self.resizable(True, True)

        # Create main frame
        self.main_frame = ttk.Frame(self, padding=10)
        self.main_frame.grid(sticky="nsew")

        # Configure layout for window
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.main_frame.columnconfigure(1, weight=1)

        self.radius = tk.StringVar(value=self.dots_config.dot_control.radius)
        self.dot_color = tk.StringVar(
            value=','.join(map(str, self.dots_config.dot_control.color)))
        self.font_color = tk.StringVar(
            value=','.join(map(str, self.dots_config.dot_control.label.color)))
        self.font_size = tk.StringVar(
            value=self.dots_config.dot_control.label.font_size)
        self.font = tk.StringVar(
            value=self.dots_config.dot_control.label.font_path)
        # Add widgets for configuration settings
        self.create_widgets()
        # Set protocol to save settings on close
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def create_widgets(self):
        # Add a label at the top
        top_label = ttk.Label(
            self.main_frame,
            text="Configure the dot label aspect settings.",
            font=("Arial", 12),
            wraplength=500  # Adjust wrap length to fit nicely in the window
        )
        top_label.grid(row=0,
                       column=0,
                       columnspan=3,
                       padx=10,
                       pady=10,
                       sticky="ew")

        # Dot Radius
        self.create_entry(
            self.main_frame,
            "Dot Radius:",
            row=1,
            column=0,
            default_value=self.dots_config.dot_control.radius,
            entry_variable=self.radius,
            tooltip_text=
            "Set the radius of the points, either in pixels or as a percentage of the image diagonal (e.g., 12 or 8%).",
            field_name="radius")

        # Dot Color
        self.create_entry(
            self.main_frame,
            "Dot Color (RGBA):",
            row=2,
            column=0,
            default_value=','.join(map(str,
                                       self.dots_config.dot_control.color)),
            entry_variable=self.dot_color,
            tooltip_text=
            "Set the color for dots in RGBA format (e.g., 0,255,0,255 for green).",
            color_box=True,
            field_name="color")

        # Font Color
        self.create_entry(
            self.main_frame,
            "Font Color (RGBA):",
            row=3,
            column=0,
            default_value=','.join(
                map(str, self.dots_config.dot_control.label.color)),
            entry_variable=self.font_color,
            tooltip_text=
            "Set the font color for labels in RGBA format (e.g., 255,0,0,255 for red).",
            color_box=True,
            field_name="label.color")

        # Font Size
        self.create_entry(
            self.main_frame,
            "Font Size:",
            row=4,
            column=0,
            default_value=self.dots_config.dot_control.label.font_size,
            entry_variable=self.font_size,
            tooltip_text=
            "Set the font size for labels, either in pixels or as a percentage of the image diagonal (e.g., 12 or 10%).",
            field_name="label.font_size")

        # Font Path (with browse button)
        self.create_entry(
            self.main_frame,
            "Font Path:",
            row=5,
            column=0,
            default_value=self.dots_config.dot_control.label.font_path,
            entry_variable=self.font,
            tooltip_text=
            "Specify the font file for labeling points (e.g., Arial.ttf). The font should be located in C:\\Windows\\Fonts.",
            browse=True,
            field_name="label.font_path")

        # Reset Button
        reset_button = ttk.Button(self.main_frame,
                                  text="Reset to Default",
                                  command=self.confirm_reset)
        reset_button.grid(row=6, column=0, columnspan=3, pady=10, sticky="ew")

    def update_config(self, field_name, value):
        # Update the relevant attribute in dots_config
        setattr(self.dots_config.dot_control, field_name, value)

    def create_entry(self,
                     params_frame,
                     label_text,
                     row,
                     column,
                     default_value,
                     entry_variable,
                     tooltip_text,
                     color_box=False,
                     color_variable=None,
                     browse=False,
                     field_name=None):
        # Create Label
        label = ttk.Label(params_frame, text=label_text)
        label.grid(row=row, column=column, padx=5, pady=5, sticky="e")

        # Create Entry
        entry = ttk.Entry(params_frame, textvariable=entry_variable)
        entry.grid(row=row, column=column + 1, padx=5, pady=5, sticky="w")

        # Add Tooltip to Entry
        Tooltip(entry, tooltip_text)

        # Add Tooltip to Label
        Tooltip(label, tooltip_text)

        # If it's a color input, add a color box
        if color_box:
            color_box_widget = tk.Label(params_frame,
                                        bg=utils.rgba_to_hex(
                                            entry_variable.get()),
                                        width=3,
                                        relief="sunken")
            color_box_widget.grid(row=row,
                                  column=column + 2,
                                  padx=5,
                                  pady=5,
                                  sticky="w")
            Tooltip(color_box_widget,
                    "Visual representation of the selected color.")

            # Update color box when color changes
            entry_variable.trace_add(
                'write', lambda *args: self.update_color_box(
                    entry_variable, color_box_widget))

        # If browse is True, add a button to browse for files
        if browse:
            browse_button = ttk.Button(
                params_frame,
                text="Browse",
                command=lambda: self.browse_file(entry_variable))
            browse_button.grid(row=row,
                               column=column + 2,
                               padx=5,
                               pady=5,
                               sticky="w")
        # Bind the entry field to update the corresponding field in dots_config
        if field_name:
            entry_variable.trace_add(
                'write', lambda *args: self.update_config(
                    field_name, entry_variable.get()))

        # Return the entry widget if needed
        return entry

    def create_combobox(self, label_text, config_key, values, row):
        label = ttk.Label(self.main_frame, text=label_text)
        label.grid(row=row, column=0, padx=5, pady=5, sticky="e")

        var = tk.StringVar(value=self.dots_config.config[config_key])
        var.trace_add(
            "write", lambda *args: self.dots_config.set_config_value(
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
                getattr(self, key).set(self.dots_config.config[field_key])

    def confirm_reset(self):
        """Display a confirmation popup and reset the configuration if confirmed."""

        def reset_action():
            # Reset the configuration using general_config's default values
            self.dots_config.reset_dot_control(self.general_config)
            # Update the local config and UI
            self.update_ui()
            messagebox.showinfo(
                "Reset Successful",
                "Dot label aspect settings have been reset to default values.")

        Popup2Buttons(
            root=self,
            title="Confirm Reset",
            main_text=
            "Are you sure you want to reset the dot label settings to their default values? This action cannot be undone.",
            button1_text="Yes",
            button1_action=reset_action,
            button2_text="No")

    def on_close(self):
        self.destroy()