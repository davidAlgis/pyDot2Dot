import os
from dot2dot.utils import get_base_directory


def set_icon(window):
    base_directory = get_base_directory()
    icon_path = os.path.join(base_directory, "assets", "dot_2_dot.ico")

    if os.path.exists(icon_path):
        # Set the window icon
        window.iconbitmap(icon_path)
    else:
        print(f"Warning: Icon not found at {icon_path}")
