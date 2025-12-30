# 📋 Clip Vault

![Platform](https://img.shields.io/badge/Platform-Linux-blue)
![Python](https://img.shields.io/badge/Python-3.10%2B-yellow)
![License](https://img.shields.io/badge/License-GPLv3-green)

**Clip Vault** is a modern, lightweight, and secure clipboard manager designed for power users. It runs quietly in the background and ensures you never lose a copied text again. Built with a focus on speed, aesthetics, and robust text rendering for all languages.

---

## ✨ Key Features

* **⚡ Lightning Fast Access:** Toggle the UI instantly from anywhere using `Ctrl + Space`.
* **🔍 Smart Search:** Quickly filter through your history. Supports complex scripts and bi-directional text (RTL/LTR) without graphical glitches.
* **🛡️ Secure Database:** All clips are stored locally in an encrypted-ready SQLite database. Your data never leaves your machine.
* **🎨 Modern Dark UI:** A beautiful, eye-friendly interface built with CustomTkinter.
* **👻 Background Mode:** Minimizes to the System Tray to keep your workspace clean.
* **🚀 Auto-Start Ready:** Includes built-in scripts to launch automatically on system startup.

---

## 📥 Installation

### Option 1: Download Binary (Recommended)
Go to the **[Releases](https://github.com/Dtera-dev/ClipVault/releases)** page and download the latest version for Linux.
1. Download the file.
2. Grant execution permission (`chmod +x ClipVault`).
3. Run it!

### Option 2: Build from Source
If you are a developer, you can clone and run it manually:

```bash
# 1. Clone the repository
git clone [https://github.com/Dtera-dev/ClipVault.git](https://github.com/Dtera-dev/ClipVault.git)
cd ClipVault

# 2. Set up environment
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Run
python main.py

```

---

## ⌨️ How to Use

| Action | Shortcut / Input |
| --- | --- |
| **Toggle Window** | `Ctrl` + `Space` |
| **Copy Clip** | Click on any item in the list |
| **Delete Clip** | Right-click on the item |
| **Switch Language** | Click the **EN/FA** button (Optimizes search direction) |
| **Quit App** | Right-click the Tray Icon > Quit |

---

## 🛠️ Technology Stack

* **Core:** Python 3
* **GUI:** CustomTkinter (Modern Tkinter wrapper)
* **Database:** SQLite3
* **Input Handling:** Pynput (Global Hotkeys)
* **System Integration:** Pystray (System Tray)

---

## 🤝 Contributing

Contributions are what make the open-source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License

Distributed under the **GNU GPLv3 License**. See `LICENSE` for more information.

---

<p align="center">
Made with ❤️ by <a href="https://www.google.com/search?q=https://github.com/Dtera-dev">Dtera-dev</a>
</p>