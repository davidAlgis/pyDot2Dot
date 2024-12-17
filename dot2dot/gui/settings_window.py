import tkinter as tk
from tkinter import ttk, filedialog, messagebox, colorchooser
from dot2dot.gui.tooltip import Tooltip
from dot2dot.gui.popup_2_buttons import Popup2Buttons
from dot2dot.utils import rgba_to_hex, parse_rgba
from dot2dot.gui.utilities_gui import set_icon


class SettingsWindow(tk.Toplevel):
    """
    This class describes the window to define 
    the general configuration settings of the application.
    """

    def __init__(self, parent, config_loader):
        super().__init__(parent)
        self.parent = parent
        self.config_loader = config_loader
        self.config = config_loader.get_config()

        # Configure the window
        self.title("General Settings Configuration")
        self.geometry("600x600")
        self.resizable(True, True)
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
        self.shape_detection = tk.StringVar(
            value=self.config.get("shapeDetection", "Automatic"))
        self.distance_min = tk.StringVar(
            value=str(self.config.get("distance")[0]))
        self.distance_max = tk.StringVar(
            value=str(self.config.get("distance")[1]))
        self.font = tk.StringVar(value=self.config.get("font", ""))
        self.font_size = tk.StringVar(value=self.config.get("fontSize", ""))
        self.font_color = tk.StringVar(value=",".join(
            map(str, self.config.get("fontColor", [0, 0, 0, 255]))))
        self.dot_color = tk.StringVar(value=",".join(
            map(str, self.config.get("dotColor", [0, 0, 0, 255]))))
        self.radius = tk.StringVar(value=self.config.get("radius", ""))
        self.dpi = tk.StringVar(value=str(self.config.get("dpi", 400)))
        self.epsilon = tk.StringVar(value=str(self.config.get("epsilon", 15)))
        self.threshold_min = tk.StringVar(
            value=str(self.config.get("thresholdBinary")[0]))
        self.threshold_max = tk.StringVar(
            value=str(self.config.get("thresholdBinary")[1]))

        # Create widgets
        self.create_widgets()

        # Set protocol to save settings on close
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def create_widgets(self):
        """Create all UI widgets for configuration."""
        self.create_entry("Input Path:", "input_path", row=1, browse=True)

        self.create_combobox("Shape Detection:",
                             "shape_detection",
                             ["Automatic", "Contour", "Path"],
                             row=2)

        self.create_entry("Distance Min:", "distance_min", row=3)
        self.create_entry("Distance Max:", "distance_max", row=4)

        self.create_entry("Font:", "font", row=5, browse=True)
        self.create_entry("Font Size:", "font_size", row=6)

        self.create_entry("Font Color (RGBA):",
                          "font_color",
                          row=7,
                          color_box=True)
        self.create_entry("Dot Color (RGBA):",
                          "dot_color",
                          row=8,
                          color_box=True)

        self.create_entry("Radius:", "radius", row=9)
        self.create_entry("DPI:", "dpi", row=10)
        self.create_entry("Epsilon:", "epsilon", row=11)

        self.create_entry("Threshold Min:", "threshold_min", row=12)
        self.create_entry("Threshold Max:", "threshold_max", row=13)

        # Reset Button
        reset_button = ttk.Button(self.main_frame,
                                  text="Reset to Default",
                                  command=self.confirm_reset)
        reset_button.grid(row=14, column=0, columnspan=3, pady=10, sticky="ew")

    def create_entry(self,
                     label_text,
                     variable_name,
                     row,
                     browse=False,
                     color_box=False):
        """Create an entry widget with optional browse and color picker features."""
        var = getattr(self, variable_name)

        # Create label
        label = ttk.Label(self.main_frame, text=label_text)
        label.grid(row=row, column=0, padx=5, pady=5, sticky="e")

        # Entry for input
        entry = ttk.Entry(self.main_frame, textvariable=var)
        entry.grid(row=row, column=1, padx=5, pady=5, sticky="ew")

        if color_box:
            # Color box button
            color_box_widget = tk.Button(
                self.main_frame,
                bg=rgba_to_hex(var.get()),
                width=3,
                relief="sunken",
                command=lambda: self.open_color_picker(var, color_box_widget,
                                                       entry))
            color_box_widget.grid(row=row,
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
            browse_button.grid(row=row, column=2, padx=5, pady=5)

    def create_combobox(self, label_text, variable_name, values, row):
        """Create a combobox for selecting predefined options."""
        var = getattr(self, variable_name)

        label = ttk.Label(self.main_frame, text=label_text)
        label.grid(row=row, column=0, padx=5, pady=5, sticky="e")

        combobox = ttk.Combobox(self.main_frame,
                                textvariable=var,
                                values=values,
                                state="readonly")
        combobox.grid(row=row, column=1, padx=5, pady=5, sticky="ew")

    def open_color_picker(self, color_var, color_box, entry):
        """Open a color picker dialog and update the color variable."""
        color = colorchooser.askcolor(title="Choose Color")
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
        file_path = filedialog.askopenfilename()
        if file_path:
            var.set(file_path)

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
        self.destroy()
