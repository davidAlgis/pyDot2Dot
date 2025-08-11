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
        Write a GeoJSON Polygon built from processed dots.

        Coordinate convention fix:
        - Images have y increasing downward; the SPH/world has y upward.
        - We flip Y so the polygon is not vertically mirrored in your engine.

        Centered scaling path:
          y' = -(y - cy) * S     (flip around centroid; no image size needed)
        Raw pixel path:
          y' = H - 1 - y         (flip using image height)
        """
        dots = getattr(self.main_gui, "processed_dots", None)
        if not dots or len(dots) < 3:
            messagebox.showerror(
                "Error", "Need at least three dots to export a polygon."
            )
            return

        apply_centered_scale = self._ask_normalize()  # repurposed prompt

        ring: List[List[float]] = []
        if apply_centered_scale:
            # 1) center of mass
            sx = 0.0
            sy = 0.0
            for d in dots:
                x, y = d.position
                sx += float(x)
                sy += float(y)
            n = float(len(dots))
            cx = sx / n
            cy = sy / n

            # 2) uniform scale from farthest horizontal/vertical displacement
            max_dx = 0.0
            max_dy = 0.0
            for d in dots:
                x, y = d.position
                dx = abs(float(x) - cx)
                dy = abs(float(y) - cy)
                if dx > max_dx:
                    max_dx = dx
                if dy > max_dy:
                    max_dy = dy
            max_disp = max(max_dx, max_dy)
            if max_disp <= 1e-12:
                messagebox.showerror(
                    "Error",
                    "Cannot scale: all dots collapse at the same position.",
                )
                return
            S = 1.0 / max_disp

            # 3) transform to [-1, 1] with uniform scaling on both axes
            #    FLIP Y: negate the vertical offset so up is positive.
            for d in dots:
                x, y = d.position
                x_t = (float(x) - cx) * S
                y_t = -(float(y) - cy) * S  # <-- flip
                ring.append([x_t, y_t])
        else:
            # raw pixel coordinates
            # map image pixel y (down) to world y (up): y' = H - 1 - y
            _, h = self._get_image_size()
            if h <= 0:
                # if we cannot determine height, warn and fall back (no flip)
                messagebox.showwarning(
                    "Warning",
                    "Image height unavailable; exported polygon may appear vertically flipped.",
                )
                for d in dots:
                    x, y = d.position
                    ring.append([int(x), int(y)])
            else:
                for d in dots:
                    x, y = d.position
                    y_flipped = (h - 1) - int(y)
                    ring.append([int(x), y_flipped])

        # close the ring
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
                "Center and scale to [-1, 1]?",
                "Do you want to center the polygon on its centroid and scale both axes "
                "uniformly so the farthest dot reaches -1 or +1 on its dominant axis?",
            )

        choice = {"value": False}

        def yes() -> None:
            choice["value"] = True

        Popup2Buttons(
            self.root,
            title="Center and scale to [-1, 1]?",
            main_text=(
                "Do you want to center the polygon on its centroid and scale both axes "
                "uniformly so the farthest dot reaches -1 or +1 on its dominant axis?"
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
