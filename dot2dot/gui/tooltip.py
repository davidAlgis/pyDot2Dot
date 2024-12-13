import tkinter as tk


class Tooltip:
    """
    It creates a tooltip for a given widget as the mouse goes on it after a small delay.
    """

    def __init__(self, widget, text='widget info', delay=250):
        self.widget = widget
        self.text = text
        self.delay = delay  # Delay in milliseconds before showing the tooltip
        self.tooltip_window = None
        self._after_id = None  # Store the ID of the scheduled event
        self.widget.bind("<Enter>", self.schedule_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)
        self.widget.bind("<Motion>", self.track_motion)
        self.widget.bind("<ButtonPress>", self.hide_tooltip)
        self.mouse_still = False  # Track if the mouse is still

    def schedule_tooltip(self, event=None):
        """Schedule the tooltip to be shown after a delay."""
        self.mouse_still = True
        self._after_id = self.widget.after(self.delay, self.show_tooltip)

    def track_motion(self, event=None):
        """Check if the mouse is moving and reset the tooltip scheduling."""
        if self.mouse_still:
            # Cancel any scheduled tooltip since the mouse moved
            self.cancel_scheduled_tooltip()
            # Re-schedule the tooltip display as the mouse is moving within the widget
            self.schedule_tooltip()

    def cancel_scheduled_tooltip(self, event=None):
        """Cancel any scheduled tooltip if the mouse moves."""
        if self._after_id is not None:
            self.widget.after_cancel(self._after_id)
            self._after_id = None

    def show_tooltip(self, event=None):
        """Display the tooltip window."""
        if self.tooltip_window or not self.text:
            return
        x, y, cx, cy = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 20
        self.tooltip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(tw,
                         text=self.text,
                         justify='left',
                         background="#ffffe0",
                         relief='solid',
                         borderwidth=1,
                         font=("tahoma", "8", "normal"))
        label.pack(ipadx=1)
        self._after_id = None  # Reset the scheduled event ID
        self.mouse_still = False  # Tooltip is shown, reset mouse still state

    def hide_tooltip(self, event=None):
        """Hide the tooltip window and cancel any scheduled display."""
        self.cancel_scheduled_tooltip()
        tw = self.tooltip_window
        self.tooltip_window = None
        if tw:
            tw.destroy()
