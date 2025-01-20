import os
from dot2dot.utils import get_base_directory
from screeninfo import get_monitors


def set_icon(window):
    base_directory = get_base_directory()
    icon_path = os.path.join(base_directory, "assets", "dot_2_dot.ico")

    if os.path.exists(icon_path):
        # Set the window icon
        window.iconbitmap(icon_path)
    else:
        print(f"Warning: Icon not found at {icon_path}")


def set_screen_choice(root, config):
    # Screen choice
    screen_choice = config["screenChoice"]
    if screen_choice is None:
        screen_choice = 0
    monitors = get_monitors()
    if screen_choice < len(monitors):
        selected_monitor = monitors[screen_choice]
        root.geometry(
            f"{selected_monitor.width}x{selected_monitor.height}+{selected_monitor.x}+{selected_monitor.y}"
        )
    else:
        print(
            f"Invalid screen choice: {screen_choice}. Defaulting to main screen."
        )


def get_screen_choice(config):
    screen_choice = config["screenChoice"]
    if screen_choice is None:
        return 0
    monitors = get_monitors()
    if screen_choice < len(monitors):
        return screen_choice
    else:
        0
