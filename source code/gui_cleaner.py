#!/usr/bin/env python3
import argparse
import math
import queue
import threading
import tkinter as tk
import tkinter.font as tkfont
from tkinter import filedialog, messagebox

# blah blah backend Engine 
import scrubbey_clean

WIN_W = 640
MARGIN = 24

STRIPE_DARK = "#EDEDED"
STRIPE_LIGHT = "#F7F7F7"
BOX_DARK = "#E2E2E2"
BOX_LIGHT = "#EBEBEB"
BOX_BORDER = "#ADADAD"
TEXT = "#1A1A1A"
TEXT_DIM = "#5C5C5C"

GEL_SILVER = [(0.00, "#FFFFFF"), (0.48, "#ECECEC"), (0.52, "#DADADA"), (1.00, "#F3F3F3")]
GEL_BLUE = [(0.00, "#CFE6FF"), (0.48, "#8AC0F9"), (0.52, "#3F94EC"), (0.85, "#3B8DE8"), (1.00, "#8CCBFC")]
GEL_BLUE_GLOW = [(0.00, "#E4F1FF"), (0.48, "#ADD5FC"), (0.52, "#62ABF4"), (0.85, "#5EA7F1"), (1.00, "#B0DAFD")]
GEL_BLUE_DOWN = [(0.00, "#9CC2EE"), (0.48, "#5A97E0"), (0.52, "#2468CC"), (1.00, "#5599E3")]
GEL_OFF = [(0.00, "#F7F7F7"), (1.00, "#E6E6E6")]
LCD_GLASS = [(0.00, "#BFC9D6"), (0.15, "#DCE3EB"), (1.00, "#EFF3F7")]
TRACK = [(0.00, "#C9CFD6"), (1.00, "#F4F6F8")]
FONT_CANDIDATES = ("Lucida Grande", "Helvetica Neue", "Helvetica", "Arial", "DejaVu Sans")

def pick_font(root, candidates):
    installed = set(tkfont.families(root))
    for name in candidates:
        if name in installed:
            return name
    return tkfont.nametofont("TkDefaultFont").actual("family")

def hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))

def rgb_to_hex(rgb):
    return "#%02x%02x%02x" % tuple(max(0, min(255, round(c))) for c in rgb)

def mix(c1, c2, t):
    a, b = hex_to_rgb(c1), hex_to_rgb(c2)
    return rgb_to_hex([a[i] + (b[i] - a[i]) * t for i in range(3)])

def gradient_color(stops, t):
    if t <= stops[0][0]:
        return stops[0][1]
    for (p0, c0), (p1, c1) in zip(stops, stops[1:]):
        if t <= p1:
            return mix(c0, c1, (t - p0) / (p1 - p0))
    return stops[-1][1]

def fill_round_rect(cv, x0, y0, x1, y1, r, color, tags=(), round_left=True, round_right=True):
    paint = color if callable(color) else (lambda t, c=color: c)
    height = int(y1 - y0)
    r = min(r, height / 2, (x1 - x0) / 2)
    ids = []
    for i in range(height):
        d = min(i + 0.5, height - i - 0.5)
        inset = r - math.sqrt(r * r - (r - d) ** 2) if d < r else 0
        left = x0 + (inset if round_left else 0)
        right = x1 - (inset if round_right else 0)
        ids.append(cv.create_rectangle(
            left, y0 + i, right, y0 + i + 1,
            fill=paint((i + 0.5) / height), outline="", tags=tags))
    return ids

def repaint(cv, ids, color):
    paint = color if callable(color) else (lambda t, c=color: c)
    n = len(ids)
    for i, item in enumerate(ids):
        cv.itemconfigure(item, fill=paint((i + 0.5) / n))

def round_rect_points(x0, y0, x1, y1, r):
    return [x0 + r, y0, x0 + r, y0, x1 - r, y0, x1 - r, y0, x1, y0, x1, y0 + r,
            x1, y0 + r, x1, y1 - r, x1, y1 - r, x1, y1, x1 - r, y1, x1 - r, y1,
            x0 + r, y1, x0 + r, y1, x0, y1, x0, y1 - r, x0, y1 - r, x0, y0 + r,
            x0, y0 + r, x0, y0]

def draw_pinstripes(cv, w, h):
    for y in range(2, h, 4):
        cv.create_rectangle(0, y, w, y + 2, fill=STRIPE_LIGHT, outline="", tags="pinstripe")
    cv.tag_lower("pinstripe")

