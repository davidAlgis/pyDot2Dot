"""
dots_exporter.py
Export utilities for Dot2Dot:
- Save rendered image (PNG/JPEG)
- Save polygon as GeoJSON/JSON (optionally normalized to [0,1] using max(width, height))
"""

import json
import tkinter as tk
import traceback
from tkinter import filedialog, messagebox
from typing import List, Tuple

import numpy as np

from dot2dot.gui.error_window import ErrorWindow
from dot2dot.gui.popup_2_buttons import Popup2Buttons


class DotsExporter:
    """
    Handle exporting either an image or a GeoJSON polygon.
    """

    def __init__(self, root: tk.Tk, main_gui) -> None:
        """
        Initialize the exporter.

        Args:
            root: Tk root window.
            main_gui: Main GUI object that provides processed_dots and images.
        """
        self.root = root
        self.main_gui = main_gui
        self.save_path: str = ""

    def export(self) -> None:
        """
        Save either an image (PNG/JPEG) or a GeoJSON/JSON polygon, not both.

        - If the chosen path ends with .png/.jpg/.jpeg: save the rendered image.
        - If the chosen path ends with .json/.geojson: save a GeoJSON Polygon
          built from processed dots (pixel coordinates).
        """
        has_image = (
            getattr(self.main_gui, "processed_image", None) is not None
            or getattr(self.main_gui, "original_output_image", None)
            is not None
        )
        has_dots = bool(getattr(self.main_gui, "processed_dots", None))
        if not has_image and not has_dots:
            messagebox.showerror("Error", "Nothing to save yet.")
            return

        self.save_path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[
                ("GeoJSON/JSON files", "*.json;*.geojson"),
                ("PNG files", "*.png"),
                ("JPEG files", "*.jpg;*.jpeg"),
            ],
            title="Save Image or Polygon (GeoJSON)",
        )
        if not self.save_path:
            return

        try:
            lower = self.save_path.lower()
            if lower.endswith((".png", ".jpg", ".jpeg")):
                self._export_image(self.save_path)
                return
            if lower.endswith((".json", ".geojson")):
                self._export_polygon_geojson(self.save_path)
                return

            messagebox.showerror("Error", "Unsupported file format.")
        except Exception:
            stack = traceback.format_exc()
            self.root.after(0, lambda: ErrorWindow(self.root, stack))

    def _export_image(self, path: str) -> None:
        """
        Write the rendered image to disk.

        Args:
            path: Destination file path.
        """
        if getattr(self.main_gui, "original_output_image", None) is None:
            messagebox.showerror("Error", "No processed image to save.")
            return

        self.main_gui.original_output_image.save(path)
        messagebox.showinfo("Success", f"Image saved to {path}.")

    def _export_polygon_geojson(self, path: str) -> None:
        """
        Write a GeoJSON Polygon built from processed dots (pixel coordinates).

        If the user chooses normalization, divide x and y by max(width, height)
        so that the largest image dimension maps to 1.0 and the other is scaled
        proportionally. The linear ring is closed.
        """
        dots = getattr(self.main_gui, "processed_dots", None)
        if not dots or len(dots) < 3:
            messagebox.showerror(
                "Error", "Need at least three dots to export a polygon."
            )
            return

        normalize = self._ask_normalize()

        width, height = self._get_image_size()
        ring: List[List[float]] = []

        if normalize:
            if width <= 0 or height <= 0:
                messagebox.showerror(
                    "Error",
                    "Image size unavailable. Cannot normalize coordinates.",
                )
                return
            scale = float(max(width, height))
            for d in dots:
                x, y = d.position
                ring.append([float(x) / scale, float(y) / scale])
        else:
            for d in dots:
                x, y = d.position
                ring.append([int(x), int(y)])

        if ring[0] != ring[-1]:
            ring.append(ring[0])

        geojson = {"type": "Polygon", "coordinates": [ring]}
        serializable = _convert_to_serializable(geojson)

        with open(path, "w", encoding="utf-8") as f:
            json.dump(serializable, f, indent=2)

        messagebox.showinfo("Success", f"Polygon saved to {path}.")

    def _ask_normalize(self) -> bool:
        """
        Ask the user if coordinates should be normalized to [0, 1]
        using max(width, height) as the divisor.

        Returns:
            True if user selects normalization, False otherwise.
        """
        if Popup2Buttons is None:
            # Fallback simple dialog if custom popup is unavailable.
            return messagebox.askyesno(
                "Normalize coordinates?",
                "Normalize coordinates to [0, 1] using the larger of width and height?",
            )

        choice = {"value": False}

        def yes() -> None:
            choice["value"] = True

        Popup2Buttons(
            self.root,
            title="Normalize coordinates?",
            main_text=(
                "Do you want to normalize coordinates to [0, 1] using the larger\n"
                "of the image width and height?"
            ),
            button1_text="Yes",
            button1_action=yes,
            button2_text="No",
            button2_action=lambda: None,
        )
        return bool(choice["value"])

    def _get_image_size(self) -> Tuple[int, int]:
        """
        Determine (width, height) from the available images.

        Returns:
            (width, height) if available; otherwise (0, 0).
        """
        img = getattr(self.main_gui, "original_output_image", None)
        if img is not None:
            try:
                w, h = img.size
                return int(w), int(h)
            except Exception:
                pass

        proc = getattr(self.main_gui, "processed_image", None)
        if (
            proc is not None
            and hasattr(proc, "shape")
            and len(proc.shape) >= 2
        ):
            h, w = proc.shape[0], proc.shape[1]
            return int(w), int(h)

        return 0, 0


def _convert_to_serializable(data):
    """
    Recursively convert NumPy types to native Python types.
    Mirrors DotsSaver.convert_to_serializable without importing it
    to avoid cyclic dependencies.
    """
    if isinstance(data, dict):
        return {k: _convert_to_serializable(v) for k, v in data.items()}
    if isinstance(data, list):
        return [_convert_to_serializable(x) for x in data]
    if isinstance(data, tuple):
        return tuple(_convert_to_serializable(x) for x in data)
    if isinstance(data, np.ndarray):
        return data.tolist()
    if isinstance(data, np.generic):
        return data.item()
    return data
