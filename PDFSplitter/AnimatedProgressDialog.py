import tkinter as tk
import math

class AnimatedProgressDialog:
    def __init__(self, parent, title="Working...", message="Please wait..."):
        self.parent = parent
        self.title = title
        self.message = message
        self.running = False
        self._after_id = None

        # Spinner setup
        self.spinner_positions = 8
        self.spinner_index = 0
        self.radius = 40  # radius of the circle
        self.dot_radius = 7  # radius of each dot

        self.win = tk.Toplevel(parent)
        self.win.overrideredirect(True)  # Make window borderless

        self.win.lift()  # Bring to front
        self.win.focus_force()  # Focus on this window
        self.win.attributes("-topmost", True)  # Always on top

        win_w, win_h = 400, 240

        self.win.title(self.title)
        
        
        self.win.update_idletasks()
        parent_x = self.parent.winfo_rootx()
        parent_y = self.parent.winfo_rooty()
        parent_w = self.parent.winfo_width()
        parent_h = self.parent.winfo_height()
        x = parent_x + (parent_w - win_w) // 2
        y = parent_y + (parent_h - win_h) // 2
        self.win.geometry(f"{win_w}x{win_h}+{x}+{y}")
        self.win.transient(parent)
        self.win.grab_set()
        self.win.protocol("WM_DELETE_WINDOW", lambda: None)  # Disable close


        # Layout: Title, Message, Spinner
        self.title_label = tk.Label(self.win, text=self.title, font=("Arial", 15, "bold"))
        self.title_label.pack(pady=(18, 2))

        self.label = tk.Label(self.win, text=self.message, font=("Arial", 12))
        self.label.pack(pady=(0, 10))

        self.canvas = tk.Canvas(self.win, width=120, height=120, bg=self.win.cget("bg"), highlightthickness=0)
        self.canvas.pack(pady=(0, 0))


    def start_animation(self, title=None, message=None):
        self.win.lift()  # Bring to front
        self.win.focus_force()  # Focus on this window
        self.win.attributes("-topmost", True)  # Always on top
        if title:
            self.adjust_title(title)
        if message:
            self.adjust_message(message)
        self.running = True
        self._animate()

    def _animate(self):
        if not self.running:
            return
        self.canvas.delete("all")
        self.win.lift()  # Bring to front
        self.win.focus_force()  # Focus on this window
        self.win.attributes("-topmost", True)  # Always on top
        cx, cy = 60, 60  # center of canvas
        for i in range(self.spinner_positions):
            angle = 2 * math.pi * i / self.spinner_positions
            x = cx + self.radius * math.cos(angle)
            y = cy + self.radius * math.sin(angle)
            if i == self.spinner_index:
                color = "#0078D7"  # Windows blue for active dot
                r = self.dot_radius + 2
            else:
                color = "#cccccc"
                r = self.dot_radius
            self.canvas.create_oval(x - r, y - r, x + r, y + r, fill=color, outline="")
        self.spinner_index = (self.spinner_index + 1) % self.spinner_positions
        self._after_id = self.win.after(100, self._animate)

    def adjust_message(self, new_message):
        self.message = new_message
        self.label.config(text=self.message)

    def set_message_safe(self, txt):
        self.win.after(0, lambda: self.adjust_message(txt))

    def adjust_title(self, new_title):
        self.title = new_title
        self.win.title(new_title)

    def stop_animation(self):
        self.running = False
        if self._after_id:
            self.win.after_cancel(self._after_id)
        self.win.destroy()