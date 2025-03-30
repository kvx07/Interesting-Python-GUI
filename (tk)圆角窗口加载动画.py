import tkinter as tk
import math
import time


class LoadingScreen:
    def __init__(self):
        self.root = tk.Tk()
        self.root.overrideredirect(True)
        self.root.geometry("200x200+500+300")
        self.root.configure(bg='white')
        self.root.attributes('-transparentcolor', 'white')
        self.root.attributes('-topmost', True)

        self.canvas = tk.Canvas(self.root, bg='white', highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.draw_precise_rounded_rect()
        self.add_copyright_text()

        self.loading_arc = self.canvas.create_arc(
            60, 60, 140, 140,
            start=0,
            extent=0,
            outline='#0099FF',
            width=0,
            style=tk.ARC
        )

        self.start_time = time.time()
        self.drag_data = {"x": 0, "y": 0}

        self.canvas.bind("<ButtonPress-1>", self.start_drag)
        self.canvas.bind("<B1-Motion>", self.on_drag)

        self.animate()
        self.root.mainloop()

    def draw_precise_rounded_rect(self):
        r = 20
        w, h = 200, 200

        points = []
        for angle_group in [(180, 270), (270, 360), (0, 90), (90, 180)]:
            start, end = angle_group
            for angle in range(start, end + 1):
                rad = math.radians(angle)
                if angle_group == (180, 270):
                    x = r + r * math.cos(rad)
                    y = r + r * math.sin(rad)
                elif angle_group == (270, 360):
                    x = w - r + r * math.cos(rad)
                    y = r + r * math.sin(rad)
                elif angle_group == (0, 90):
                    x = w - r + r * math.cos(rad)
                    y = h - r + r * math.sin(rad)
                else:
                    x = r + r * math.cos(rad)
                    y = h - r + r * math.sin(rad)
                points.extend([x, y])

        self.canvas.create_polygon(
            points,
            fill='#2B2B2B',
            outline='white',
            smooth=False
        )

    def add_copyright_text(self):
        self.canvas.create_text(
            190, 190,
            text="designed by apple",
            anchor=tk.SE,
            fill='#888888',
            font=('Arial', 7)
        )

    def start_drag(self, event):
        self.drag_data["x"] = event.x_root
        self.drag_data["y"] = event.y_root

    def on_drag(self, event):
        dx = event.x_root - self.drag_data["x"]
        dy = event.y_root - self.drag_data["y"]
        self.root.geometry(f"+{self.root.winfo_x() + dx}+{self.root.winfo_y() + dy}")
        self.drag_data["x"] = event.x_root
        self.drag_data["y"] = event.y_root

    def animate(self):
        elapsed = time.time() - self.start_time
        progress = elapsed % 2

        angle = 0
        if elapsed < 0.5:
            width = 5 * (1 - math.cos(progress * math.pi))
            extent = 300 * (1 - math.cos(progress * math.pi))
        else:
            angle = (elapsed - 0.5) * 720 % 360
            width = 3 + 2 * math.sin(elapsed * 6 * math.pi)
            extent = 300

        self.canvas.itemconfig(
            self.loading_arc,
            start=angle - 2,
            extent=extent + 4,
            width=width
        )

        self.root.after(10, self.animate)


if __name__ == "__main__":
    LoadingScreen()
