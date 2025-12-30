import os
import shutil
import sys

# --- Config ---
APP_NAME = "ClipVault"
BINARY_SOURCE = "dist/ClipVault" # مسیری که پای‌اینستالر فایل رو ساخته
ICON_SOURCE = "icon.png"

INSTALL_DIR = os.path.expanduser("~/.local/bin")
DESKTOP_DIR = os.path.expanduser("~/.local/share/applications")
AUTOSTART_DIR = os.path.expanduser("~/.config/autostart")
ICON_DIR = os.path.expanduser("~/.local/share/icons")

def install():
    print("🚀 Installing ClipVault v0.3.0 (Binary Method)...")

    # 1. Check if binary exists
    if not os.path.exists(BINARY_SOURCE):
        print(f"❌ Error: Could not find binary at '{BINARY_SOURCE}'")
        print("   Did you run 'pyinstaller ...' first?")
        return

    # 2. Create directories
    for d in [INSTALL_DIR, DESKTOP_DIR, AUTOSTART_DIR, ICON_DIR]:
        os.makedirs(d, exist_ok=True)

    # 3. Copy Binary
    dest_binary = os.path.join(INSTALL_DIR, APP_NAME)
    shutil.copy(BINARY_SOURCE, dest_binary)
    os.chmod(dest_binary, 0o755) # Make executable
    print(f"✅ Binary installed to: {dest_binary}")

    # 4. Copy Icon
    dest_icon = os.path.join(ICON_DIR, "clipvault.png")
    if os.path.exists(ICON_SOURCE):
        shutil.copy(ICON_SOURCE, dest_icon)
    else:
        print("⚠️ Icon not found, skipping icon copy.")
        dest_icon = "utilities-terminal" # Fallback icon

    # 5. Create .desktop file content
    desktop_content = f"""[Desktop Entry]
Type=Application
Name={APP_NAME}
Comment=Clipboard Manager v0.3.0
Exec={dest_binary}
Icon={dest_icon}
Terminal=false
Categories=Utility;
X-GNOME-Autostart-enabled=true
"""

    # 6. Write .desktop files (Menu & Autostart)
    desktop_file = os.path.join(DESKTOP_DIR, "clipvault.desktop")
    autostart_file = os.path.join(AUTOSTART_DIR, "clipvault.desktop")

    with open(desktop_file, "w") as f:
        f.write(desktop_content)
    
    with open(autostart_file, "w") as f:
        f.write(desktop_content)

    # Make desktop files executable (important for some distros)
    os.chmod(desktop_file, 0o755)
    os.chmod(autostart_file, 0o755)

    print(f"✅ Desktop entry created.")
    print(f"✅ Autostart entry created.")
    print("\n🎉 INSTALLATION COMPLETE!")
    print("👉 You can now launch 'ClipVault' from your app menu.")
    print("👉 Try pressing Ctrl+Space to toggle it!")

if __name__ == "__main__":
    install()