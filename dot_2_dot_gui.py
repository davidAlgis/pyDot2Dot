import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
import sys
import threading
from main import process_single_image, utils
import cv2
import matplotlib.pyplot as plt


class DotToDotGUI:

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Dot to Dot Processor")
        self.create_widgets()

    def create_widgets(self):
        # Input Selection
        input_frame = ttk.LabelFrame(self.root, text="Input")
        input_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        self.input_path = tk.StringVar()
        ttk.Entry(input_frame, textvariable=self.input_path,
                  width=50).grid(row=0, column=0, padx=5, pady=5)
        ttk.Button(input_frame, text="Browse",
                   command=self.browse_input).grid(row=0,
                                                   column=1,
                                                   padx=5,
                                                   pady=5)

        # Output Selection
        output_frame = ttk.LabelFrame(self.root, text="Output")
        output_frame.grid(row=1, column=0, padx=10, pady=10, sticky="ew")

        self.output_path = tk.StringVar()
        ttk.Entry(output_frame, textvariable=self.output_path,
                  width=50).grid(row=0, column=0, padx=5, pady=5)
        ttk.Button(output_frame, text="Browse",
                   command=self.browse_output).grid(row=0,
                                                    column=1,
                                                    padx=5,
                                                    pady=5)

        # Parameters Frame
        params_frame = ttk.LabelFrame(self.root, text="Parameters")
        params_frame.grid(row=2, column=0, padx=10, pady=10, sticky="ew")

        # Shape Detection
        ttk.Label(params_frame, text="Shape Detection:").grid(row=0,
                                                              column=0,
                                                              padx=5,
                                                              pady=5,
                                                              sticky="e")
        self.shape_detection = tk.StringVar(value="Contour")
        ttk.Combobox(params_frame,
                     textvariable=self.shape_detection,
                     values=["Contour", "Path"],
                     state="readonly").grid(row=0,
                                            column=1,
                                            padx=5,
                                            pady=5,
                                            sticky="w")

        # Number of Points
        ttk.Label(params_frame, text="Number of Points:").grid(row=1,
                                                               column=0,
                                                               padx=5,
                                                               pady=5,
                                                               sticky="e")
        self.num_points = tk.IntVar(value=200)
        ttk.Entry(params_frame, textvariable=self.num_points).grid(row=1,
                                                                   column=1,
                                                                   padx=5,
                                                                   pady=5,
                                                                   sticky="w")

        # Epsilon
        ttk.Label(params_frame, text="Epsilon:").grid(row=2,
                                                      column=0,
                                                      padx=5,
                                                      pady=5,
                                                      sticky="e")
        self.epsilon = tk.DoubleVar(value=0.001)
        ttk.Entry(params_frame, textvariable=self.epsilon).grid(row=2,
                                                                column=1,
                                                                padx=5,
                                                                pady=5,
                                                                sticky="w")

        # Distance
        ttk.Label(params_frame, text="Distance Min:").grid(row=3,
                                                           column=0,
                                                           padx=5,
                                                           pady=5,
                                                           sticky="e")
        self.distance_min = tk.StringVar(value="")
        ttk.Entry(params_frame,
                  textvariable=self.distance_min).grid(row=3,
                                                       column=1,
                                                       padx=5,
                                                       pady=5,
                                                       sticky="w")

        ttk.Label(params_frame, text="Distance Max:").grid(row=4,
                                                           column=0,
                                                           padx=5,
                                                           pady=5,
                                                           sticky="e")
        self.distance_max = tk.StringVar(value="")
        ttk.Entry(params_frame,
                  textvariable=self.distance_max).grid(row=4,
                                                       column=1,
                                                       padx=5,
                                                       pady=5,
                                                       sticky="w")

        # Font
        ttk.Label(params_frame, text="Font:").grid(row=5,
                                                   column=0,
                                                   padx=5,
                                                   pady=5,
                                                   sticky="e")
        self.font = tk.StringVar(value="Arial.ttf")
        ttk.Entry(params_frame, textvariable=self.font).grid(row=5,
                                                             column=1,
                                                             padx=5,
                                                             pady=5,
                                                             sticky="w")

        # Font Size
        ttk.Label(params_frame, text="Font Size:").grid(row=6,
                                                        column=0,
                                                        padx=5,
                                                        pady=5,
                                                        sticky="e")
        self.font_size = tk.StringVar(value="1%")
        ttk.Entry(params_frame, textvariable=self.font_size).grid(row=6,
                                                                  column=1,
                                                                  padx=5,
                                                                  pady=5,
                                                                  sticky="w")

        # Font Color
        ttk.Label(params_frame, text="Font Color (RGBA):").grid(row=7,
                                                                column=0,
                                                                padx=5,
                                                                pady=5,
                                                                sticky="e")
        self.font_color = tk.StringVar(value="0,0,0,255")
        ttk.Entry(params_frame, textvariable=self.font_color).grid(row=7,
                                                                   column=1,
                                                                   padx=5,
                                                                   pady=5,
                                                                   sticky="w")

        # Dot Color
        ttk.Label(params_frame, text="Dot Color (RGBA):").grid(row=8,
                                                               column=0,
                                                               padx=5,
                                                               pady=5,
                                                               sticky="e")
        self.dot_color = tk.StringVar(value="0,0,0,255")
        ttk.Entry(params_frame, textvariable=self.dot_color).grid(row=8,
                                                                  column=1,
                                                                  padx=5,
                                                                  pady=5,
                                                                  sticky="w")

        # Radius
        ttk.Label(params_frame, text="Radius:").grid(row=9,
                                                     column=0,
                                                     padx=5,
                                                     pady=5,
                                                     sticky="e")
        self.radius = tk.StringVar(value="0.5%")
        ttk.Entry(params_frame, textvariable=self.radius).grid(row=9,
                                                               column=1,
                                                               padx=5,
                                                               pady=5,
                                                               sticky="w")

        # DPI
        ttk.Label(params_frame, text="DPI:").grid(row=10,
                                                  column=0,
                                                  padx=5,
                                                  pady=5,
                                                  sticky="e")
        self.dpi = tk.IntVar(value=400)
        ttk.Entry(params_frame, textvariable=self.dpi).grid(row=10,
                                                            column=1,
                                                            padx=5,
                                                            pady=5,
                                                            sticky="w")

        # Threshold Binary
        ttk.Label(params_frame,
                  text="Threshold Binary (min max):").grid(row=11,
                                                           column=0,
                                                           padx=5,
                                                           pady=5,
                                                           sticky="e")
        self.threshold_min = tk.IntVar(value=100)
        self.threshold_max = tk.IntVar(value=255)
        ttk.Entry(params_frame, textvariable=self.threshold_min,
                  width=5).grid(row=11,
                                column=1,
                                padx=(5, 0),
                                pady=5,
                                sticky="w")
        ttk.Entry(params_frame, textvariable=self.threshold_max,
                  width=5).grid(row=11,
                                column=1,
                                padx=(60, 5),
                                pady=5,
                                sticky="w")

        # Checkboxes
        self.debug = tk.BooleanVar(value=False)
        ttk.Checkbutton(params_frame, text="Debug Mode",
                        variable=self.debug).grid(row=12,
                                                  column=0,
                                                  padx=5,
                                                  pady=5,
                                                  sticky="w")

        self.display_output = tk.BooleanVar(value=True)
        ttk.Checkbutton(params_frame,
                        text="Display Output",
                        variable=self.display_output).grid(row=12,
                                                           column=1,
                                                           padx=5,
                                                           pady=5,
                                                           sticky="w")

        self.verbose = tk.BooleanVar(value=True)
        ttk.Checkbutton(params_frame, text="Verbose",
                        variable=self.verbose).grid(row=13,
                                                    column=0,
                                                    padx=5,
                                                    pady=5,
                                                    sticky="w")

        # Process Button
        process_button = ttk.Button(self.root,
                                    text="Process",
                                    command=self.process_threaded)
        process_button.grid(row=3, column=0, padx=10, pady=10)

        # Progress Bar
        self.progress = ttk.Progressbar(self.root, mode='indeterminate')
        self.progress.grid(row=4, column=0, padx=10, pady=(0, 10), sticky="ew")

    def browse_input(self):
        # Allow selecting a file or directory
        path = filedialog.askopenfilename(title="Select Input Image",
                                          filetypes=[("Image Files",
                                                      "*.png;*.jpg;*.jpeg")])
        if not path:
            path = filedialog.askdirectory(title="Select Input Folder")
        if path:
            self.input_path.set(path)

    def browse_output(self):
        path = filedialog.askdirectory(title="Select Output Folder")
        if path:
            self.output_path.set(path)

    def process_threaded(self):
        # Run the processing in a separate thread to keep the GUI responsive
        threading.Thread(target=self.process).start()

    def process(self):
        input_path = self.input_path.get()
        output_path = self.output_path.get()

        if not input_path:
            messagebox.showerror("Error",
                                 "Please select an input file or folder.")
            return

        # Disable the process button and start the progress bar
        self.set_processing_state(True)

        try:
            # Create a mock argparse.Namespace object
            class Args:
                pass

            args = Args()
            args.input = input_path
            args.output = output_path
            args.shapeDetection = self.shape_detection.get()
            args.numPoints = self.num_points.get()
            args.epsilon = self.epsilon.get()
            args.distance = [
                self.distance_min.get(),
                self.distance_max.get()
            ] if self.distance_min.get() and self.distance_max.get() else None
            args.font = self.font.get()
            args.fontSize = self.font_size.get()
            args.fontColor = [
                int(c) for c in self.font_color.get().split(',')
            ] if self.font_color.get() else [0, 0, 0, 255]
            args.dotColor = [int(c) for c in self.dot_color.get().split(',')
                             ] if self.dot_color.get() else [0, 0, 0, 255]
            args.radius = self.radius.get()
            args.dpi = self.dpi.get()
            args.debug = self.debug.get()
            args.displayOutput = self.display_output.get()
            args.verbose = self.verbose.get()
            args.thresholdBinary = [
                self.threshold_min.get(),
                self.threshold_max.get()
            ]

            # Validate distance inputs
            if args.distance:
                if not self.validate_distance(args.distance):
                    messagebox.showerror(
                        "Error",
                        "Invalid distance values. Please enter valid numbers or percentages (e.g., 10% or 0.05)."
                    )
                    self.set_processing_state(False)
                    return

            # Validate font color and dot color
            if len(args.fontColor) != 4 or len(args.dotColor) != 4:
                messagebox.showerror(
                    "Error",
                    "Font color and Dot color must have exactly 4 integer values (RGBA)."
                )
                self.set_processing_state(False)
                return

            # Process images
            if os.path.isdir(input_path):
                # Processing multiple images
                output_dir = output_path if output_path else input_path
                image_files = [
                    f for f in os.listdir(input_path)
                    if f.lower().endswith(('.png', '.jpg', '.jpeg'))
                ]
                if self.verbose.get():
                    print(
                        f"Processing {len(image_files)} images in the folder {input_path}..."
                    )

                for image_file in image_files:
                    img_input_path = os.path.join(input_path, image_file)
                    img_output_path = utils.generate_output_path(
                        img_input_path,
                        os.path.join(output_dir, image_file)
                        if output_path else None)
                    process_single_image(img_input_path, img_output_path, args)

            elif os.path.isfile(input_path):
                # Processing a single image
                img_output_path = utils.generate_output_path(
                    input_path, output_path)
                process_single_image(input_path, img_output_path, args)
            else:
                messagebox.showerror("Error",
                                     f"Input path '{input_path}' is invalid.")
                self.set_processing_state(False)
                return

            # Display output if needed
            if args.debug or args.displayOutput:
                if os.path.isfile(img_output_path):
                    debug_image = utils.resize_for_debug(
                        cv2.imread(img_output_path))
                    utils.display_with_matplotlib(debug_image, 'Output')
                    plt.show()

            messagebox.showinfo("Success", "Processing complete.")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred:\n{e}")
        finally:
            # Re-enable the process button and stop the progress bar
            self.set_processing_state(False)

    def validate_distance(self, distance):
        # Validate that distance_min and distance_max are either numbers or percentages
        for d in distance:
            if d.endswith('%'):
                try:
                    float(d.strip('%'))
                except ValueError:
                    return False
            else:
                try:
                    float(d)
                except ValueError:
                    return False
        return True

    def set_processing_state(self, is_processing):
        if is_processing:
            self.root.config(cursor="wait")
            self.progress.start()
        else:
            self.root.config(cursor="")
            self.progress.stop()

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    gui = DotToDotGUI()
    gui.run()