def draw_app_logo(cv, x, y):
    # SERVER LOOKIN AHH
    fill_round_rect(cv, x, y + 11, x + 28, y + 65, 4, "#1A252F") 
    fill_round_rect(cv, x + 1, y + 10, x + 27, y + 64, 3, "#2C3E50")
    cv.create_line(x + 5, y + 20, x + 23, y + 20, fill="#34495E", width=2)
    cv.create_line(x + 5, y + 26, x + 23, y + 26, fill="#34495E", width=2)
    cv.create_oval(x + 6, y + 54, x + 10, y + 58, fill="#2ECC71", outline="") 
    cv.create_oval(x + 14, y + 54, x + 18, y + 58, fill="#E74C3C", outline="")

    # PLAYLIST w sparkle you know like clean or sum 
    px, py = x + 16, y + 4
    fill_round_rect(cv, px - 1, py - 1, px + 33, py + 41, 2, "#5C5C5C") 
    fill_round_rect(cv, px, py, px + 32, py + 40, 2, "#FFFFFF")
    for i in range(4):
        cv.create_line(px + 6, py + 10 + (i * 7), px + 26, py + 10 + (i * 7), fill="#5C5C5C", width=2)
        
    sx, sy = px + 30, py + 6
    cv.create_polygon(sx, sy-7, sx+2, sy-2, sx+7, sy, sx+2, sy+2, sx, sy+7, 
                      sx-2, sy+2, sx-7, sy, sx-2, sy-2, fill="#F1C40F", outline="#D4AC0D")

    # IPOD (Foreground Right)
    ix, iy = x + 28, y + 22
    fill_round_rect(cv, ix, iy + 1, ix + 30, iy + 45, 5, "#C4C4C4")
    fill_round_rect(cv, ix, iy, ix + 30, iy + 44, 4, "#8E8E8E")
    fill_round_rect(cv, ix + 1, iy + 1, ix + 29, iy + 43, 3, 
                    lambda t: gradient_color([(0, "#FFFFFF"), (1, "#DCDCDC")], t))
    
    fill_round_rect(cv, ix + 4, iy + 4, ix + 26, iy + 20, 2, "#6E7C8C")
    fill_round_rect(cv, ix + 5, iy + 5, ix + 25, iy + 19, 1, 
                    lambda t: gradient_color([(0, "#CBDDF0"), (1, "#EAF2FA")], t))
    
    cv.create_oval(ix + 6, iy + 22, ix + 24, iy + 40, fill="#F2F2F2", outline="#9A9A9A")
    cv.create_oval(ix + 12, iy + 28, ix + 18, iy + 34, fill="#FFFFFF", outline="#A9A9A9")

class AquaButton:
    def __init__(self, cv, x, y, w, h, text, command, font, default=False):
        self.cv, self.command, self.default = cv, command, default
        self.box = (x, y, x + w, y + h)
        self.enabled = True
        self._down = False
        self._inside = False
        self._phase = 0.0
        self._pulsing = False

        tag = "aquabutton%d" % id(self)
        r = h / 2
        fill_round_rect(cv, x, y + 1, x + w, y + h + 1, r, "#BEBEBE", tags=tag)
        self.edge = fill_round_rect(cv, x, y, x + w, y + h, r, "#8A8A8A", tags=tag)
        self.body = fill_round_rect(cv, x + 1, y + 1, x + w - 1, y + h - 1, r - 1, "#FFFFFF", tags=tag)
        self.label = cv.create_text(x + w / 2, y + h / 2, text=text, font=font, fill="#000000", tags=tag)

        cv.tag_bind(tag, "<ButtonPress-1>", self._on_press)
        cv.tag_bind(tag, "<B1-Motion>", self._on_drag)
        cv.tag_bind(tag, "<ButtonRelease-1>", self._on_release)

        self._paint()
        if default:
            self._start_pulse()

    def _paint(self):
        if not self.enabled:
            body, edge, ink = (lambda t: gradient_color(GEL_OFF, t)), "#C4C4C4", "#9A9A9A"
        elif self._down and self._inside:
            body, edge, ink = (lambda t: gradient_color(GEL_BLUE_DOWN, t)), "#1B4F9C", "#000000"
        elif self.default:
            glow = (1 - math.cos(self._phase * 2 * math.pi)) / 2
            body = lambda t: mix(gradient_color(GEL_BLUE, t), gradient_color(GEL_BLUE_GLOW, t), glow)
            edge, ink = "#2E62AD", "#000000"
        else:
            body, edge, ink = (lambda t: gradient_color(GEL_SILVER, t)), "#8A8A8A", "#000000"
        repaint(self.cv, self.body, body)
        repaint(self.cv, self.edge, edge)
        self.cv.itemconfigure(self.label, fill=ink)

    def _start_pulse(self):
        if not self._pulsing:
            self._pulsing = True
            self._pulse()

    def _pulse(self):
        if not (self.default and self.enabled):
            self._pulsing = False
            return
        self._phase = (self._phase + 0.045) % 1.0
        if not self._down:
            self._paint()
        self.cv.after(50, self._pulse)

    def set_enabled(self, flag):
        self.enabled = flag
        self._down = self._inside = False
        self._paint()
        if flag and self.default:
            self._start_pulse()

    def _hit(self, e):
        x0, y0, x1, y1 = self.box
        return x0 <= e.x <= x1 and y0 <= e.y <= y1

    def _on_press(self, e):
        if self.enabled:
            self._down = self._inside = True
            self._paint()

    def _on_drag(self, e):
        if self._down and self._hit(e) != self._inside:
            self._inside = not self._inside
            self._paint()

    def _on_release(self, e):
        if not self._down:
            return
        fire = self._inside and self._hit(e)
        self._down = self._inside = False
        self._paint()
        if fire and self.enabled:
            self.command()

