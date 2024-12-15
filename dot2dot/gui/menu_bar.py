"""
This module implement the menu bar in main window
"""
from tkinter import Menu, messagebox
from dot2dot.gui.settings_window import SettingsWindow
from dot2dot.gui.aspect_settings_window import AspectSettingsWindow
from dot2dot.gui.message_box_href import MessageBoxHref
from metadata import read_metadata


class MenuBar:
    """
    This class implement the menu bar in main window
    """

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
                              command=self.main_gui.load_input_threaded,
                              accelerator="Ctrl+O")
        self.root.bind("<Control-o>", self._on_open_shortcut)
        file_menu.add_command(label="Save",
                              command=self._save_dots,
                              accelerator="Ctrl+S")
        self.root.bind("<Control-s>", self._on_save_shortcut)
        file_menu.add_command(label="Save As...",
                              command=self._save_dots_as,
                              accelerator="Ctrl+Shift+S")
        self.root.bind("<Control-Shift-s>", self._on_save_as_shortcut)
        file_menu.add_command(label="Export As...",
                              command=self.dots_saver.export_output_image,
                              accelerator="Ctrl+E")
        self.root.bind("<Control-e>", self._on_export_shortcut)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.main_gui.on_close)
        self.menu_bar.add_cascade(label="File", menu=file_menu)

        # Edit Menu
        edit_menu = Menu(self.menu_bar, tearoff=0)
        edit_menu.add_command(label="Dot and Label Aspect",
                              command=self._show_dot_label_aspect_window)
        edit_menu.add_command(label="Process Current Input",
                              command=self.main_gui.process_threaded,
                              accelerator="Alt+P")
        self.root.bind("<Alt-p>", self._on_process_shortcut)
        edit_menu.add_command(label="Edit Output",
                              command=self.main_gui.open_edit_window,
                              accelerator="Alt+E")
        self.root.bind("<Alt-e>", self._on_edit_shortcut)
        self.menu_bar.add_cascade(label="Edit", menu=edit_menu)

        # View Menu
        # view_menu = Menu(self.menu_bar, tearoff=0)
        # self.menu_bar.add_cascade(label="View", menu=view_menu)

        # Preferences Menu
        preferences_menu = Menu(self.menu_bar, tearoff=0)
        preferences_menu.add_command(label="Default Settings",
                                     command=self._open_config_menu)
        self.menu_bar.add_cascade(label="Preferences", menu=preferences_menu)

        # Help Menu
        help_menu = Menu(self.menu_bar, tearoff=0)
        help_menu.add_command(label="About", command=self._show_about)
        help_menu.add_command(label="Help", command=self._show_help)
        help_menu.add_command(label="Report an Issue",
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

    def _show_dot_label_aspect_window(self):
        AspectSettingsWindow(self.root, self.main_gui.dots_config, self.config)

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

        MessageBoxHref.showinfo(
            "Help", "See ",
            "https://github.com/davidAlgis/pyDot2Dot/blob/main/documentations/software.md"
        )

    def _report_issue(self):

        MessageBoxHref.showinfo(
            "Report an issue", "See ",
            "https://github.com/davidAlgis/pyDot2Dot/issues/new")

    # Shortcut functions
    def _on_open_shortcut(self, _=None):
        self.main_gui.load_input_threaded()

    def _on_save_shortcut(self, _=None):
        self._save_dots()

    def _on_save_as_shortcut(self, _=None):
        self._save_dots_as()

    def _on_export_shortcut(self, _=None):
        self.dots_saver.export_output_image()

    def _on_edit_shortcut(self, _=None):
        self.main_gui.open_edit_window()

    def _on_process_shortcut(self, _=None):
        self.main_gui.process_threaded()
