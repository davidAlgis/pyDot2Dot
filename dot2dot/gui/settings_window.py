import tkinter as tk
from tkinter import ttk
from tkinter import filedialog, messagebox, colorchooser
from dot2dot.gui.popup_2_buttons import Popup2Buttons
from dot2dot.gui.tooltip import Tooltip
from dot2dot.gui.utilities_gui import set_icon
from dot2dot.utils import rgba_to_hex, parse_rgba


class SettingsWindow(tk.Toplevel):

    def __init__(self, parent, config_loader):
        super().__init__(parent)
        self.parent = parent
        self.config_loader = config_loader
        self.config = config_loader.get_config()

        # Configure the window
        self.title("Settings Configuration")
        self.geometry("600x600")
        set_icon(self)
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
            ("Change the default settings used by each new project when the executable is opened:"
             ),
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
            # Handle list-based configuration keys
            value = self.config.get(config_key, [])[index]
            var.set(str(value))

            if config_key == "thresholdBinary":
                # For 'thresholdBinary', convert input to integer
                var.trace_add(
                    "write", lambda *args: self.config_loader.set_config_value(
                        config_key, int(var.get()), index))
            else:
                # For 'distance', keep it as string
                var.trace_add(
                    "write", lambda *args: self.config_loader.set_config_value(
                        config_key, var.get(), index))
        else:
            if config_key in ["fontColor", "dotColor"]:
                # Handle color fields
                rgba_list = self.config.get(config_key, [0, 0, 0, 255])
                var.set(','.join(map(str, rgba_list)))
                var.trace_add(
                    "write", lambda *args: self.config_loader.set_config_value(
                        config_key, parse_rgba(var.get())))
            else:
                # Handle standard fields
                var.set(self.config.get(config_key, ""))
                var.trace_add(
                    "write", lambda *args: self.config_loader.set_config_value(
                        config_key, var.get()))

        if config_key in ["fontColor", "dotColor"]:
            # Create Entry for RGBA input
            entry = ttk.Entry(self.main_frame, textvariable=var)
            entry.grid(row=row, column=1, padx=5, pady=5, sticky="ew")
            Tooltip(
                entry,
                f"Set the RGBA color for {label_text.split()[0].lower()}.")

            # Use a button as the color box
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
            Tooltip(color_box_widget, "Click to open the color picker.")

            # Update the color box when the input field changes
            var.trace_add(
                'write',
                lambda *args: self.update_color_box(var, color_box_widget))
        else:
            # Create standard entry for other fields
            entry = ttk.Entry(self.main_frame, textvariable=var)
            entry.grid(row=row, column=1, padx=5, pady=5, sticky="ew")
            Tooltip(entry, f"Set the {label_text.split()[0].lower()}.")

            if browse:
                browse_button = ttk.Button(
                    self.main_frame,
                    text="Browse",
                    command=lambda: self.browse_file(var))
                browse_button.grid(row=row,
                                   column=2,
                                   padx=5,
                                   pady=5,
                                   sticky="w")
                Tooltip(browse_button, "Browse to select a file.")

    def open_color_picker(self, color_var, color_box, entry):
        """
        Opens a color picker dialog to select a color and updates the UI.
        Updates both the input field and the color box background.
        """
        color = colorchooser.askcolor(title="Choose Color")
        if color[1]:  # Check if a color was selected
            # Extract RGB values and append alpha value
            rgb = color[0]
            rgba_str = f"{int(rgb[0])},{int(rgb[1])},{int(rgb[2])},255"
            # Parse the RGBA string into a list of integers
            rgba = parse_rgba(rgba_str)
            # Update the color variable with the parsed RGBA list
            color_var.set(','.join(map(str, rgba)))
            # Update the color box's background
            color_box.config(bg=rgba_to_hex(','.join(map(str, rgba))))
            # Update the input field
            entry.delete(0, tk.END)
            entry.insert(0, ','.join(map(str, rgba)))

        # Bring the window to the front
        self.lift()
        self.focus_set()

    def update_color_box(self, color_var, color_box):
        """
        Updates the color box based on the RGBA value from the Entry widget.
        """
        try:
            rgba_str = color_var.get()
            rgba = parse_rgba(rgba_str)  # Ensure we parse to list
            if len(rgba) == 4 and all(0 <= val <= 255 for val in rgba):
                hex_color = rgba_to_hex(','.join(map(str, rgba)))
                color_box.config(bg=hex_color)
            else:
                # Reset to default color if invalid
                color_box.config(bg=rgba_to_hex('0,0,0,255'))
        except (ValueError, TypeError):
            # Ignore invalid input and reset color box to default
            color_box.config(bg=rgba_to_hex('0,0,0,255'))

    def create_combobox(self, label_text, config_key, values, row):
        label = ttk.Label(self.main_frame, text=label_text)
        label.grid(row=row, column=0, padx=5, pady=5, sticky="e")

        var = tk.StringVar(value=self.config.get(config_key, values[0]))
        var.trace_add(
            "write", lambda *args: self.config_loader.set_config_value(
                config_key, var.get()))

        combobox = ttk.Combobox(self.main_frame,
                                textvariable=var,
                                values=values,
                                state="readonly")
        combobox.grid(row=row, column=1, padx=5, pady=5, sticky="ew")
        Tooltip(
            combobox,
            f"Select the {label_text.split()[0].lower()} detection method.")

    def browse_file(self, var):
        file_path = filedialog.askopenfilename()
        if file_path:
            var.set(file_path)

    def update_ui(self):
        """Update the UI fields with the current configuration."""
        for widget in self.main_frame.winfo_children():
            # Update entries
            if isinstance(widget, ttk.Entry):
                var = widget.cget('textvariable')
                var_obj = self.nametowidget(var)
                key, index = self._get_config_key_and_index(widget)
                if key:
                    if index is not None:
                        value = self.config.get(key, ["", ""])[index]
                        var_obj.set(str(value))
                    else:
                        value = self.config.get(key, "")
                        if key in ["fontColor", "dotColor"]:
                            var_obj.set(','.join(map(str, value)))
                        else:
                            var_obj.set(str(value))
            # Update comboboxes
            elif isinstance(widget, ttk.Combobox):
                var = widget.cget('textvariable')
                var_obj = self.nametowidget(var)
                key = self._get_config_key(widget)
                if key:
                    value = self.config.get(key, widget['values'][0])
                    var_obj.set(str(value))
            # Update color boxes
            elif isinstance(widget,
                            tk.Button) and widget.cget('relief') == 'sunken':
                key, index = self._get_config_key_and_index(widget)
                if key:
                    if index is not None:
                        rgba = self.config.get(key, [0, 0, 0, 255])[index]
                        rgba_str = ','.join(map(str, rgba)) if isinstance(
                            rgba, list) else str(rgba)
                    else:
                        rgba = self.config.get(key, [0, 0, 0, 255])
                        rgba_str = ','.join(map(str, rgba))
                    widget.config(bg=rgba_to_hex(rgba_str))

    def _get_config_key_and_index(self, widget):
        """
        Helper method to retrieve the configuration key and index for a given widget.

        Args:
            widget: The Tkinter widget.

        Returns:
            tuple: (config_key, index) or (None, None)
        """
        # This method assumes that the widget's grid row corresponds to the config_key
        # Adjust this method based on your actual grid layout and widget association
        row = widget.grid_info().get('row')
        config_map = {
            1: ("input", None),
            2: ("shapeDetection", None),
            4: ("distance", 0),
            5: ("distance", 1),
            6: ("font", None),
            7: ("fontSize", None),
            8: ("fontColor", None),
            9: ("dotColor", None),
            10: ("radius", None),
            11: ("dpi", None),
            12: ("epsilon", None),
            13: ("thresholdBinary", 0),
            14: ("thresholdBinary", 1),
        }
        return config_map.get(int(row), (None, None))

    def _get_config_key(self, widget):
        """
        Helper method to retrieve the configuration key for a given widget.

        Args:
            widget: The Tkinter widget.

        Returns:
            str or None: The configuration key or None.
        """
        row = widget.grid_info().get('row')
        config_map = {
            2: "shapeDetection",
            # Add other combobox mappings if any
        }
        return config_map.get(int(row), None)

    def confirm_reset(self):
        """Display a confirmation popup and reset the configuration if confirmed."""

        def reset_action():
            # Reset the configuration using the config_loader's reset method
            self.config_loader.reset_config_user()
            # Fetch the updated configuration
            self.config = self.config_loader.get_config()
            # Update all input fields to reflect the reset configuration
            self.update_ui()
            messagebox.showinfo("Reset Successful",
                                "Settings have been reset to default values.")

        # Display a confirmation dialog
        Popup2Buttons(
            root=self,
            title="Confirm Reset",
            main_text=
            ("Are you sure you want to reset the settings to their default values? "
             "This action cannot be undone."),
            button1_text="Yes",
            button1_action=reset_action,
            button2_text="No")

    def on_close(self):
        # Save configuration through LoadConfig when closing the window
        self.config_loader.save_config(self.config)
        self.destroy()
