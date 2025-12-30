import customtkinter as ctk
import sqlite3
import re
import sys
import threading
from PIL import Image, ImageDraw
from pynput import keyboard

# --- Configuration & Version ---
VERSION = "0.2.1"
DB_VERSION = 2

# --- Library Safety Checks ---
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

# --- Database & Migration Logic ---
def run_migrations():
    """Checks DB version and applies updates if needed."""
    conn = sqlite3.connect("vault.db")
    cursor = conn.cursor()
    
    # Check current DB version
    try:
        cursor.execute("PRAGMA user_version")
        current_v = cursor.fetchone()[0]
    except:
        current_v = 0

    # Initial Setup (v1)
    if current_v < 1:
        cursor.execute('''CREATE TABLE IF NOT EXISTS clips 
                          (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                           content TEXT UNIQUE, 
                           timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
        cursor.execute("PRAGMA user_version = 1")
        print("✅ Database initialized (v1)")

    # Update for v2 (Example: adding favorite column)
    if current_v < 2:
        try:
            cursor.execute("ALTER TABLE clips ADD COLUMN is_favorite INTEGER DEFAULT 0")
            cursor.execute("PRAGMA user_version = 2")
            print("✅ Database migrated to v2")
        except sqlite3.OperationalError:
            pass # Column likely exists

    conn.commit()
    conn.close()

def insert_clip(text):
    if not text.strip(): return False
    conn = sqlite3.connect("vault.db")
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT OR IGNORE INTO clips (content) VALUES (?)", (text,))
        return cursor.rowcount > 0
    except:
        return False
    finally:
        conn.close()

def fetch_clips(search_query=""):
    conn = sqlite3.connect("vault.db")
    cursor = conn.cursor()
    if search_query:
        cursor.execute("SELECT content FROM clips WHERE content LIKE ? ORDER BY id ASC", (f"%{search_query}%",))
    else:
        cursor.execute("SELECT content FROM clips ORDER BY id ASC")
    rows = cursor.fetchall()
    conn.close()
    return [row[0] for row in rows]

def delete_clip_from_db(text):
    conn = sqlite3.connect("vault.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM clips WHERE content = ?", (text,))
    conn.commit()
    conn.close()

# --- Text Processing (Reshaping) ---
def process_text_for_display(text):
    """Reshapes text for Label/Button display (Not for Entry)"""
    if re.search(r'[\u0600-\u06FF]', text):
        if HAS_RESHAPER:
            try:
                reshaped = arabic_reshaper.reshape(text)
                bidi = get_display(reshaped)
                return bidi, "e", ("Arial", 14)
            except: pass
        return text, "e", ("Arial", 14)
    return text, "w", ("Consolas", 13)

# --- System Tray Icon Generator ---
def create_icon_image():
    image = Image.new('RGB', (64, 64), color=(30, 144, 255))
    d = ImageDraw.Draw(image)
    d.rectangle([16, 16, 48, 48], fill="white")
    return image

# --- Main GUI Application ---
class ClipVaultApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title(f"Clip Vault v{VERSION}")
        self.geometry("400x650")
        ctk.set_appearance_mode("dark")
        
        self.clip_widgets = []
        self.last_detected_clip = "" 
        self.is_farsi_mode = False 
        self.hotkey_listener = None

        # Handle 'X' button -> Hide instead of destroy
        self.protocol("WM_DELETE_WINDOW", self.hide_window)

        # --- UI LAYOUT ---
        # 1. Header
        self.top_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.top_frame.pack(pady=10, padx=10, fill="x")

        self.label = ctk.CTkLabel(self.top_frame, text="Clipboard History", font=("Arial", 20, "bold"))
        self.label.pack()

        self.shortcut_label = ctk.CTkLabel(self.top_frame, text="Toggle: Ctrl + Space", font=("Arial", 10), text_color="#2CC985")
        self.shortcut_label.pack(pady=(0, 5))

        # 2. Search Area
        self.search_container = ctk.CTkFrame(self.top_frame, fg_color="transparent")
        self.search_container.pack(fill="x", pady=5)

        # Language Toggle Button
        self.lang_btn = ctk.CTkButton(self.search_container, text="EN", width=40, fg_color="#2CC985", command=self.toggle_language)
        self.lang_btn.pack(side="right", padx=(5, 0))

        # Stack Frame for "Overlay" trick
        self.stack_frame = ctk.CTkFrame(self.search_container, fg_color="transparent")
        self.stack_frame.pack(side="left", fill="x", expand=True)

        # The Actual Input (Hidden in FA mode)
        self.search_entry = ctk.CTkEntry(self.stack_frame, placeholder_text="Search...", justify="left", font=("Consolas", 14), text_color="#FFFFFF")
        self.search_entry.pack(fill="x", expand=True)
        self.search_entry.bind("<KeyRelease>", self.perform_search)

        # The Visual Overlay (Visible in FA mode)
        self.overlay_label = ctk.CTkLabel(self.search_entry, text="", text_color="#FFFFFF", font=("Arial", 14), bg_color="transparent", anchor="e")
        self.overlay_label.place_forget()

        # 3. Clips List
        self.scrollable_frame = ctk.CTkScrollableFrame(self, width=350, height=450)
        self.scrollable_frame.pack(pady=(0, 10), padx=10, fill="both", expand=True)
        
        self.hint_label = ctk.CTkLabel(self, text="Right-click to delete | Runs in background", text_color="gray", font=("Arial", 10))
        self.hint_label.pack(side="bottom", pady=5)

        # --- Initialization ---
        self.load_clips_to_ui()
        self.check_clipboard()
        
        if HAS_TRAY:
            self.setup_tray_icon()
            
        # Start Global Hotkey
        self.start_hotkey_listener()

    # --- Hotkey Logic ---
    def start_hotkey_listener(self):
        """Robust Global Hotkey using pynput.GlobalHotKeys"""
        self.hotkey_listener = keyboard.GlobalHotKeys({
            '<ctrl>+<space>': self.on_hotkey_press
        })
        self.hotkey_listener.start()

    def on_hotkey_press(self):
        # Must use .after to interact with GUI from another thread
        self.after(0, self.toggle_window_visibility)

    def toggle_window_visibility(self):
        """Smart Toggle: Checks real visibility status."""
        if self.winfo_viewable(): 
            self.hide_window()
        else:
            self.show_window()

    def hide_window(self):
        self.withdraw()

    def show_window(self, icon=None, item=None):
        self.deiconify()
        # Linux-specific force focus sequence
        self.lift()
        self.attributes('-topmost', True)
        self.after(50, lambda: self.attributes('-topmost', False))
        self.focus_force()
        self.search_entry.focus_set()

    # --- Search & Language Logic ---
    def toggle_language(self):
        self.is_farsi_mode = not self.is_farsi_mode
        if self.is_farsi_mode:
            # FA MODE
            self.lang_btn.configure(text="FA", fg_color="#3B8ED0")
            self.search_entry.configure(text_color="#343638") # Hide original text (approx dark color)
            self.overlay_label.place(relx=0.02, rely=0.1, relwidth=0.96, relheight=0.8)
            self.search_entry.focus()
            self.perform_search()
        else:
            # EN MODE
            self.lang_btn.configure(text="EN", fg_color="#2CC985")
            self.search_entry.configure(text_color="#FFFFFF")
            self.overlay_label.place_forget()
            self.search_entry.focus()

    def perform_search(self, event=None):
        query = self.search_entry.get()
        
        # Update Overlay for Farsi
        if self.is_farsi_mode:
            if query:
                if HAS_RESHAPER:
                    try:
                        reshaped = arabic_reshaper.reshape(query)
                        bidi = get_display(reshaped)
                        self.overlay_label.configure(text=f"| {bidi}")
                    except: self.overlay_label.configure(text=query)
                else: self.overlay_label.configure(text=query)
            else:
                self.overlay_label.configure(text="")
        
        self.load_clips_to_ui(query)

    # --- Core Features ---
    def setup_tray_icon(self):
        image = create_icon_image()
        menu = pystray.Menu(pystray.MenuItem("Show", self.show_window), pystray.MenuItem("Quit", self.quit_app))
        self.icon = pystray.Icon("ClipVault", image, "Clip Vault", menu)
        threading.Thread(target=self.icon.run, daemon=True).start()

    def quit_app(self, icon=None, item=None):
        if HAS_TRAY: self.icon.stop()
        if self.hotkey_listener: self.hotkey_listener.stop()
        self.quit()
        sys.exit()

    def create_clip_button(self, text):
        display, anchor, font = process_text_for_display(text)
        if len(display) > 50: display = display[:50] + "..."
        
        btn = ctk.CTkButton(
            self.scrollable_frame, 
            text=display, 
            fg_color="#333333", 
            anchor=anchor, 
            font=font, 
            hover_color="#444444", 
            command=lambda t=text: self.copy_to_clipboard(t)
        )
        btn.bind("<Button-3>", lambda e, t=text, w=btn: self.delete_clip(t, w))
        return btn

    def load_clips_to_ui(self, search_query=""):
        for w in self.clip_widgets: w.destroy()
        self.clip_widgets.clear()
        clips = fetch_clips(search_query)
        for t in clips: self.add_single_clip(t)

    def add_single_clip(self, text):
        btn = self.create_clip_button(text)
        if self.clip_widgets: btn.pack(before=self.clip_widgets[0], fill="x", pady=2, padx=5)
        else: btn.pack(fill="x", pady=2, padx=5)
        self.clip_widgets.insert(0, btn)

    def delete_clip(self, text, widget):
        delete_clip_from_db(text)
        widget.destroy()
        if widget in self.clip_widgets: self.clip_widgets.remove(widget)

    def copy_to_clipboard(self, text):
        self.last_detected_clip = text 
        self.clipboard_clear()
        self.clipboard_append(text)
        self.update() 
        # Uncomment to auto-hide after copy
        # self.hide_window()

    def check_clipboard(self):
        try:
            curr = self.clipboard_get()
            if curr != self.last_detected_clip:
                if insert_clip(curr):
                    self.last_detected_clip = curr
                    if not self.search_entry.get(): self.add_single_clip(curr)
        except: pass
        self.after(1000, self.check_clipboard)

if __name__ == "__main__":
    run_migrations() # Update DB Schema before starting UI
    app = ClipVaultApp()
    app.mainloop()