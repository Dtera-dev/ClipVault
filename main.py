import customtkinter as ctk
import sqlite3
import re
import sys
import threading
import os
from PIL import Image, ImageDraw
from pynput import keyboard

# --- Configuration ---
VERSION = "0.3.0"
DB_VERSION = 2

# --- Path Configuration (CRITICAL FOR LINUX/APPIMAGE) ---
if sys.platform == "win32":
    APP_DATA_DIR = os.path.join(os.getenv("APPDATA"), "ClipVault")
else:
    APP_DATA_DIR = os.path.join(os.path.expanduser("~"), ".config", "ClipVault")

if not os.path.exists(APP_DATA_DIR):
    try:
        os.makedirs(APP_DATA_DIR)
    except OSError: pass

DB_PATH = os.path.join(APP_DATA_DIR, "vault.db")
print(f"📁 Database Path: {DB_PATH}")

# --- Library Checks ---
try:
    import arabic_reshaper
    from bidi.algorithm import get_display
    HAS_RESHAPER = True
except ImportError:
    HAS_RESHAPER = False

try:
    import pystray
    HAS_TRAY = True
except ImportError:
    HAS_TRAY = False

# --- Database Core ---
def run_migrations():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("PRAGMA user_version")
        res = cursor.fetchone()
        current_v = res[0] if res else 0
    except: current_v = 0

    if current_v < 1:
        cursor.execute('''CREATE TABLE IF NOT EXISTS clips 
                          (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                           content TEXT UNIQUE, 
                           timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
        cursor.execute("PRAGMA user_version = 1")

    if current_v < 2:
        try:
            cursor.execute("ALTER TABLE clips ADD COLUMN is_favorite INTEGER DEFAULT 0")
            cursor.execute("PRAGMA user_version = 2")
        except: pass 
    conn.commit()
    conn.close()

def insert_clip(text):
    if not text.strip(): return False
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT OR IGNORE INTO clips (content, is_favorite) VALUES (?, 0)", (text,))
        return cursor.rowcount > 0
    except: return False
    finally: conn.close()

def update_clip_content(old_text, new_text):
    if not new_text.strip(): return False
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE clips SET content = ? WHERE content = ?", (new_text, old_text))
        conn.commit()
        return True
    except: return False 
    finally: conn.close()

def fetch_clips(search_query=""):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        if search_query:
            cursor.execute("SELECT content, is_favorite FROM clips WHERE content LIKE ? ORDER BY is_favorite DESC, id DESC", (f"%{search_query}%",))
        else:
            cursor.execute("SELECT content, is_favorite FROM clips ORDER BY is_favorite DESC, id DESC")
        rows = cursor.fetchall()
    except: rows = []
    finally: conn.close()
    return rows

def toggle_pin_in_db(text):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE clips SET is_favorite = NOT is_favorite WHERE content = ?", (text,))
    conn.commit()
    conn.close()

def delete_clip_from_db(text):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM clips WHERE content = ?", (text,))
    conn.commit()
    conn.close()

# --- Helpers ---
def process_text_for_display(text):
    if re.search(r'[\u0600-\u06FF]', text):
        if HAS_RESHAPER:
            try:
                reshaped = arabic_reshaper.reshape(text)
                bidi = get_display(reshaped)
                return bidi, "e", ("Arial", 14)
            except: pass
        return text, "e", ("Arial", 14)
    return text, "w", ("Consolas", 13)

def create_icon_image():
    image = Image.new('RGB', (64, 64), color=(30, 30, 30))
    d = ImageDraw.Draw(image)
    d.rectangle([16, 16, 48, 48], fill="white") 
    return image

# --- CUSTOM UI COMPONENTS ---

class EditDialog(ctk.CTkToplevel):
    def __init__(self, parent, old_text, on_save_callback):
        super().__init__(parent)
        self.title("Edit")
        self.geometry("400x300")
        self.old_text = old_text
        self.on_save = on_save_callback
        
        # Center logic
        self.update_idletasks()
        ws, hs = self.winfo_screenwidth(), self.winfo_screenheight()
        x = (ws/2) - (400/2)
        y = (hs/2) - (300/2)
        self.geometry(f"400x300+{int(x)}+{int(y)}")
        
        self.attributes('-topmost', True)
        self.configure(fg_color="#1a1a1a")
        
        self.textbox = ctk.CTkTextbox(self, font=("Consolas", 14), wrap="word", fg_color="#2b2b2b", text_color="white")
        self.textbox.pack(fill="both", expand=True, padx=10, pady=10)
        self.textbox.insert("0.0", old_text)
        
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        ctk.CTkButton(btn_frame, text="Cancel", fg_color="#555", width=80, command=self.destroy).pack(side="right", padx=5)
        ctk.CTkButton(btn_frame, text="Save", fg_color="#2CC985", width=80, command=self.save_click).pack(side="right", padx=5)
        
    def save_click(self):
        new_text = self.textbox.get("0.0", "end").strip()
        if new_text and new_text != self.old_text:
            self.on_save(self.old_text, new_text)
        self.destroy()

class ModernContextMenu(ctk.CTkToplevel):
    def __init__(self, parent, x, y, text, is_fav, callbacks):
        super().__init__(parent)
        self.callbacks = callbacks 
        self.text = text
        
        self.overrideredirect(True) 
        self.geometry(f"160x130+{x}+{y}")
        self.configure(fg_color="#252525")
        
        self.focus_force()
        self.bind("<FocusOut>", lambda e: self.destroy())
        self.bind("<Escape>", lambda e: self.destroy())

        # Menu Items - FIXED ARGUMENTS
        self.add_menu_item("Edit Text", self.on_edit)
        
        pin_label = "Unpin Item" if is_fav else "Pin to Top"
        pin_bg = "#D2691E" if is_fav else "transparent"
        self.add_menu_item(pin_label, self.on_pin, bg_color=pin_bg)
        
        self.add_separator()
        self.add_menu_item("Delete", self.on_delete, hover_color="#8B0000", text_color="#FF6666")

    def add_menu_item(self, text, command, bg_color="transparent", hover_color="#3A3A3A", text_color="white"):
        # Fixed the argument names to prevent TypeError
        btn = ctk.CTkButton(
            self, text=text, fg_color=bg_color, hover_color=hover_color, text_color=text_color,
            anchor="w", height=32, corner_radius=0, command=lambda: [command(), self.destroy()]
        )
        btn.pack(fill="x", padx=1, pady=1)

    def add_separator(self):
        ctk.CTkFrame(self, height=1, fg_color="#444").pack(fill="x", pady=2)

    def on_edit(self): self.callbacks['edit'](self.text)
    def on_pin(self): self.callbacks['pin'](self.text)
    def on_delete(self): self.callbacks['delete'](self.text)

# --- MAIN APP ---
class ClipVaultApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(f"ClipVault v{VERSION}")
        self.geometry("400x650")
        ctk.set_appearance_mode("dark")
        
        self.clip_widgets = []
        self.last_detected_clip = "" 
        self.is_farsi_mode = False 
        self.hotkey_listener = None

        self.protocol("WM_DELETE_WINDOW", self.hide_window)

        # Header
        self.top_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.top_frame.pack(pady=10, padx=10, fill="x")
        ctk.CTkLabel(self.top_frame, text="Clipboard History", font=("Arial", 20, "bold")).pack()
        ctk.CTkLabel(self.top_frame, text="Toggle: Ctrl + Space", font=("Arial", 10), text_color="#2CC985").pack(pady=(0,5))

        # Search
        self.search_container = ctk.CTkFrame(self.top_frame, fg_color="transparent")
        self.search_container.pack(fill="x", pady=5)
        self.lang_btn = ctk.CTkButton(self.search_container, text="EN", width=40, fg_color="#2CC985", command=self.toggle_language)
        self.lang_btn.pack(side="right", padx=(5, 0))
        
        self.stack_frame = ctk.CTkFrame(self.search_container, fg_color="transparent")
        self.stack_frame.pack(side="left", fill="x", expand=True)
        self.search_entry = ctk.CTkEntry(self.stack_frame, placeholder_text="Search...", justify="left", font=("Consolas", 14), text_color="#FFFFFF")
        self.search_entry.pack(fill="x", expand=True)
        self.search_entry.bind("<KeyRelease>", self.perform_search)
        
        # Farsi Overlay
        self.overlay_label = ctk.CTkLabel(self.search_entry, text="", text_color="#FFFFFF", font=("Arial", 14), bg_color="transparent", anchor="e")
        self.overlay_label.place_forget()

        # List
        self.scrollable_frame = ctk.CTkScrollableFrame(self, width=350, height=450)
        self.scrollable_frame.pack(pady=(0, 10), padx=10, fill="both", expand=True)
        ctk.CTkLabel(self, text="Right-click for Options", text_color="gray", font=("Arial", 10)).pack(side="bottom", pady=5)

        self.load_clips_to_ui()
        self.check_clipboard()
        if HAS_TRAY: self.setup_tray_icon()
        self.start_hotkey_listener()

    # --- Mouse Follower Logic ---
    def show_window(self, icon=None, item=None):
        w, h = 400, 650
        mx, my = self.winfo_pointerx(), self.winfo_pointery()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        
        nx = mx + 10
        if nx + w > sw: nx = mx - w - 10
        ny = my
        if ny + h > sh: ny = sh - h - 50
        if ny < 0: ny = 0

        self.geometry(f"{w}x{h}+{nx}+{ny}")
        self.deiconify()
        self.lift()
        self.attributes('-topmost', True)
        self.after(50, lambda: self.attributes('-topmost', False))
        self.focus_force()
        self.search_entry.focus_set()

    def hide_window(self): self.withdraw()

    # --- Actions ---
    def open_modern_menu(self, event, text, is_fav):
        callbacks = {
            'edit': lambda t: EditDialog(self, t, self.save_edited_clip),
            'pin': lambda t: self.toggle_pin(t),
            'delete': lambda t: self.delete_clip(t, None) 
        }
        ModernContextMenu(self, event.x_root, event.y_root, text, is_fav, callbacks)

    def save_edited_clip(self, old, new):
        if update_clip_content(old, new):
            self.load_clips_to_ui(self.search_entry.get())

    def toggle_pin(self, text):
        toggle_pin_in_db(text)
        self.load_clips_to_ui(self.search_entry.get())

    def delete_clip(self, text, widget):
        delete_clip_from_db(text)
        self.load_clips_to_ui(self.search_entry.get())

    def toggle_language(self):
        self.is_farsi_mode = not self.is_farsi_mode
        if self.is_farsi_mode:
            self.lang_btn.configure(text="FA", fg_color="#3B8ED0")
            self.search_entry.configure(text_color="#343638")
            self.overlay_label.place(relx=0.02, rely=0.1, relwidth=0.96, relheight=0.8)
        else:
            self.lang_btn.configure(text="EN", fg_color="#2CC985")
            self.search_entry.configure(text_color="#FFFFFF")
            self.overlay_label.place_forget()
        self.search_entry.focus()
        self.perform_search()

    def perform_search(self, event=None):
        query = self.search_entry.get()
        if self.is_farsi_mode and query and HAS_RESHAPER:
            try: self.overlay_label.configure(text=f"| {get_display(arabic_reshaper.reshape(query))}")
            except: self.overlay_label.configure(text=query)
        elif self.is_farsi_mode: self.overlay_label.configure(text="")
        self.load_clips_to_ui(query)

    # --- Loading UI ---
    def load_clips_to_ui(self, search_query=""):
        for w in self.clip_widgets: w.destroy()
        self.clip_widgets.clear()
        for text, is_fav in fetch_clips(search_query):
             self.add_single_clip(text, is_fav)

    def add_single_clip(self, text, is_fav=0):
        display, anchor, font = process_text_for_display(text)
        
        # Professional Star Icon
        prefix = "★ " if is_fav else ""
        display_text = prefix + display
        if len(display_text) > 50: display_text = display_text[:50] + "..."
        
        # Colors (Gold for Pin, Dark for Normal)
        btn_color = "#B8860B" if is_fav else "#333333"
        hover_color = "#D2691E" if is_fav else "#444444"

        btn = ctk.CTkButton(
            self.scrollable_frame, text=display_text, fg_color=btn_color, anchor=anchor, font=font, hover_color=hover_color, 
            command=lambda t=text: self.copy_to_clipboard(t)
        )
        btn.bind("<Button-3>", lambda e, t=text, f=is_fav: self.open_modern_menu(e, t, f))
        btn.pack(fill="x", pady=2, padx=5)
        self.clip_widgets.append(btn)

    def copy_to_clipboard(self, text):
        self.last_detected_clip = text 
        self.clipboard_clear()
        self.clipboard_append(text)
        self.update() 

    def check_clipboard(self):
        try:
            curr = self.clipboard_get()
            if curr != self.last_detected_clip:
                if insert_clip(curr):
                    self.last_detected_clip = curr
                    if not self.search_entry.get(): self.load_clips_to_ui()
        except: pass
        self.after(1000, self.check_clipboard)

    def setup_tray_icon(self):
        menu = pystray.Menu(pystray.MenuItem("Show", self.show_window), pystray.MenuItem("Quit", self.quit_app))
        self.icon = pystray.Icon("ClipVault", create_icon_image(), "Clip Vault", menu)
        threading.Thread(target=self.icon.run, daemon=True).start()

    def start_hotkey_listener(self):
        self.hotkey_listener = keyboard.GlobalHotKeys({'<ctrl>+<space>': lambda: self.after(0, self.toggle_visibility)})
        self.hotkey_listener.start()

    def toggle_visibility(self):
        if self.winfo_viewable(): self.hide_window()
        else: self.show_window()

    def quit_app(self, i=None, it=None):
        if HAS_TRAY: self.icon.stop()
        if self.hotkey_listener: self.hotkey_listener.stop()
        self.quit()
        sys.exit()

if __name__ == "__main__":
    run_migrations()
    app = ClipVaultApp()
    app.mainloop()