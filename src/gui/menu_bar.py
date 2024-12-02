import tkinter as tk
from tkinter import Menu, messagebox
from gui.settings_window import SettingsWindow
from metadata import read_metadata


class MenuBar:

    def __init__(self, root, main_gui, config):
        self.root = root
        self.main_gui = main_gui
        self.config = config
        self.menu_bar = Menu(root)
        root.config(menu=self.menu_bar)

        # File Menu
        file_menu = Menu(self.menu_bar, tearoff=0)
        file_menu.add_command(label="Open File...",
                              command=self.main_gui.browse_input)
        file_menu.add_command(label="Save",
                              command=self.main_gui.save_output_image)
        file_menu.add_command(label="Save As...",
                              command=self.main_gui.save_output_image)
        file_menu.add_command(label="Export As...", command=None)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.main_gui.on_close)
        self.menu_bar.add_cascade(label="File", menu=file_menu)

        # Edit Menu
        edit_menu = Menu(self.menu_bar, tearoff=0)
        # edit_menu.add_command(label="Undo", command=self.undo)
        # edit_menu.add_command(label="Redo", command=self.redo)
        # edit_menu.add_separator()
        # edit_menu.add_command(label="Cut", command=self.cut)
        # edit_menu.add_command(label="Copy", command=self.copy)
        # edit_menu.add_command(label="Paste", command=self.paste)
        self.menu_bar.add_cascade(label="Edit", menu=edit_menu)

        # View Menu
        view_menu = Menu(self.menu_bar, tearoff=0)
        # view_menu.add_command(label="Zoom In", command=self.zoom_in)
        # view_menu.add_command(label="Zoom Out", command=self.zoom_out)
        self.menu_bar.add_cascade(label="View", menu=view_menu)

        # Preferences Menu
        preferences_menu = Menu(self.menu_bar, tearoff=0)
        preferences_menu.add_command(label="Default settings",
                                     command=self._open_config_menu)
        self.menu_bar.add_cascade(label="Preferences", menu=preferences_menu)

        # Help Menu
        help_menu = Menu(self.menu_bar, tearoff=0)
        help_menu.add_command(label="About", command=self._show_about)
        help_menu.add_command(label="Help", command=self._show_help)
        help_menu.add_command(label="Report an issue",
        self.menu_bar.add_cascade(label="Help", menu=help_menu)

    def _open_config_menu(self):
        SettingsWindow(self.root, self.config)

    def _show_about(self):
        """
        Opens a popup window displaying metadata information.
        """
        try:
            metadata = read_metadata()
            about_message = f"Name: {metadata['name']}\n" \
                            f"Author: {metadata['author']}\n" \
                            f"Version: {metadata['version']}\n" \
                            f"Commit ID: {metadata['commit']}"
        except Exception as e:
            about_message = f"Error loading metadata: {str(e)}"

        messagebox.showinfo("About", about_message)

    def _show_help(self):

        messagebox.showinfo("Help",
                            "See https://github.com/davidAlgis/pyDot2Dot")

    def _report_issue(self):

        messagebox.showinfo(
            "Report an issue",
            "See https://github.com/davidAlgis/pyDot2Dot/issues/new")
