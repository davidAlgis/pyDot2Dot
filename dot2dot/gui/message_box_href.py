import tkinter as tk
import webbrowser
from tkinter import font


class MessageBoxHref:

    @staticmethod
    def showinfo(title, content, url):
        """
        Displays a message box with a clickable URL seamlessly integrated into the content.

        :param title: The title of the message box.
        :param content: The content of the message box.
        :param url: The URL to open when clicked.
        """
        # Create a Toplevel window for the message box
        # Calculate the dimensions of the window based on content length
        content_font = font.Font(family="TkDefaultFont")
        content_width = max(content_font.measure(content),
                            content_font.measure(url))
        window_width = min(max(content_width + 50, 300),
                           600)  # Set min/max bounds for width
        window_height = 100 + (len(content) //
                               50) * 20  # Adjust height based on text length
        window = tk.Toplevel()
        window.title(title)
        window.geometry(f"{window_width}x{window_height}")
        # window.geometry("300x150")  # Set the size of the window
        window.resizable(False, False)

        # Frame for content and link
        frame = tk.Frame(window)
        frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        # Add content text and clickable URL
        full_text = f"{content} "
        content_label = tk.Label(frame,
                                 text=full_text,
                                 wraplength=250,
                                 justify="left")
        content_label.pack(side=tk.LEFT, anchor="w")

        # Add the clickable URL as part of the same line
        link_label = tk.Label(frame, text=url, fg="blue", cursor="hand2")
        link_label.pack(side=tk.LEFT, anchor="w")

        # Bind the link to open in a browser
        def open_url(event):
            webbrowser.open_new(url)

        link_label.bind("<Button-1>", open_url)

        # Ensure the message box stays on top
        window.transient()
        window.grab_set()
        window.wait_window()
