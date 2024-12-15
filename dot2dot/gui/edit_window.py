import tkinter as tk
import tkinter.filedialog as fd
from tkinter import Frame, Button, messagebox, ttk
from PIL import Image, ImageFont, ImageDraw, ImageTk
from dot2dot.dot import Dot
from dot2dot.dot_label import DotLabel
from dot2dot.gui.tooltip import Tooltip
from dot2dot.utils import distance_to_segment, rgba_to_hex
from dot2dot.grid_dots import GridDots
from dot2dot.gui.display_window_base import DisplayWindowBase
from dot2dot.gui.dot_selection_popup import DotSelectionPopup


class EditWindow(DisplayWindowBase):

    def __init__(
            self,
            master,
            dots,
            dot_control,
            image_width,
            image_height,
            input_image,  # Expected to be a PIL Image object or image path
            apply_callback=None):
        """
        Initializes the EditWindow to allow editing of dots and labels.

        Parameters:
        - master: The parent Tkinter window.
        - dots: List of Dot objects.
        - dot_control: Dot configuration object controlling radius, label font, etc.
        - image_width: Width of the image.
        - image_height: Height of the image.
        - input_image: PIL Image object or file path to be used as the background.
        - apply_callback: Function to call when 'Apply' is clicked.
        """
        super().__init__(master,
                         title="Edit Dots and Labels",
                         width=image_width,
                         height=image_height)

        # Override canvas dimensions set by the base class
        self.canvas_width = image_width
        self.canvas_height = image_height
        self.update_scrollregion(self.canvas_width, self.canvas_height)

        self.apply_callback = apply_callback
        self.dots = dots
        self.dot_control = dot_control
        self.overlap_color = (255, 0, 0, 255)  # RGBA for red
        self.add_hoc_offset_y_label = 15
        self.show_labels_var = tk.BooleanVar(value=True)
        self.link_dots_var = tk.BooleanVar(value=False)
        self.bg_opacity = 0.1  # Default to partially transparent
        self.nu = 50

        # Setup GridDots to detect overlaps
        self.grid = GridDots(image_width, image_height, 80, dots)
        overlaps = self.grid.find_all_overlaps()
        for obj in overlaps:
            obj.color = self.overlap_color

        # Load and prepare the background image
        self.original_image = self._load_input_image(input_image, image_width,
                                                     image_height)

        self.last_selected_dot_index = None
        self.selected_dot_index = None
        self.selected_label_index = None
        self.offset_x = 0
        self.offset_y = 0
        self.selected_label_offset_x = 0
        self.selected_label_offset_y = 0

        self.anchor_mapping = {
            'ls': 'sw',  # left, baseline
            'rs': 'se',  # right, baseline
            'ms': 's',  # center, baseline
        }

        # Bind mouse events for dragging dots and labels
        self.canvas.bind('<ButtonPress-1>', self.on_left_button_press)
        self.canvas.bind('<B1-Motion>', self.on_mouse_move)
        self.canvas.bind('<ButtonRelease-1>', self.on_left_button_release)
        self.window.bind('<Delete>', self.on_delete_key_press)
        self.window.bind('<Key-Delete>', self.on_delete_key_press)
        self.window.bind('<KeyPress-Delete>', self.on_delete_key_press)
        self.canvas.bind("<Double-1>", self.on_double_click)

        # Adjust the initial view to show all dots and labels
        self.fit_canvas_to_content()

        # Add overlay buttons and the opacity slider
        self.add_overlay_buttons()

    def _load_input_image(self, input_image, image_width, image_height):
        if isinstance(input_image, str):
            try:
                img = Image.open(input_image).convert("RGBA")
            except IOError:
                messagebox.showerror("Error",
                                     f"Cannot open image: {input_image}")
                img = Image.new("RGBA", (image_width, image_height),
                                (255, 255, 255, 255))
        elif isinstance(input_image, Image.Image):
            img = input_image.convert("RGBA")
        else:
            messagebox.showerror("Error", "Invalid input_image provided.")
            img = Image.new("RGBA", (image_width, image_height),
                            (255, 255, 255, 255))

        # Ensure the background image matches the specified dimensions
        if img.size != (image_width, image_height):
            resample_method = Image.Resampling.LANCZOS
            img = img.resize((image_width, image_height), resample_method)

        return img

    def redraw_canvas(self, skip_background=False):
        """
        Clears and redraws the canvas contents based on the current scale and opacity.
        If skip_background is True, it skips redrawing the background for performance.
        """
        self.canvas.delete("all")
        if not skip_background:
            self.draw_background()
        self._draw_dots_and_labels()
        if self.link_dots_var.get():
            self.draw_link_lines()

    def draw_background(self):
        """
        Draws the background image on the canvas with the current opacity.
        """
        if self.bg_opacity < 1.0:
            # Create a copy with adjusted opacity
            bg_image = self.original_image.copy()
            alpha = bg_image.split()[3]
            alpha = alpha.point(lambda p: p * self.bg_opacity)
            bg_image.putalpha(alpha)
        else:
            bg_image = self.original_image

        scaled_width = int(bg_image.width * self.scale)
        scaled_height = int(bg_image.height * self.scale)
        scaled_image = bg_image.resize((scaled_width, scaled_height),
                                       self.resample_method)
        self.background_photo = ImageTk.PhotoImage(scaled_image)
        self.canvas.create_image(0,
                                 0,
                                 image=self.background_photo,
                                 anchor='nw')

    def _draw_dots_and_labels(self):
        """
        Draws all the dots and labels on the canvas.
        """
        self.dot_items = []
        self.label_items = []

        for dot in self.dots:
            self._draw_dot(dot)
            if dot.label and self.show_labels_var.get():
                self._draw_label(dot.label, str(dot.dot_id))

    def _draw_dot(self, dot: Dot):
        x, y = dot.position
        scaled_x, scaled_y = x * self.scale, y * self.scale
        scaled_radius = dot.radius * self.scale
        fill_color = rgba_to_hex(dot.color)
        item_id = self.canvas.create_oval(scaled_x - scaled_radius,
                                          scaled_y - scaled_radius,
                                          scaled_x + scaled_radius,
                                          scaled_y + scaled_radius,
                                          fill=fill_color,
                                          outline='')
        self.dot_items.append(item_id)

    def _draw_label(self, label: DotLabel, id_str: str):
        x_label, y_label = label.position
        y_label += self.add_hoc_offset_y_label
        add_hoc_label_scale_factor = 0.75
        scaled_x_label, scaled_y_label = x_label * self.scale, y_label * self.scale
        scaled_font_size = max(
            int(label.font_size * self.scale * add_hoc_label_scale_factor), 1)
        item_id = self.canvas.create_text(scaled_x_label,
                                          scaled_y_label,
                                          text=id_str,
                                          fill=rgba_to_hex(label.color),
                                          font=(label.font, scaled_font_size),
                                          anchor=self.anchor_mapping.get(
                                              label.anchor, 'center'))
        self.label_items.append(item_id)

    def on_left_button_press(self, event):
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)

        # Check if clicking on a dot
        for dot in self.dots:
            dot_x, dot_y = dot.position
            dot_x_scaled = dot_x * self.scale
            dot_y_scaled = dot_y * self.scale
            scaled_radius = dot.radius * self.scale
            distance = ((x - dot_x_scaled)**2 + (y - dot_y_scaled)**2)**0.5

            if distance <= 2 * scaled_radius:
                self.selected_dot_index = dot.dot_id - 1
                self.last_selected_dot_index = dot.dot_id - 1
                self.offset_x = dot_x_scaled - x
                self.offset_y = dot_y_scaled - y
                return

        # Check if clicking on a label
        for idx, label_item_id in enumerate(self.label_items):
            if label_item_id:
                bbox = self.canvas.bbox(label_item_id)
                if bbox:
                    x1, y1, x2, y2 = bbox
                    if x1 <= x <= x2 and y1 <= y <= y2:
                        self.selected_label_index = idx
                        label_x, label_y = self.canvas.coords(label_item_id)
                        self.selected_label_offset_x = label_x - x
                        self.selected_label_offset_y = label_y - y
                        return

        self.selected_dot_index = None
        self.selected_label_index = None

    def on_mouse_move(self, event):
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)

        if self.selected_label_index is not None and self.show_labels_var.get(
        ):
            self._move_label(x, y)
            return

        if self.selected_dot_index is not None:
            self._move_dot(x, y)

    def on_left_button_release(self, _):
        self.selected_dot_index = None
        self.selected_label_index = None

    def on_delete_key_press(self, _):
        if self.selected_dot_index is not None:
            index_to_remove = self.selected_dot_index
        elif self.last_selected_dot_index is not None:
            index_to_remove = self.last_selected_dot_index
        else:
            return

        del self.dots[index_to_remove]
        for idx in range(index_to_remove, len(self.dots)):
            self.dots[idx].dot_id = idx + 1

        self.redraw_canvas()
        self.selected_dot_index = None
        self.selected_label_index = None
        self.last_selected_dot_index = None

    def on_double_click(self, event):
        click_x_canvas = self.canvas.canvasx(event.x)
        click_y_canvas = self.canvas.canvasy(event.y)
        click_x = click_x_canvas / self.scale
        click_y = click_y_canvas / self.scale

        oval_radius = 5
        oval = self.canvas.create_oval(click_x_canvas - oval_radius,
                                       click_y_canvas - oval_radius,
                                       click_x_canvas + oval_radius,
                                       click_y_canvas + oval_radius,
                                       outline="red",
                                       width=2)
        self.canvas.after(300, lambda: self.canvas.delete(oval))

        for i in range(len(self.dots) - 1):
            dot1 = self.dots[i]
            dot2 = self.dots[i + 1]
            x1, y1 = dot1.position
            x2, y2 = dot2.position
            distance = distance_to_segment(click_x, click_y, x1, y1, x2, y2)
            if distance <= self.nu:
                self.add_dot_at_position(click_x, click_y, i + 1)
                return

    def add_dot_at_position(self, x, y, insert_after_index):
        new_dot_id = insert_after_index + 1
        new_dot = Dot(position=(int(x), int(y)), dot_id=new_dot_id)
        new_dot.radius = self.dot_control.radius
        new_dot.color = self.dot_control.color
        new_dot.set_label(tuple(self.dot_control.label.color),
                          self.dot_control.label.font_path,
                          self.dot_control.label.font_size)
        new_dot.label.position = (int(x),
                                  int(y) - int(self.add_hoc_offset_y_label))
        new_dot.label.anchor = self.dot_control.label.anchor
        self.dots.insert(insert_after_index, new_dot)

        for idx in range(insert_after_index + 1, len(self.dots)):
            self.dots[idx].dot_id = idx + 1

        self.redraw_canvas()

    def draw_link_lines(self):
        line_color = "red"
        for i in range(len(self.dots) - 1):
            x1, y1 = self.dots[i].position
            x2, y2 = self.dots[i + 1].position
            x1, y1 = x1 * self.scale, y1 * self.scale
            x2, y2 = x2 * self.scale, y2 * self.scale
            self.canvas.create_line(x1, y1, x2, y2, fill=line_color, width=2)

    def on_apply(self):
        canvas_image = self.generate_image()
        if canvas_image is not None and self.apply_callback:
            self.apply_callback(canvas_image, self.dots)
        self.window.destroy()

    def generate_image(self):
        image = Image.new("RGBA",
                          (int(self.canvas_width), int(self.canvas_height)),
                          (255, 255, 255, 0))
        draw = ImageDraw.Draw(image)
        for dot in self.dots:
            x_dot, y_dot = dot.position
            radius = dot.radius
            fill_color = dot.color
            upper_left = (x_dot - radius, y_dot - radius)
            bottom_right = (x_dot + radius, y_dot + radius)
            draw.ellipse([upper_left, bottom_right], fill=fill_color)
            if dot.label:
                x_label, y_label = dot.label.position
                anchor_map = dot.label.anchor
                draw.text((x_label, y_label),
                          str(dot.dot_id),
                          font=dot.label.font,
                          fill=dot.label.color,
                          anchor=anchor_map)
        return image

    def on_cancel_main_button(self):
        popup = tk.Toplevel(self.window)
        popup.title("Confirm Cancel")
        popup.transient(self.window)
        popup.grab_set()
        message_label = tk.Label(
            popup,
            text=
            "Are you sure you want to cancel? All unsaved changes will be lost."
        )
        message_label.pack(padx=20, pady=20)
        button_frame = tk.Frame(popup)
        button_frame.pack(padx=20, pady=10)
        yes_button = tk.Button(
            button_frame,
            text="Yes",
            width=10,
            command=lambda: [popup.destroy(),
                             self.window.destroy()])
        yes_button.pack(side=tk.LEFT, padx=5)
        no_button = tk.Button(button_frame,
                              text="No",
                              width=10,
                              command=popup.destroy)
        no_button.pack(side=tk.LEFT, padx=5)
        self.window.wait_window(popup)

    def add_overlay_buttons(self):
        width_control_button = 20
        dots_frame = Frame(self.canvas_frame,
                           bg='#b5cccc',
                           bd=2,
                           relief='groove',
                           padx=10,
                           pady=10)
        dots_frame.place(relx=1.0, rely=0.0, anchor='ne', x=-25, y=10)

        dots_label = tk.Label(dots_frame,
                              text="Dots Controls:",
                              bg='#b5cccc',
                              font=("Helvetica", 12, "bold"))
        dots_label.pack(side=tk.TOP, pady=(5, 10), anchor='nw')

        add_button = Button(dots_frame,
                            text="Add",
                            width=width_control_button,
                            command=self.open_add_dot_popup)
        add_button.pack(side=tk.TOP, padx=5, pady=5, anchor='nw')
        Tooltip(add_button, "Add a New Dot")

        remove_button = Button(dots_frame,
                               text="Remove",
                               width=width_control_button,
                               command=self.open_remove_dot_popup)
        remove_button.pack(side=tk.TOP, padx=5, pady=5, anchor='nw')
        Tooltip(remove_button, "Remove a Dot")

        radius_button = Button(dots_frame,
                               text="Radius for One Dot",
                               width=width_control_button,
                               command=self.open_set_radius_popup)
        radius_button.pack(side=tk.TOP, padx=5, pady=5, anchor='nw')
        Tooltip(radius_button, "Set Radius of a Dot")

        order_button = Button(dots_frame,
                              text="Order",
                              width=width_control_button,
                              command=self.open_order_popup)
        order_button.pack(side=tk.TOP, padx=5, pady=5, anchor='nw')
        Tooltip(order_button,
                "Reorder the Dots Starting from the Selected Dot")

        direction_button = Button(dots_frame,
                                  text="Direction",
                                  width=width_control_button,
                                  command=self.reverse_dots_order)
        direction_button.pack(side=tk.TOP, padx=5, pady=5, anchor='nw')
        Tooltip(direction_button, "Reverse the Current Order of Dots")

        link_dots_checkbutton = tk.Checkbutton(dots_frame,
                                               text="Link Dots",
                                               variable=self.link_dots_var,
                                               command=self.redraw_canvas)
        link_dots_checkbutton.pack(side=tk.TOP, padx=5, pady=5, anchor='nw')
        Tooltip(link_dots_checkbutton, "Toggle to link dots with red lines")

        radius_frame = Frame(dots_frame, bg='#b5cccc')
        radius_frame.pack(side=tk.TOP, pady=5, fill='x')
        radius_label = tk.Label(radius_frame, text="Dot Radius:", bg='#b5cccc')
        radius_label.pack(side=tk.LEFT)
        self.radius_var = tk.DoubleVar(value=self.dot_control.radius)
        radius_entry = tk.Entry(radius_frame,
                                textvariable=self.radius_var,
                                width=10)
        radius_entry.pack(side=tk.LEFT, padx=5)
        apply_radius_button = Button(radius_frame,
                                     text="Set",
                                     command=self.set_global_dot_radius)
        apply_radius_button.pack(side=tk.LEFT, padx=5)
        Tooltip(apply_radius_button, "Set global dot radius")

        font_size_frame = Frame(dots_frame, bg='#b5cccc')
        font_size_frame.pack(side=tk.TOP, pady=5, fill='x')
        font_size_label = tk.Label(font_size_frame,
                                   text="Font Size:",
                                   bg='#b5cccc')
        font_size_label.pack(side=tk.LEFT)
        self.font_size_var = tk.IntVar(value=self.dot_control.label.font_size)
        font_size_entry = tk.Entry(font_size_frame,
                                   textvariable=self.font_size_var,
                                   width=10)
        font_size_entry.pack(side=tk.LEFT, padx=5)
        apply_font_size_button = Button(font_size_frame,
                                        text="Set",
                                        command=self.set_global_font_size)
        apply_font_size_button.pack(side=tk.LEFT, padx=5)
        Tooltip(apply_font_size_button, "Set global label font size")

        show_labels_checkbutton = tk.Checkbutton(dots_frame,
                                                 text="Show Labels",
                                                 variable=self.show_labels_var,
                                                 command=self.redraw_canvas)
        show_labels_checkbutton.pack(side=tk.TOP, padx=5, pady=5, anchor="nw")
        Tooltip(show_labels_checkbutton, "Toggle to show or hide labels")

        background_label = tk.Label(dots_frame,
                                    text="Background Settings:",
                                    bg='#b5cccc',
                                    font=("Helvetica", 12, "bold"))
        background_label.pack(side=tk.TOP, padx=5, pady=(20, 5), anchor='nw')

        opacity_frame = Frame(dots_frame, bg='#b5cccc', pady=10)
        opacity_frame.pack(side=tk.TOP, fill='x', padx=5)
        opacity_text_label = tk.Label(opacity_frame,
                                      text="Opacity:",
                                      bg='#b5cccc',
                                      font=("Helvetica", 10, "bold"))
        opacity_text_label.pack(side=tk.LEFT)
        self.opacity_var = tk.DoubleVar()
        self.opacity_var.set(self.bg_opacity)
        opacity_slider = ttk.Scale(opacity_frame,
                                   from_=0.0,
                                   to=1.0,
                                   orient=tk.HORIZONTAL,
                                   variable=self.opacity_var,
                                   command=self.on_opacity_change)
        opacity_slider.pack(side=tk.LEFT, padx=5, fill='x', expand=True)
        self.opacity_display = tk.Label(opacity_frame,
                                        text=f"{self.bg_opacity:.2f}",
                                        bg='#b5cccc',
                                        font=("Helvetica", 10))
        self.opacity_display.pack(side=tk.LEFT)

        browse_button = Button(dots_frame,
                               text="Browse background...",
                               width=20,
                               command=self.browse_background)
        browse_button.pack(side=tk.TOP, padx=5, pady=10, anchor='nw')
        Tooltip(browse_button, "Browse for Background Image")

        actions_frame = Frame(self.canvas_frame,
                              bg='#b5cccc',
                              bd=2,
                              relief='groove',
                              padx=10,
                              pady=10)
        actions_frame.place(relx=0.5, rely=1.0, anchor='s', y=-25)
        apply_button = Button(actions_frame,
                              text="Apply",
                              width=15,
                              command=self.on_apply)
        apply_button.pack(side=tk.LEFT, padx=10, pady=5)
        Tooltip(apply_button, "Apply Changes")
        cancel_button = Button(actions_frame,
                               text="Cancel",
                               width=15,
                               command=self.on_cancel_main_button)
        cancel_button.pack(side=tk.LEFT, padx=10, pady=5)
        Tooltip(cancel_button, "Cancel Changes")

    def _move_label(self, x, y):
        new_x = x + self.selected_label_offset_x
        new_y = y + self.selected_label_offset_y
        label_x = new_x / self.scale
        label_y = new_y / self.scale
        associated_dot = self.dots[self.selected_label_index]
        label = associated_dot.label
        label.position = (label_x, label_y)
        label_item_id = self.label_items[self.selected_label_index]
        self.canvas.coords(label_item_id, new_x, new_y)
        self.grid.move_label(label)
        self._update_color_label(label, label_item_id)

    def _update_color_label(self, label, label_item_id):
        overlap_found, overlapping_dots, overlapping_labels = self.grid.do_overlap(
            label)
        self._reset_non_overlapping(label.overlap_dot_list, overlapping_dots,
                                    self.dot_control.color, "dot")
        self._reset_non_overlapping(label.overlap_label_list,
                                    overlapping_labels,
                                    self.dot_control.label.color, "label")
        label.overlap_dot_list = overlapping_dots
        label.overlap_label_list = overlapping_labels
        label.color = self.overlap_color if overlap_found else self.dot_control.label.color
        self.canvas.itemconfig(label_item_id, fill=rgba_to_hex(label.color))
        self._update_overlap_color(overlapping_dots, self.overlap_color, "dot")
        self._update_overlap_color(overlapping_labels, self.overlap_color,
                                   "label")
        label.overlap_other_dots = overlap_found

    def _update_color_dot(self, dot, dot_item_id, label, label_item_id):
        overlap_found, overlapping_dots, overlapping_labels = self.grid.do_overlap(
            dot)
        self._reset_non_overlapping(dot.overlap_dot_list, overlapping_dots,
                                    self.dot_control.color, "dot")
        self._reset_non_overlapping(dot.overlap_label_list, overlapping_labels,
                                    self.dot_control.label.color, "label")
        dot.overlap_dot_list = overlapping_dots
        dot.overlapping_labels = overlapping_labels
        dot.color = self.overlap_color if overlap_found else self.dot_control.color
        self.canvas.itemconfig(dot_item_id, fill=rgba_to_hex(dot.color))
        self._update_overlap_color(overlapping_dots, self.overlap_color, "dot")
        self._update_overlap_color(overlapping_labels, self.overlap_color,
                                   "label")
        dot.overlap_other_dots = overlap_found
        self._update_color_label(label, label_item_id)

    def _move_dot(self, x, y):
        new_x = (x + self.offset_x) / self.scale
        new_y = (y + self.offset_y) / self.scale
        self.dots[self.selected_dot_index].position = (new_x, new_y)
        scaled_radius = self.dots[self.selected_dot_index].radius * self.scale
        item_id = self.dot_items[self.selected_dot_index]
        self.canvas.coords(item_id, x - scaled_radius, y - scaled_radius,
                           x + scaled_radius, y + scaled_radius)
        label = self.dots[self.selected_dot_index].label
        if label:
            label.position = (new_x, new_y - self.add_hoc_offset_y_label)
            if self.show_labels_var.get():
                label_item_id = self.label_items[self.selected_dot_index]
                self.canvas.coords(label_item_id, x, y)
        dot = self.dots[self.selected_dot_index]
        self.grid.move_dot_and_label(dot)
        self._update_color_dot(
            dot, self.dot_items[self.selected_dot_index], label,
            self.label_items[self.selected_dot_index] if label else None)

    def _reset_non_overlapping(self, previous_items, current_items,
                               default_color, item_type):
        for item in previous_items:
            if item not in current_items:
                item.color = default_color
                if item_type == "dot":
                    item_id = self.dot_items[item.dot_id - 1]
                else:
                    item_id = self.label_items[item.label_id - 1]
                self.canvas.itemconfig(item_id,
                                       fill=rgba_to_hex(default_color))
                item.overlap_other_dots = False

    def _update_overlap_color(self, items, overlap_color, item_type):
        for item in items:
            item.color = overlap_color
            if item_type == "dot":
                item_id = self.dot_items[item.dot_id - 1]
            else:
                item_id = self.label_items[item.label_id - 1]
            self.canvas.itemconfig(item_id, fill=rgba_to_hex(overlap_color))
            item.overlap_other_dots = True

    def browse_background(self):
        file_path = fd.askopenfilename(title="Select Background Image",
                                       filetypes=[("Image Files",
                                                   "*.png;*.jpg;*.jpeg;*.bmp")
                                                  ])
        self.window.lift()
        self.window.focus_set()
        if file_path:
            try:
                self.original_image = Image.open(file_path).convert("RGBA")
                if self.original_image.size != (self.canvas_width,
                                                self.canvas_height):
                    self.original_image = self.original_image.resize(
                        (self.canvas_width, self.canvas_height),
                        self.resample_method)
                self.redraw_canvas()
            except IOError:
                messagebox.showerror("Error",
                                     f"Cannot open image: {file_path}")

    def set_global_dot_radius(self):
        try:
            new_radius = self.radius_var.get()
            if new_radius <= 0:
                raise ValueError("Radius must be positive.")
            self.dot_control.radius = new_radius
            for dot in self.dots:
                dot.radius = new_radius
            self.redraw_canvas()
        except (ValueError, tk.TclError):
            messagebox.showerror(
                "Invalid Input",
                "Please enter a positive number for the radius.")

    def reverse_dots_order(self):
        """
        Reverses the current order of dots and their associated labels.
        """
        if not self.dots:
            messagebox.showerror("Error", "No dots available to reverse.")
            return

        # Reverse the dots and labels
        self.dots.reverse()

        # Update the labels' text to reflect the new order
        for idx in range(len(self.dots)):
            new_idx = idx + 1
            self.dots[idx].dot_id = new_idx

        # Redraw the canvas to reflect the reversed order
        self.redraw_canvas()

    def set_global_font_size(self):
        try:
            new_font_size = self.font_size_var.get()
            if new_font_size <= 0:
                raise ValueError("Font size must be positive.")
            self.dot_control.label.font_size = new_font_size
            self.dot_control.label.font = ImageFont.truetype(
                self.dot_control.label.font_path,
                self.dot_control.label.font_size)
            for dot in self.dots:
                dot.label.font_size = new_font_size
                dot.label.font = self.dot_control.label.font
            self.redraw_canvas()
        except (ValueError, tk.TclError, IOError):
            messagebox.showerror(
                "Invalid Input",
                "Please enter a positive number for the font size.")

    def open_set_radius_popup(self):
        if not self.dots:
            messagebox.showerror("Error", "No dots available to modify.")
            return

        dot_numbers = [f"Dot {i+1}" for i in range(len(self.dots))]

        def on_apply(selected_index, input_value):
            # This callback is called when "Apply" is clicked
            if input_value is None:
                # No input provided
                return

            # Validate input
            try:
                new_radius = float(input_value)
                if new_radius <= 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror(
                    "Invalid Input",
                    "Please enter a positive number for the radius.")
                return

            # Update the radius of the selected dot
            dot = self.dots[selected_index]
            dot.radius = new_radius
            label = dot.label

            # Recalculate label position based on new radius
            distance_from_dots = 1.2 * new_radius
            new_pos_x = dot.position[0] + distance_from_dots
            new_pos_y = dot.position[1] + distance_from_dots
            label.position = (new_pos_x, new_pos_y)

            self.redraw_canvas()

        # Default value for input is the radius of the first dot by default
        default_radius = self.dots[
            0].radius if self.dots else self.dot_control.radius

        DotSelectionPopup(parent=self.window,
                          title="Set Dot Radius",
                          label_text="Radius of dot number:",
                          dot_numbers=dot_numbers,
                          on_apply=on_apply,
                          input_label_text="New Radius:",
                          input_default_value=default_radius)

    def open_order_popup(self):
        if not self.dots:
            messagebox.showerror("Error", "No dots available to reorder.")
            return

        dot_numbers = [f"Dot {i+1}" for i in range(len(self.dots))]

        def on_apply(selected_index, _):
            # Reorders the dots so that the selected dot becomes the first one.
            if selected_index < 0 or selected_index >= len(self.dots):
                messagebox.showerror("Error", "Selected dot does not exist.")
                return

            reordered_dots = self.dots[
                selected_index:] + self.dots[:selected_index]
            self.dots = reordered_dots

            # Update dot_id
            for idx in range(len(self.dots)):
                self.dots[idx].dot_id = idx + 1

            self.redraw_canvas()

        DotSelectionPopup(
            parent=self.window,
            title="Order Dots",
            label_text=
            "Set the starting dots to globally reorder the other one",
            dot_numbers=dot_numbers,
            on_apply=on_apply)

    def open_add_dot_popup(self):
        if not self.dots:
            messagebox.showerror("Error", "No dots available to add after.")
            return

        dot_numbers = [f"Dot {i+1}" for i in range(len(self.dots))]

        def on_apply(selected_index, _):
            # Similar logic as in original add_dot method
            if selected_index + 1 < len(self.dots):
                selected_dot = self.dots[selected_index].position
                next_dot = self.dots[selected_index + 1].position
                new_dot_x = (selected_dot[0] + next_dot[0]) / 2
                new_dot_y = (selected_dot[1] + next_dot[1]) / 2
            else:
                selected_dot = self.dots[selected_index].position
                offset = 20
                new_dot_x = selected_dot[0] + offset
                new_dot_y = selected_dot[1] + offset

            new_pos = (int(new_dot_x), int(new_dot_y))
            new_idx = selected_index + 2
            new_dot = Dot(position=new_pos, dot_id=new_idx)
            new_dot.radius = self.dot_control.radius
            new_dot.color = self.dot_control.color
            new_dot.set_label(self.dot_control.label.color,
                              self.dot_control.label.font_path,
                              self.dot_control.label.font_size)

            self.dots.insert(selected_index + 1, new_dot)

            # Update IDs
            for idx in range(selected_index + 2, len(self.dots)):
                self.dots[idx].dot_id += 1

            self.redraw_canvas()

        DotSelectionPopup(parent=self.window,
                          title="Add a New Dot",
                          label_text="Add a dot after dot number:",
                          dot_numbers=dot_numbers,
                          on_apply=on_apply)

    def open_remove_dot_popup(self):
        if not self.dots:
            messagebox.showerror("Error", "No dots available to remove.")
            return

        dot_numbers = [f"Dot {i+1}" for i in range(len(self.dots))]

        def on_apply(selected_index, _):
            try:
                del self.dots[selected_index]
            except IndexError:
                messagebox.showerror("Error", "Selected dot does not exist.")
                return

            # Update IDs
            for idx in range(selected_index, len(self.dots)):
                self.dots[idx].dot_id = idx + 1

            self.redraw_canvas()

        DotSelectionPopup(parent=self.window,
                          title="Remove a Dot",
                          label_text="Remove the dot number:",
                          dot_numbers=dot_numbers,
                          on_apply=on_apply)
