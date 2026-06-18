# Media Converter Pro 📚🔄
[![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/KyLaEga/MediaConverterPro/build.yml?branch=main&label=Build&logo=github)](https://github.com/KyLaEga/MediaConverterPro/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Media Converter Pro** is a powerful, cross-platform desktop application designed for the automated batch conversion of comics and images into **CBZ** and **PDF** formats.

Built with a modern UI (PySide6), it supports recursive processing of a huge number of files without requiring manual confirmations.

---

## 🎨 Features
- **Batch Processing**: Load dozens of archives (`.zip`, `.cbz`) or image folders — the program will automatically queue and convert them.
- **Multi-Selection Support**: You can select specific archives as well as entire directories for recursive scanning.
- **Bilingual Interface**: Full support for English and Russian (switching on the fly).
- **Light & Dark Themes**: An elegant `ThemeManager` design system that adapts to your preferences.
- **Multithreading**: The GUI never freezes, thanks to heavy logic processing in background threads (`QThread`).
- **Separate Output Paths**: Specify different directories for generating CBZ and PDF files. Uncheck a format if you don't need it.

---

## 🚀 Installation and Usage (For Developers)
If you want to run the project locally via Python:

1. Clone the repository:
   ```bash
   git clone https://github.com/KyLaEga/MediaConverterPro.git
   cd MediaConverterPro
   ```

2. Run the startup script (it will automatically install the required dependencies from `requirements.txt` and launch the app):
   ```bash
   ./start.sh
   ```

---

## 📦 Download Ready-to-Use Application
We use **GitHub Actions** to automatically compile the project into native, ready-to-use applications (no Python installation required).

You can download the latest built files in the **[Actions -> Build & Release](https://github.com/KyLaEga/MediaConverterPro/actions)** tab or in the **Releases** section.
- 🍎 **macOS**: `MediaConverterPro-macOS.zip` (extract and run the `.app`)
- 🪟 **Windows**: `MediaConverterPro-Windows.exe`
- 🐧 **Linux**: `MediaConverterPro-Linux` (executable binary)

---

## 🛠 Technologies
- **Language**: Python 3.9+
- **Interface**: PySide6 (Qt)
- **Image Processing**: Pillow (PIL)
- **Build Tools**: PyInstaller + GitHub Actions
