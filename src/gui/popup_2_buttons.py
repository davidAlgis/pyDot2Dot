import tkinter as tk


class Popup2Buttons:

    def __init__(self,
                 root,
                 title,
                 main_text,
                 button1_text="Yes",
                 button1_action=lambda: None,
                 button2_text="No",
                 button2_action=lambda: None):
        self.root = root
        self.title = title
        self.main_text = main_text
        self.button1_text = button1_text
        self.button1_action = button1_action
        self.button2_text = button2_text
        self.button2_action = button2_action
        self.create_popup()

    def create_popup(self):
        # Create a confirmation popup
        popup = tk.Toplevel(self.root)
        popup.title(self.title)
        popup.transient(self.root)  # Set to be on top of the main window
        popup.grab_set()  # Make the popup modal

        # Message Label
        tk.Label(popup, text=self.main_text).pack(padx=20, pady=20)

        # Button Frame
        button_frame = tk.Frame(popup)
        button_frame.pack(padx=20, pady=10)

        # Button 1
        tk.Button(button_frame,
                  text=self.button1_text,
                  width=10,
                  command=lambda: [popup.destroy(),
                                   self.button1_action()]).pack(side=tk.LEFT,
                                                                padx=5)

        # Button 2
        tk.Button(button_frame,
                  text=self.button2_text,
                  width=10,
                  command=lambda: [popup.destroy(),
                                   self.button2_action()]).pack(side=tk.LEFT,
                                                                padx=5)

        # Wait for the popup to close before returning
        self.root.wait_window(popup)