class AquaCheckbox:
    def __init__(self, cv, x, cy, text, variable, font):
        self.cv, self.var = cv, variable
        self._down = self._inside = False
        top = int(cy - 8)
        tag = "aquacheck%d" % id(self)
        self.edge = fill_round_rect(cv, x, top, x + 16, top + 16, 4, "#7C7C7C", tags=tag)
        self.body = fill_round_rect(cv, x + 1, top + 1, x + 15, top + 15, 3,
                                    lambda t: gradient_color(GEL_SILVER, t), tags=tag)
        self.tick = cv.create_line(x + 3.5, top + 8.5, x + 6.5, top + 12, x + 12.5, top + 3.5,
                                   width=2.2, fill="#111111", capstyle="round", joinstyle="round", tags=tag)
        cv.create_text(x + 22, cy, text=text, anchor="w", font=font, fill=TEXT, tags=tag)
        self.hit = cv.bbox(tag)

        cv.tag_bind(tag, "<ButtonPress-1>", self._on_press)
        cv.tag_bind(tag, "<B1-Motion>", self._on_drag)
        cv.tag_bind(tag, "<ButtonRelease-1>", self._on_release)

        variable.trace_add("write", lambda *_: self._sync())
        self._sync()

    def _sync(self):
        self.cv.itemconfigure(self.tick, state="normal" if self.var.get() else "hidden")

    def _paint(self):
        pressed = self._down and self._inside
        repaint(self.cv, self.body, lambda t: gradient_color(GEL_BLUE_DOWN if pressed else GEL_SILVER, t))

    def _inside_box(self, e):
        x0, y0, x1, y1 = self.hit
        return x0 <= e.x <= x1 and y0 <= e.y <= y1

    def _on_press(self, e):
        self._down = self._inside = True
        self._paint()

    def _on_drag(self, e):
        if self._down and self._inside_box(e) != self._inside:
            self._inside = not self._inside
            self._paint()

    def _on_release(self, e):
        fire = self._down and self._inside and self._inside_box(e)
        self._down = self._inside = False
        self._paint()
        if fire:
            self.var.set(not self.var.get())

