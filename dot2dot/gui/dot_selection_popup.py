import tkinter as tk
from tkinter import Toplevel, Frame, Button, messagebox, ttk


class DotSelectionPopup:
    """
    A helper class to create a popup window for selecting a dot from a combobox, 
    optionally inputting a new value, and applying changes.

    Parameters:
    - parent: The parent window (e.g., self.window in EditWindow).
    - title: Title of the popup window.
    - label_text: Text label explaining what is being selected.
    - dot_numbers: List of dot labels (e.g. ["Dot 1", "Dot 2", ...]).
    - on_apply: A callback function to be called when "Apply" is clicked.
      This callback should accept two parameters:
        (selected_index, input_value) where input_value can be None if no input field is present.
    - input_label_text: If provided, creates a label and entry field for user input.
    - input_default_value: If provided, sets the default value of the input field.
    """

    def __init__(self,
                 parent,
                 title,
                 label_text,
                 dot_numbers,
                 on_apply,
                 input_label_text=None,
                 input_default_value=None):

        self.parent = parent
        self.on_apply = on_apply
        self.input_label_text = input_label_text

        self.popup = tk.Toplevel(parent)
        self.popup.title(title)
        self.popup.grab_set()  # Make the popup modal

        # Message Label
        message_label = tk.Label(self.popup,
                                 text=label_text,
                                 wraplength=300,
                                 justify='left')
        message_label.pack(padx=20, pady=20)

        # Dropdown (Combobox) with dot numbers
        self.dot_var = tk.StringVar()
        if dot_numbers:
            self.dot_var.set(dot_numbers[0])  # Default selection
        dropdown = ttk.Combobox(self.popup,
                                textvariable=self.dot_var,
                                values=dot_numbers,
                                state='readonly')
        dropdown.pack(padx=20, pady=10)

        self.input_entry = None
        if self.input_label_text is not None:
            # Input field frame
            input_frame = tk.Frame(self.popup)
            input_frame.pack(padx=20, pady=10, fill='x')

            input_label = tk.Label(input_frame, text=self.input_label_text)
            input_label.pack(side=tk.LEFT)

            self.input_entry = tk.Entry(input_frame)
            self.input_entry.pack(side=tk.LEFT, padx=5)
            if input_default_value is not None:
                self.input_entry.insert(0, str(input_default_value))

            # Allow optional behavior on combobox change, if needed.
            # The callback can be provided by the caller by re-binding the dropdown
            # after the popup is created, if necessary.

        # Button Frame
        button_frame = tk.Frame(self.popup)
        button_frame.pack(padx=20, pady=20)

        # Cancel Button
        cancel_button = tk.Button(button_frame,
                                  text="Cancel",
                                  width=10,
                                  command=self.popup.destroy)
        cancel_button.pack(side=tk.LEFT, padx=5)

        # Apply Button
        apply_button = tk.Button(button_frame,
                                 text="Apply",
                                 width=10,
                                 command=self._on_apply_clicked)
        apply_button.pack(side=tk.LEFT, padx=5)

    def _on_apply_clicked(self):
        selected_dot_text = self.dot_var.get()
        if not selected_dot_text:
            # No selection made
            self.popup.destroy()
            return

        selected_index = int(selected_dot_text.split()[1]) - 1
        input_value = None
        if self.input_entry is not None:
            val = self.input_entry.get().strip()
            input_value = val if val else None

        self.on_apply(selected_index, input_value)
        self.popup.destroy()
