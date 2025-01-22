import tkinter as tk
from tkinter import ttk, filedialog, messagebox, colorchooser
from screeninfo import get_monitors

from dot2dot.gui.tooltip import Tooltip
from dot2dot.gui.popup_2_buttons import Popup2Buttons
from dot2dot.utils import rgba_to_hex, parse_rgba, str_to_int_safe, find_font_in_windows
from dot2dot.gui.utilities_gui import set_icon
from dot2dot.dots_config import DotsConfig
from dot2dot.gui.utilities_gui import get_screen_choice, set_screen_choice


class SettingsWindow(tk.Toplevel):
    """
    This class describes the window to define 
    the general configuration settings of the application.
    """

    def __init__(self, parent, main_gui, config_loader):
        super().__init__(parent)
        self.parent = parent
        self.config_loader = config_loader
        self.config = config_loader.get_config()
        self.main_gui = main_gui
        self.row_index = 0
        # Configure the window
        self.title("General Settings Configuration")
        self.geometry("600x600")
        self.resizable(True, True)

        # Make the window stay on top
        self.attributes("-topmost", True)
        set_icon(self)

        # Create main frame
        self.main_frame = ttk.Frame(self, padding=10)
        self.main_frame.grid(sticky="nsew")

        # Configure layout for window
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.main_frame.columnconfigure(1, weight=1)

        # Add configuration variables
        self.input_path = tk.StringVar(value=self.config.get("input", ""))
        self.input_path.trace_add(
            'write',
            lambda *args: self.update_config("input", self.input_path.get()))

        self.shape_detection = tk.StringVar(
            value=self.config.get("shapeDetection", "Automatic"))
        self.shape_detection.trace_add(
            'write', lambda *args: self.update_config(
                "shapeDetection", self.shape_detection.get()))

        self.distance_min = tk.StringVar(
            value=str(self.config.get("distance")[0]))
        self.distance_min.trace_add(
            'write',
            lambda *args: self.update_config("distance", self.distance_min.get(
            ), 0))

        self.distance_max = tk.StringVar(
            value=str(self.config.get("distance")[1]))
        self.distance_max.trace_add(
            'write',
            lambda *args: self.update_config("distance", self.distance_max.get(
            ), 1))

        self.font = tk.StringVar(value=self.config.get("font", ""))
        self.font.trace_add(
            'write', lambda *args: self.update_config("font", self.font.get()))

        self.font_size = tk.StringVar(value=self.config.get("fontSize", ""))
        self.font_size.trace_add(
            'write',
            lambda *args: self.update_config("fontSize", self.font_size.get()))

        self.font_color = tk.StringVar(value=",".join(
            map(str, self.config.get("fontColor", [0, 0, 0, 255]))))
        self.font_color.trace_add(
            'write', lambda *args: self.update_config(
                "fontColor", parse_rgba(self.font_color.get())))

        self.dot_color = tk.StringVar(value=",".join(
            map(str, self.config.get("dotColor", [0, 0, 0, 255]))))
        self.dot_color.trace_add(
            'write', lambda *args: self.update_config(
                "dotColor", parse_rgba(self.dot_color.get())))

        self.radius = tk.StringVar(value=self.config.get("radius", ""))
        self.radius.trace_add(
            'write',
            lambda *args: self.update_config("radius", self.radius.get()))

        self.dpi = tk.StringVar(value=str(self.config.get("dpi", 400)))
        self.dpi.trace_add(
            'write', lambda *args: self.config_loader.set_config_value(
                "dpi", str_to_int_safe(self.dpi.get()), None))

        self.epsilon = tk.StringVar(value=str(self.config.get("epsilon", 15)))
        self.epsilon.trace_add(
            'write', lambda *args: self.config_loader.set_config_value(
                "epsilon", str_to_int_safe(self.epsilon.get()), None))

        self.threshold_min = tk.StringVar(
            value=str(self.config.get("thresholdBinary")[0]))
        self.threshold_min.trace_add(
            'write', lambda *args: self.config_loader.set_config_value(
                "thresholdBinary", str_to_int_safe(self.threshold_min.get()), 0
            ))

        self.threshold_max = tk.StringVar(
            value=str(self.config.get("thresholdBinary")[1]))
        self.threshold_max.trace_add(
            'write', lambda *args: self.config_loader.set_config_value(
                "thresholdBinary", str_to_int_safe(self.threshold_max.get()), 1
            ))

        # Create widgets
        self.create_widgets()

        # Set protocol to save settings on close
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def create_widgets(self):
        """Create all UI widgets for configuration."""
        self.create_entry("Input Path:", "input_path", browse=True)

        self.create_combobox("Shape Detection:", "shape_detection",
                             ["Automatic", "Contour", "Path"])

        self.create_entry("Distance Min:", "distance_min")
        self.create_entry("Distance Max:", "distance_max")

        self.create_entry("Font:", "font", browse=True)
        self.create_entry("Font Size:", "font_size")

        self.create_entry("Font Color (RGBA):", "font_color", color_box=True)
        self.create_entry("Dot Color (RGBA):", "dot_color", color_box=True)

        self.create_entry("Radius:", "radius")
        self.create_entry("DPI:", "dpi")
        self.create_entry("Epsilon:", "epsilon")

        self.create_entry("Threshold Min:", "threshold_min")
        self.create_entry("Threshold Max:", "threshold_max")

        self.create_screen_choice_option(self.main_frame)
        # Reset Button
        reset_button = ttk.Button(self.main_frame,
                                  text="Reset to Default",
                                  command=self.confirm_reset)
        reset_button.grid(row=self.row_index,
                          column=0,
                          columnspan=3,
                          pady=10,
                          sticky="ew")

    def create_entry(self,
                     label_text,
                     variable_name,
                     browse=False,
                     color_box=False):
        """Create an entry widget with optional browse and color picker features."""
        var = getattr(self, variable_name)

        # Create label
        label = ttk.Label(self.main_frame, text=label_text)
        label.grid(row=self.row_index, column=0, padx=5, pady=5, sticky="e")

        # Entry for input
        entry = ttk.Entry(self.main_frame, textvariable=var)
        entry.grid(row=self.row_index, column=1, padx=5, pady=5, sticky="ew")

        if color_box:
            # Color box button
            color_box_widget = tk.Button(
                self.main_frame,
                bg=rgba_to_hex(var.get()),
                width=3,
                relief="sunken",
                command=lambda: self.open_color_picker(var, color_box_widget,
                                                       entry))
            color_box_widget.grid(row=self.row_index,
                                  column=2,
                                  padx=5,
                                  pady=5,
                                  sticky="w")

            var.trace_add(
                'write',
                lambda *args: self.update_color_box(var, color_box_widget))

        if browse:
            browse_button = ttk.Button(self.main_frame,
                                       text="Browse",
                                       command=lambda: self.browse_file(var))
            browse_button.grid(row=self.row_index, column=2, padx=5, pady=5)
        self.row_index += 1

    def create_combobox(self, label_text, variable_name, values):
        """Create a combobox for selecting predefined options."""
        var = getattr(self, variable_name)

        label = ttk.Label(self.main_frame, text=label_text)
        label.grid(row=self.row_index, column=0, padx=5, pady=5, sticky="e")

        combobox = ttk.Combobox(self.main_frame,
                                textvariable=var,
                                values=values,
                                state="readonly")
        combobox.grid(row=self.row_index,
                      column=1,
                      padx=5,
                      pady=5,
                      sticky="ew")
        self.row_index += 1

    def open_color_picker(self, color_var, color_box, entry):
        """Open a color picker dialog and update the color variable."""
        color = colorchooser.askcolor(title="Choose Color", parent=self)
        if color[1]:  # Check if a color was selected
            rgb = color[0]
            rgba = f"{int(rgb[0])},{int(rgb[1])},{int(rgb[2])},255"
            color_var.set(rgba)
            color_box.config(bg=rgba_to_hex(rgba))
            entry.delete(0, tk.END)
            entry.insert(0, rgba)

    def update_color_box(self, color_var, color_box):
        """Update the color box background based on the current RGBA value."""
        try:
            rgba = parse_rgba(color_var.get())
            color_box.config(bg=rgba_to_hex(",".join(map(str, rgba))))
        except (ValueError, TypeError):
            pass

    def browse_file(self, var):
        """Open a file dialog and update the variable."""
        file_path = filedialog.askopenfilename(parent=self)
        if file_path:
            var.set(file_path)

    def update_config(self, key, value, index=None):
        """Update the configuration through config_loader."""
        self.config_loader.set_config_value(key, value, index)

    def confirm_reset(self):
        """Reset the user configuration and update the UI."""

        def reset_action():
            self.config_loader.reset_config_user()
            self.config = self.config_loader.get_config()
            self.update_ui()
            messagebox.showinfo("Reset Successful",
                                "Settings have been reset to default values.")

        Popup2Buttons(
            root=self,
            title="Confirm Reset",
            main_text="Are you sure you want to reset settings to defaults?",
            button1_text="Yes",
            button1_action=reset_action,
            button2_text="No")

    def update_ui(self):
        """Update the UI with the current configuration."""
        self.input_path.set(self.config.get("input", ""))
        self.shape_detection.set(self.config.get("shapeDetection",
                                                 "Automatic"))
        self.distance_min.set(str(self.config.get("distance")[0]))
        self.distance_max.set(str(self.config.get("distance")[1]))
        self.font.set(self.config.get("font", ""))
        self.font_size.set(self.config.get("fontSize", ""))
        self.font_color.set(",".join(map(str, self.config.get("fontColor"))))
        self.dot_color.set(",".join(map(str, self.config.get("dotColor"))))
        self.radius.set(self.config.get("radius", ""))
        self.dpi.set(str(self.config.get("dpi", 400)))
        self.epsilon.set(str(self.config.get("epsilon", 15)))
        self.threshold_min.set(str(self.config.get("thresholdBinary")[0]))
        self.threshold_max.set(str(self.config.get("thresholdBinary")[1]))

    def on_close(self):
        """Save the configuration and close the window."""
        self.config_loader.save_config(self.config)

        def apply_to_current_dot_config():
            # Reset the configuration using general_config's default values
            self.main_gui.dots_config = DotsConfig.default_dots_config(
                self.config)

            set_screen_choice(self.main_gui.root, self.config)

        Popup2Buttons(
            root=self,
            title="Confirm Apply",
            main_text=
            "Do you want to apply this new settings to the current configuration ?",
            button1_text="Yes",
            button1_action=apply_to_current_dot_config,
            button2_text="No")

        self.destroy()

    def create_screen_choice_option(self, frame):
        """
        Add screen selection option to the settings window.
        """
        label = ttk.Label(self.main_frame, text="Select Screen:")
        label.grid(row=self.row_index, column=0, padx=5, pady=5, sticky="e")

        # Get the current screen choice from the config
        current_screen_choice = self.config.get("screenChoice", 0)
        screen_choice_var = tk.IntVar(value=current_screen_choice)

        # Update the configuration when the dropdown selection changes
        def save_screen_choice(event=None):
            selected_index = dropdown.current(
            )  # Get the current selected index
            if selected_index >= 0:  # Ensure a valid selection
                screen_choice_var.set(selected_index)
                self.update_config("screenChoice", selected_index)

        # Get monitor information for the dropdown options
        monitors = get_monitors()
        screen_options = [
            f"{i}: {m.width}x{m.height} ({m.x},{m.y})"
            for i, m in enumerate(monitors)
        ]

        # Create the dropdown and set the current value
        dropdown = ttk.Combobox(frame, values=screen_options, state="readonly")
        dropdown.set(screen_options[current_screen_choice])
        dropdown.grid(row=self.row_index, column=1, sticky="ew", pady=5)

        # Bind the save_screen_choice function to the dropdown selection event
        dropdown.bind("<<ComboboxSelected>>", save_screen_choice)

        self.row_index += 1