class AquaPopup:
    def __init__(self, cv, x, y, w, h, variable, values, font):
        self.cv, self.var = cv, variable
        self.box = (x, y, x + w, y + h)
        tag = "aquapopup%d" % id(self)
        r = h / 2
        fill_round_rect(cv, x, y + 1, x + w, y + h + 1, r, "#BEBEBE", tags=tag)
        fill_round_rect(cv, x, y, x + w, y + h, r, "#8A8A8A", tags=tag)
        fill_round_rect(cv, x + 1, y + 1, x + w - 1, y + h - 1, r - 1,
                        lambda t: gradient_color(GEL_SILVER, t), tags=tag)
        cap = 24
        fill_round_rect(cv, x + w - cap, y + 1, x + w - 1, y + h - 1, r - 1,
                        lambda t: gradient_color(GEL_BLUE, t), tags=tag, round_left=False)
        cv.create_line(x + w - cap, y + 1, x + w - cap, y + h - 1, fill="#5F86BD", tags=tag)
        cx, cy = x + w - cap / 2, y + h / 2
        for s in (-1, 1):
            cv.create_polygon(cx - 3.5, cy + s * 2, cx + 3.5, cy + s * 2, cx, cy + s * 6,
                              fill="#151515", outline="", tags=tag)
        self.text = cv.create_text(x + 12, cy, text=variable.get(), anchor="w", font=font, fill=TEXT, tags=tag)

        self.menu = tk.Menu(cv, tearoff=0)
        for v in values:
            self.menu.add_radiobutton(label=v, variable=variable, value=v)
        cv.tag_bind(tag, "<ButtonPress-1>", self._open)
        variable.trace_add("write", lambda *_: cv.itemconfigure(self.text, text=variable.get()))

    def _open(self, e):
        x0, y0, x1, y1 = self.box
        try:
            self.menu.tk_popup(self.cv.winfo_rootx() + x0, self.cv.winfo_rooty() + y1)
        finally:
            self.menu.grab_release()

class AquaEntry:
    def __init__(self, cv, x, y, w, h, variable, font):
        self.cv = cv
        self.rings = []
        for grow, col in ((3, "#BCD8F8"), (2, "#8FBDF4"), (1, "#5E9DEB")):
            pts = round_rect_points(x - grow, y - grow, x + w + grow, y + h + grow, 3 + grow)
            self.rings.append(cv.create_polygon(pts, smooth=True, fill="", outline=col, state="hidden"))
        cv.create_rectangle(x, y, x + w, y + h, fill="#FFFFFF", outline="#8E8E8E")
        cv.create_line(x + 1, y + 1, x + w, y + 1, fill="#D2D2D2")
        cv.create_line(x + 1, y + 2, x + w, y + 2, fill="#E8E8E8")

        self.entry = tk.Entry(cv, textvariable=variable, font=font, bd=0, relief="flat",
                              highlightthickness=0, bg="#FFFFFF", fg="#111111",
                              insertbackground="#111111",
                              selectbackground="#B5D5FB", selectforeground="#000000")
        cv.create_window(x + 5, y + 3, anchor="nw", window=self.entry, width=w - 8, height=h - 5)
        self.entry.bind("<FocusIn>", lambda e: self._glow(True))
        self.entry.bind("<FocusOut>", lambda e: self._glow(False))

    def _glow(self, on):
        for ring in self.rings:
            self.cv.itemconfigure(ring, state="normal" if on else "hidden")

class BarberPole:
    PERIOD, STEP = 16, 2
    def __init__(self, cv, x, y, w, h):
        self.cv = cv
        r = h / 2
        fill_round_rect(cv, x, y, x + w, y + h, r, "#8793A3")
        fill_round_rect(cv, x + 1, y + 1, x + w - 1, y + h - 1, r - 1,
                        lambda t: gradient_color(TRACK, t))
        self.frames = [self._make_frame(w - 2, h - 2, s) for s in range(0, self.PERIOD, self.STEP)]
        self.item = cv.create_image(x + 1, y + 1, image=self.frames[0], anchor="nw", state="hidden")
        self._i = 0
        self._running = False

    def _make_frame(self, w, h, shift):
        img = tk.PhotoImage(width=w, height=h)
        img.blank()
        r = h / 2
        for row in range(h):
            t = (row + 0.5) / h
            dark = gradient_color(GEL_BLUE, t)
            light = mix(dark, "#FFFFFF", 0.45)
            d = min(row + 0.5, h - row - 0.5)
            inset = math.ceil(r - math.sqrt(r * r - (r - d) ** 2)) if d < r else 0
            pixels = []
            for xx in range(inset, w - inset):
                stripe = ((xx - row + shift) % self.PERIOD) < self.PERIOD / 2
                pixels.append(light if stripe else dark)
            img.put("{" + " ".join(pixels) + "}", to=(inset, row))
        return img

    def start(self):
        if not self._running:
            self._running = True
            self.cv.itemconfigure(self.item, state="normal")
            self._step()

    def _step(self):
        if self._running:
            self._i = (self._i + 1) % len(self.frames)
            self.cv.itemconfigure(self.item, image=self.frames[self._i])
            self.cv.after(60, self._step)

    def stop(self):
        self._running = False
        self.cv.itemconfigure(self.item, state="hidden")

class ScrubbeyApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Scrubbey")
        self.root.resizable(False, False)

        self.input_path = tk.StringVar()
        self.library_path = tk.StringVar()
        self.output_path = tk.StringVar()

        self.paths_format = tk.StringVar(value="basename")
        self.fuzzy = tk.BooleanVar(value=True)
        self.no_extinf = tk.BooleanVar(value=True)
        self.dedupe = tk.BooleanVar(value=True)
        self.recursive = tk.BooleanVar(value=False)
        self.keep_missing = tk.BooleanVar(value=False)

        self.busy = False
        self.results = queue.Queue()

        self.create_widgets()
        self.root.bind("<Return>", lambda e: self.run_cleaner())
        self.root.bind("<KP_Enter>", lambda e: self.run_cleaner())

    def create_widgets(self):
        family = pick_font(self.root, FONT_CANDIDATES)
        f_title = (family, -21, "bold")
        f_body = (family, -13)
        f_label = (family, -12)
        f_bold = (family, -12, "bold")
        f_small = (family, -11)

        cv = tk.Canvas(self.root, width=WIN_W, height=700, bg=STRIPE_DARK, highlightthickness=0, bd=0)
        cv.pack()
        cv.bind("<Button-1>", lambda e: cv.focus_set())
        self.cv = cv

        draw_app_logo(cv, MARGIN, 16)
        cv.create_text(MARGIN + 85, 38, text="Scrubbey!", anchor="w", font=f_title, fill=TEXT)
        cv.create_text(MARGIN + 85, 64, text="Standardize and clean playlists for Navidrome, iOpenPod or any music software that supports M3U8 importing.", anchor="w", font=f_label, fill=TEXT_DIM, width=WIN_W - 120)
        cv.create_line(0, 96, WIN_W, 96, fill="#BDBDBD")
        cv.create_line(0, 97, WIN_W, 97, fill="#FFFFFF")

        inner_x = MARGIN + 18
        inner_w = WIN_W - 2 * MARGIN - 36

        top = self.group_box(cv, "Directory Setup", 118, 200, f_bold)
        fy = top + 16
        for label, var in (("1. Playlists Folder (Input):", self.input_path),
                           ("2. Music Library (Where audio files live):", self.library_path),
                           ("3. Output Folder (Leave blank to overwrite in-place):", self.output_path)):
            cv.create_text(inner_x, fy, text=label, anchor="nw", font=f_label, fill=TEXT)
            AquaEntry(cv, inner_x, fy + 20, inner_w - 100, 24, var, f_body)
            AquaButton(cv, inner_x + inner_w - 88, fy + 20, 88, 24, "Browse\u2026",
                       lambda v=var: self.browse_folder(v), f_body)
            fy += 62

        top = self.group_box(cv, "Cleaning Rules", top + 200 + 24, 196, f_bold)
        rules = (("Fuzzy Match (Ignore weird prefixes/punctuation)", self.fuzzy),
                 ("Remove Metadata / EXTINF (Straight names)", self.no_extinf),
                 ("Remove Duplicates", self.dedupe),
                 ("Keep Missing Tracks in List", self.keep_missing),
                 ("Recursive (Scan sub-folders)", self.recursive))
        for i, (text, var) in enumerate(rules):
            AquaCheckbox(cv, inner_x, top + 24 + i * 26, text, var, f_body)

        py = top + 24 + 4 * 26 + 40
        cv.create_text(inner_x, py, text="Path Format:", anchor="w", font=f_body, fill=TEXT)
        AquaPopup(cv, inner_x + 92, py - 11, 132, 22, self.paths_format,
                  ("basename", "relative", "absolute"), f_body)

        desc_label = cv.create_text(inner_x + 235, py, text="", anchor="w", font=f_small, fill=TEXT_DIM, width=310)

        format_descriptions = {
            "basename": "(e.g., Song.m4a) - Best if playlist and audio are in the same folder.",
            "relative": "(e.g., ../Music/Song.m4a) - Connects paths based on folder structure.",
            "absolute": "(e.g., /Users/Name/.../Song.m4a) - Hardcoded full path."
        }

        def update_format_desc(*args):
            current_choice = self.paths_format.get()
            self.cv.itemconfigure(desc_label, text=format_descriptions.get(current_choice, ""))

        self.paths_format.trace_add("write", update_format_desc)
        update_format_desc() 

        ly = top + 196 + 22
        lw, lh = WIN_W - 2 * MARGIN - 140, 58
        fill_round_rect(cv, MARGIN, ly, MARGIN + lw, ly + lh, 8, "#7D8794")
        fill_round_rect(cv, MARGIN + 1, ly + 1, MARGIN + lw - 1, ly + lh - 1, 7,
                        lambda t: gradient_color(LCD_GLASS, t))
        self.lcd_title = cv.create_text(MARGIN + 14, ly + 16, text=":)", anchor="w",
                                        font=f_bold, fill="#1B1F24")
        self.lcd_msg = cv.create_text(MARGIN + 14, ly + 32, anchor="w", font=f_small, fill="#4A5360",
                                      text="Ready. Pick your folders, then press Clean Playlists.")
        self.pole = BarberPole(cv, MARGIN + 14, ly + 40, lw - 28, 10)

        self.run_btn = AquaButton(cv, WIN_W - MARGIN - 124, ly + (lh - 28) // 2, 124, 28,
                                  "Clean Playlists", self.run_cleaner, f_body, default=True)

        height = ly + lh + MARGIN
        draw_pinstripes(cv, WIN_W, height)
        cv.configure(height=height)

    def group_box(self, cv, title, title_y, height, font):
        x0, x1 = MARGIN, WIN_W - MARGIN
        top = title_y + 12
        cv.create_text(x0 + 3, title_y, text=title, anchor="w", font=font, fill=TEXT)

        def stripes(t, first_row=top + 1, rows=height - 2):
            row = first_row + int(t * rows)
            return BOX_LIGHT if (row // 2) % 2 else BOX_DARK

        fill_round_rect(cv, x0, top, x1, top + height, 8, BOX_BORDER)
        fill_round_rect(cv, x0 + 1, top + 1, x1 - 1, top + height - 1, 7, stripes)
        return top

    def browse_folder(self, var):
        folder = filedialog.askdirectory()
        if folder:
            var.set(folder)

    def set_status(self, headline, detail):
        self.cv.itemconfigure(self.lcd_title, text=headline)
        self.cv.itemconfigure(self.lcd_msg, text=detail)

    def set_busy(self, busy):
        self.busy = busy
        self.run_btn.set_enabled(not busy)
        if busy:
            self.pole.start()
        else:
            self.pole.stop()

    def run_cleaner(self):
        if self.busy:
            return
        if not self.input_path.get() or not self.library_path.get():
            messagebox.showerror("Error", "Please select at least the Input and Library folders.")
            return

        args = argparse.Namespace(
            inputs=[self.input_path.get()],
            library=self.library_path.get(),
            out=self.output_path.get() if self.output_path.get() else None,
            paths=self.paths_format.get(),
            fuzzy=self.fuzzy.get(),
            no_extinf=self.no_extinf.get(),
            dedupe=self.dedupe.get(),
            recursive=self.recursive.get(),
            missing='keep' if self.keep_missing.get() else 'drop',
            prefix=None,
            unicode='keep',
            reverse=False,
            in_place=False
        )

        self.set_busy(True)
        self.set_status("Cleaning\u2026", "Working through them playlists. Hang tight!")
        threading.Thread(target=self._worker, args=(args,), daemon=True).start()
        self.root.after(100, self._poll_worker)

    def _worker(self, args):
        try:

            scrubbey_clean.run(args)
            self.results.put(("ok", None))
        except SystemExit as e:
            self.results.put(("error", f"The cleaner stopped early (exit code {e.code})."))
        except Exception as e:
            self.results.put(("error", str(e) or repr(e)))

    def _poll_worker(self):
        try:
            kind, payload = self.results.get_nowait()
        except queue.Empty:
            self.root.after(100, self._poll_worker)
            return
        self.set_busy(False)
        if kind == "ok":
            self.set_status(":)", "Done! Your playlists are now shiny like Mr. Clean!")
            messagebox.showinfo("Success", "Playlists successfully cleaned! Check your output folder.")
        else:
            self.set_status(":)", "Something went wrong. See the alert for details.")
            messagebox.showerror("Execution Error", f"An error occurred:\n{payload}")


if __name__ == "__main__":
    root = tk.Tk()
    app = ScrubbeyApp(root)
    root.mainloop()