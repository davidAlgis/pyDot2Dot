"""
Open a window to defined the visual settings of the dots and the label
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, colorchooser
from dot2dot.gui.tooltip import Tooltip
from dot2dot.gui.popup_2_buttons import Popup2Buttons
from dot2dot.utils import rgba_to_hex, str_color_to_tuple, str_to_int_safe
from dot2dot.gui.utilities_gui import set_icon


class AspectSettingsWindow(tk.Toplevel):
    """
    This class describes the window to defined 
    the visual settings of the dots and the label
    """

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
        self.attributes("-topmost", True)
        set_icon(self)

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
            text="Configure visual aspect of dots and label:",
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
            "Set the radius of the points, either in pixels or as a percentage of the image diagonal (e.g., 12 or 8%)."
        )
        self.radius.trace_add(
            'write',
            lambda *args: setattr(self.dots_config.dot_control, "radius",
                                  str_to_int_safe(self.radius.get())))

        # Dot Color
        self.create_entry(self.main_frame,
                          "Dot Color (RGBA):",
                          row=2,
                          column=0,
                          default_value=','.join(
                              map(str, self.dots_config.dot_control.color)),
                          entry_variable=self.dot_color,
                          tooltip_text="Set the color for dots.",
                          color_box=True)
        self.dot_color.trace_add(
            'write',
            lambda *args: setattr(self.dots_config.dot_control, "color",
                                  str_color_to_tuple(self.dot_color.get())))

        # Font Color
        self.create_entry(self.main_frame,
                          "Font Color (RGBA):",
                          row=3,
                          column=0,
                          default_value=','.join(
                              map(str,
                                  self.dots_config.dot_control.label.color)),
                          entry_variable=self.font_color,
                          tooltip_text="Set the font color for labels.",
                          color_box=True)
        self.font_color.trace_add(
            'write',
            lambda *args: setattr(self.dots_config.dot_control.label, "color",
                                  str_color_to_tuple(self.font_color.get())))

        # Font Size
        self.create_entry(
            self.main_frame,
            "Font Size:",
            row=4,
            column=0,
            default_value=self.dots_config.dot_control.label.font_size,
            entry_variable=self.font_size,
            tooltip_text=
            "Set the font size for labels, either in pixels or as a percentage of the image diagonal (e.g., 12 or 10%)."
        )
        self.font_size.trace_add(
            'write', lambda *args: setattr(
                self.dots_config.dot_control.label, "font_size",
                str_to_int_safe(self.font_size.get())))

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
            browse=True)
        self.font.trace_add(
            'write', lambda *args: setattr(self.dots_config.dot_control.label,
                                           "font_path", self.font.get()))

        # Reset Button
        reset_button = ttk.Button(self.main_frame,
                                  text="Reset to Default",
                                  command=self.confirm_reset)
        reset_button.grid(row=6, column=0, columnspan=3, pady=10, sticky="ew")

    def create_entry(self,
                     params_frame,
                     label_text,
                     row,
                     column,
                     default_value,
                     entry_variable,
                     tooltip_text,
                     color_box=False,
                     browse=False):
        # Create Label
        label = ttk.Label(params_frame, text=label_text)
        label.grid(row=row, column=column, padx=5, pady=5, sticky="e")

        if color_box:
            # Create Entry for RGBA input
            entry = ttk.Entry(params_frame, textvariable=entry_variable)
            entry.grid(row=row, column=column + 1, padx=5, pady=5, sticky="w")
            Tooltip(entry, tooltip_text)

            # Use a button instead of a label for the color box
            color_box_widget = tk.Button(
                params_frame,
                bg=rgba_to_hex(entry_variable.get()),
                width=3,
                relief="sunken",
                command=lambda: self.open_color_picker(
                    entry_variable, color_box_widget, entry))
            color_box_widget.grid(row=row,
                                  column=column + 2,
                                  padx=5,
                                  pady=5,
                                  sticky="w")

            Tooltip(color_box_widget, "Click to open the color picker.")

            # Update the color box when the input field changes
            entry_variable.trace_add(
                'write', lambda *args: self.update_color_box(
                    entry_variable, color_box_widget))
        else:
            # Create Entry for other settings
            entry = ttk.Entry(params_frame, textvariable=entry_variable)
            entry.grid(row=row, column=column + 1, padx=5, pady=5, sticky="w")
            Tooltip(entry, tooltip_text)
            Tooltip(label, tooltip_text)

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

    def open_color_picker(self, color_var, color_box, entry):
        """
        Opens a color picker dialog to select a color and updates the UI.
        Updates both the input field and the color box background.
        """
        color = colorchooser.askcolor(title="Choose Color", parent=self)
        if color[1]:  # Check if a color was selected
            # Update the color variable with the selected color in RGBA format
            rgb = color[0]
            rgba = f"{int(rgb[0])},{int(rgb[1])},{int(rgb[2])},255"
            color_var.set(rgba)
            # Update the color box's background
            color_box.config(bg=rgba_to_hex(rgba))
            # Update the input field
            entry.delete(0, tk.END)
            entry.insert(0, rgba)

    def update_color_box(self, color_var, color_box):
        """
        Updates the color box based on the RGBA value from the Entry widget.
        """
        try:
            rgba_str = color_var.get()
            # Check if the RGBA format is valid
            rgba = tuple(map(int, rgba_str.split(',')))
            if len(rgba) == 4 and all(0 <= val <= 255 for val in rgba):
                hex_color = rgba_to_hex(rgba_str)
                color_box.config(bg=hex_color)
        except (ValueError, TypeError):
            # Ignore invalid input
            pass

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
        file_path = filedialog.askopenfilename(parent=self)
        if file_path:
            var.set(file_path)

    def update_ui(self):
        """Update the UI fields with the current configuration."""
        for key, _ in self.__dict__.items():
            if key.endswith("_var"):
                field_key = key[:-4]  # Remove '_var' to get the config key
                getattr(self, key).set(self.dots_config.config[field_key])

    def confirm_reset(self):
        """Display a confirmation popup and reset the configuration if confirmed."""

        def reset_action():
            # Reset the configuration using general_config's default values
            self.dots_config.reset_dot_control(self.dots_config.dot_control,
                                               self.general_config)
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
