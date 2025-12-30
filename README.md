# 🛡️ ClipVault
> **Version 0.3.0** | Professional, Lightweight & Secure Clipboard Manager for Linux.
![Platform](https://img.shields.io/badge/Platform-Linux-blue)
![Python](https://img.shields.io/badge/Python-3.10%2B-yellow)
![License](https://img.shields.io/badge/License-GPLv3-green)

ClipVault is a minimalist yet powerful clipboard management tool built for power users. It eliminates the frustration of losing copied snippets by providing a persistent, searchable, and editable history of your clipboard.

---

## 🚀 Key Highlights

- **Mouse-Centric HUD:** The interface opens exactly at your cursor's coordinates for zero-distraction workflow.
- **Advanced Pinning System:** Secure your most-used snippets at the top of the list with a professional ★ indicator.
- **In-place Editor:** Modify any captured text instantly without leaving the application.
- **Smart RTL Support:** Native rendering for Farsi, Arabic, and other Right-to-Left scripts using advanced reshaping algorithms.
- **Global Accessibility:** Toggle visibility from any workspace with a customizable global hotkey (`Ctrl + Space`).
- **Minimalist Aesthetics:** Designed with a dark "Mica" inspired UI, free from colorful emojis and clutter.

---

## 🛠 Feature Breakdown

### 📍 Intelligent Positioning
Unlike traditional managers that open in a fixed location, ClipVault calculates your screen boundaries and cursor position to spawn the window in the most ergonomic spot.

### 📝 Integrated Text Editing
Click "Edit Content" in the custom context menu to trigger a focused editing environment. Changes are reflected instantly across the database and UI.

### 📦 Persistence & Security
Uses a localized **SQLite3** engine. Your data never touches the cloud.
- **Schema:** `id (PK)`, `content (TEXT)`, `is_favorite (BOOL)`, `timestamp`.

---

## ⌨️ Command Shortcuts

| Action | Input |
| :--- | :--- |
| **Toggle Vault** | `Ctrl` + `Space` |
| **Copy Snippet** | `Left Click` |
| **Open Menu** | `Right Click` |
| **Close Window** | `Esc` or `Focus Out` |

---

## ⚙️ Installation

### Prerequisites
- **Python:** 3.10 or higher
- **Display Server:** X11 or Wayland (with XWayland)

### Setup from Source
```bash
# Clone the repository
git clone [https://github.com/Dtera-dev/ClipVault.git](https://github.com/Dtera-dev/ClipVault.git)
cd ClipVault

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py

```

### Binary Deployment

To build a standalone executable:

```bash
pyinstaller --onefile --windowed --name ClipVault main.py

```

---

## 🗺️ Project Roadmap

* [x] **v0.1.0:** Core clipboard monitoring and storage.
* [x] **v0.2.0:** RTL support and basic UI.
* [x] **v0.3.0:** (Current) Global hotkeys, Mouse positioning, Pinned items, and Edit mode.
* [ ] **v0.4.0:** Image/Screenshot support and localized blacklist for sensitive apps.
* [ ] **v0.5.0:** Plugin system for text transformation (e.g., Base64 decode, JSON format).

---

## 📄 License & Legal

This project is licensed under the **GNU GPLv3 License**. You are free to modify and distribute it under the same license terms.

---

**Developed by [Dtera-dev](https://www.google.com/search?q=https://github.com/Dtera-dev) with a focus on efficiency.**