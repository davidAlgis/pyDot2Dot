import tkinter as tk
from tkinter import Menu, messagebox
from gui.settings_window import SettingsWindow
from metadata import read_metadata
from dots_saver import DotsSaver


class MenuBar:

    def __init__(self, root, main_gui, config, dots_saver):
        self.root = root
        self.main_gui = main_gui
        self.config = config
        self.dots_saver = dots_saver
        self.menu_bar = Menu(root)
        root.config(menu=self.menu_bar)

        # File Menu
        file_menu = Menu(self.menu_bar, tearoff=0)
        file_menu.add_command(label="Open File...",
                              command=self.main_gui.browse_input)
        file_menu.add_command(label="Save", command=self._save_dots)
        file_menu.add_command(label="Save As...", command=self._save_dots_as)
        file_menu.add_command(label="Export As...",
                              command=self.dots_saver.export_output_image)
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
                              command=self._report_issue)
        self.menu_bar.add_cascade(label="Help", menu=help_menu)

    def _open_config_menu(self):
        SettingsWindow(self.root, self.config)

    def _save_dots(self):
        """
        Call the save_d2d method with the dots list.
        """
        dots = self.main_gui.processed_dots
        dots_config = self.main_gui.dots_config
        if dots:
            self.dots_saver.save_d2d(dots, dots_config)
        else:
            messagebox.showerror("Error", "No dots data to save.")

    def _save_dots_as(self):
        """
        Call the save_d2d method with the dots list and prompt the user to save to a new location.
        """
        dots = self.main_gui.processed_dots
        dots_config = self.main_gui.dots_config
        if dots:
            self.dots_saver.save_d2d_as(dots, dots_config)
        else:
            messagebox.showerror("Error", "No dots data to save.")

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
