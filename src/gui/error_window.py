# gui/error_window.py

import tkinter as tk
from tkinter import ttk, messagebox, filedialog


class ErrorWindow:

    def __init__(self, master, stack_trace):
        """
        Initializes the ErrorWindow to display the stack trace.

        Parameters:
        - master: The parent Tkinter window.
        - stack_trace: The stack trace string to display.
        """
        self.master = master
        self.stack_trace = stack_trace

        # Create a new top-level window
        self.window = tk.Toplevel(master)
        self.window.title("Error Details")
        self.window.geometry("800x600")  # Set a default size
        self.window.resizable(True, True)

        # Make sure the window is on top and modal
        self.window.transient(master)
        self.window.grab_set()

        # Configure grid layout
        self.window.columnconfigure(0, weight=1)
        self.window.rowconfigure(1, weight=1)

        # Header Frame
        header_frame = ttk.Frame(self.window, padding="10 10 10 10")
        header_frame.grid(row=0, column=0, sticky="ew")
        header_frame.columnconfigure(0, weight=1)

        # Header Label
        header_label = ttk.Label(header_frame,
                                 text="An unexpected error has occurred:",
                                 font=("Helvetica", 14, "bold"))
        header_label.grid(row=0, column=0, sticky="w")

        # Instruction Label
        instruction_label = ttk.Label(
            header_frame,
            text="Below is the detailed stack trace for debugging purposes:",
            font=("Helvetica", 10))
        instruction_label.grid(row=1, column=0, sticky="w", pady=(5, 0))

        # Text Frame with Scrollbars
        text_frame = ttk.Frame(self.window)
        text_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        text_frame.columnconfigure(0, weight=1)
        text_frame.rowconfigure(0, weight=1)

        # Vertical Scrollbar
        v_scroll = ttk.Scrollbar(text_frame, orient=tk.VERTICAL)
        v_scroll.grid(row=0, column=1, sticky="ns")

        # Horizontal Scrollbar
        h_scroll = ttk.Scrollbar(text_frame, orient=tk.HORIZONTAL)
        h_scroll.grid(row=1, column=0, sticky="ew")

        # Text Widget
        self.text_area = tk.Text(text_frame,
                                 wrap='none',
                                 bg='black',
                                 fg='white',
                                 font=("Courier New", 10),
                                 undo=True)
        self.text_area.grid(row=0, column=0, sticky="nsew")

        # Configure scrollbars
        self.text_area.config(yscrollcommand=v_scroll.set,
                              xscrollcommand=h_scroll.set)
        v_scroll.config(command=self.text_area.yview)
        h_scroll.config(command=self.text_area.xview)

        # Insert the stack trace
        self.text_area.insert(tk.END, self.stack_trace)
        self.text_area.config(state='disabled')  # Make the text read-only

        # Button Frame
        button_frame = ttk.Frame(self.window, padding="10 10 10 10")
        button_frame.grid(row=2, column=0, sticky="e")

        # Copy Button
        copy_button = ttk.Button(button_frame,
                                 text="Copy to Clipboard",
                                 command=self.copy_to_clipboard)
        copy_button.grid(row=0, column=0, padx=5, pady=5)

        # Save Button
        save_button = ttk.Button(button_frame,
                                 text="Save to File",
                                 command=self.save_to_file)
        save_button.grid(row=0, column=1, padx=5, pady=5)

        # Close Button
        close_button = ttk.Button(button_frame,
                                  text="Close",
                                  command=self.close_window)
        close_button.grid(row=0, column=2, padx=5, pady=5)

    def copy_to_clipboard(self):
        """
        Copies the stack trace to the clipboard.
        """
        try:
            self.text_area.config(state='normal')
            self.window.clipboard_clear()
            self.window.clipboard_append(self.stack_trace)
            self.text_area.config(state='disabled')
            messagebox.showinfo("Copied", "Stack trace copied to clipboard.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to copy to clipboard:\n{e}")

    def save_to_file(self):
        """
        Saves the stack trace to a user-selected file.
        """
        try:
            file_path = filedialog.asksaveasfilename(defaultextension=".txt",
                                                     filetypes=[("Text Files",
                                                                 "*.txt"),
                                                                ("All Files",
                                                                 "*.*")],
                                                     title="Save Stack Trace")
            if file_path:
                with open(file_path, 'w') as file:
                    file.write(self.stack_trace)
                messagebox.showinfo("Saved",
                                    f"Stack trace saved to {file_path}.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save to file:\n{e}")

    def close_window(self):
        """
        Closes the error window.
        """
        self.window.destroy()
