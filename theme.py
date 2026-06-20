from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPalette, QColor, QIcon, QPixmap
from PySide6.QtCore import QByteArray
from PySide6 import QtSvg  # noqa: F401  (registers the SVG image handler for make_icon)

class ThemeManager:
    DARK = {
        "bg": "#1E1F22",
        "surface": "#2B2D31",
        "text": "#DBDEE1",
        "border": "#4E5058",
    }
    LIGHT = {
        "bg": "#F2F3F5",
        "surface": "#FFFFFF",
        "text": "#313338",
        "border": "#E3E5E8",
    }

    FONT_CAPTION = 11
    FONT_BASE = 13
    FONT_H1 = 20

    BUTTON_HEIGHT_PRIMARY = 40
    BUTTON_HEIGHT_ICON = 40

    ICON_GLYPHS = {
        "folder": "M10 4H4c-1.1 0-1.99.9-1.99 2L2 18c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2h-8l-2-2z",
        "book": "M18 2H6c-1.1 0-2 .9-2 2v16c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zM6 4h5v8l-2.5-1.5L6 12V4z",
        "info": "M11 7h2v2h-2zm0 4h2v6h-2zm1-9C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8z"
    }

    @classmethod
    def make_icon(cls, glyph_name: str, color: str) -> QIcon:
        path_d = cls.ICON_GLYPHS.get(glyph_name)
        if not path_d:
            print(f"ThemeManager: unknown icon glyph '{glyph_name}'")
            return QIcon()
        svg = (
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" '
            f'width="48" height="48"><path fill="{color}" d="{path_d}"/></svg>'
        )
        pixmap = QPixmap()
        pixmap.loadFromData(QByteArray(svg.encode("utf-8")), "SVG")
        return QIcon(pixmap)

    _active = DARK

    @classmethod
    def colors(cls) -> dict:
        return cls._active

    @classmethod
    def _typography_qss(cls) -> str:
        return (
            f'QLabel[txt="h1"] {{ font-size: {cls.FONT_H1}px; font-weight: bold; }}'
            f'QLabel[txt="body"] {{ font-size: {cls.FONT_BASE}px; }}'
            f'QLabel[txt="caption"] {{ font-size: {cls.FONT_CAPTION}px; }}'
        )

    @classmethod
    def apply_modern_dark(cls, app: QApplication):
        cls._active = cls.DARK
        app.setStyle("Fusion")
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(cls.DARK["bg"]))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(cls.DARK["text"]))
        palette.setColor(QPalette.ColorRole.Base, QColor(cls.DARK["surface"]))
        palette.setColor(QPalette.ColorRole.Text, QColor(cls.DARK["text"]))
        palette.setColor(QPalette.ColorRole.Button, QColor(64, 66, 73))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(cls.DARK["text"]))
        app.setPalette(palette)

        qss = """
        QMainWindow { background-color: #1E1F22; }

        QPushButton {
            background-color: #404249; color: #DBDEE1;
            border: none; border-radius: 6px;
            padding: 5px 12px; font-weight: 500;
        }
        QPushButton:hover { background-color: #4E5058; }
        QPushButton:pressed { background-color: #313338; }
        QPushButton:disabled { background-color: #313338; color: #5C5E66; }

        QPushButton#primary { background-color: #23A559; color: white; font-weight: bold; }
        QPushButton#primary:hover { background-color: #1D8A4A; }

        QPushButton#secondary {
            background-color: transparent;
            border: 1px solid #4E5058;
            border-radius: 6px;
            padding: 4px 10px;
            color: #DBDEE1;
        }
        QPushButton#secondary:hover { background-color: #3F4147; border: 1px solid #5865F2; }

        QLineEdit {
            background-color: #1E1F22; color: #FFFFFF;
            border: 1px solid #4E5058; border-radius: 6px;
            padding: 6px 10px; selection-background-color: #5865F2;
        }
        QLineEdit:focus { border: 1px solid #5865F2; }

        QCheckBox { spacing: 8px; color: #DBDEE1; font-weight: 500; }
        QCheckBox::indicator { width: 18px; height: 18px; border-radius: 4px; border: 2px solid #5865F2; background: transparent; }
        QCheckBox::indicator:checked { background: #5865F2; border: 2px solid #5865F2; image: url(none); }
        QCheckBox::indicator:checked:pressed { background: #4752C4; border-color: #4752C4; }

        QLabel { color: #DBDEE1; }

        QProgressBar { border: none; background-color: #1E1F22; border-radius: 4px; text-align: center; color: white; font-weight: bold; }
        QProgressBar::chunk { background-color: #5865F2; border-radius: 4px; }

        QListWidget { background-color: #1E1F22; border: 1px solid #4E5058; border-radius: 6px; color: #DBDEE1; outline: none; padding: 4px; }
        QListWidget::item { padding: 6px; border-radius: 4px; }
        QListWidget::item:selected { background-color: #3F4147; color: white; }

        QComboBox { background-color: #1E1F22; color: #FFFFFF; border: 1px solid #4E5058; border-radius: 6px; padding: 4px 10px; }
        QComboBox:hover { border: 1px solid #5865F2; }
        QComboBox::drop-down { border: none; width: 20px; }
        QComboBox QAbstractItemView { background-color: #1E1F22; color: #FFFFFF; border: 1px solid #4E5058; border-radius: 6px; selection-background-color: #3F4147; outline: none; }
        """
        app.setStyleSheet(qss + cls._typography_qss())

    @classmethod
    def apply_modern_light(cls, app: QApplication):
        cls._active = cls.LIGHT
        app.setStyle("Fusion")
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(cls.LIGHT["bg"]))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(cls.LIGHT["text"]))
        palette.setColor(QPalette.ColorRole.Base, QColor(cls.LIGHT["surface"]))
        palette.setColor(QPalette.ColorRole.Text, QColor(cls.LIGHT["text"]))
        palette.setColor(QPalette.ColorRole.Button, QColor(cls.LIGHT["border"]))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(cls.LIGHT["text"]))
        app.setPalette(palette)

        qss = """
        QMainWindow { background-color: #F2F3F5; }

        QPushButton { background-color: #E3E5E8; color: #313338; border: none; border-radius: 6px; padding: 4px 10px; font-weight: 500; }
        QPushButton:hover { background-color: #D4D7DC; }
        QPushButton:pressed { background-color: #B5BAC1; }
        QPushButton:disabled { background-color: #E3E5E8; color: #949BA4; }

        QPushButton#primary { background-color: #23A559; color: white; font-weight: bold; }
        QPushButton#primary:hover { background-color: #1D8A4A; }

        QPushButton#secondary {
            background-color: transparent;
            border: 1px solid #D4D7DC;
            border-radius: 6px;
            padding: 4px 10px;
            color: #313338;
        }
        QPushButton#secondary:hover { background-color: #E3E5E8; border: 1px solid #5865F2; }

        QLineEdit {
            background-color: #FFFFFF; color: #313338;
            border: 1px solid #D4D7DC; border-radius: 6px;
            padding: 6px 10px; selection-background-color: #5865F2; selection-color: white;
        }
        QLineEdit:focus { border: 1px solid #5865F2; }

        QCheckBox { spacing: 8px; color: #313338; font-weight: 500; }
        QCheckBox::indicator { width: 18px; height: 18px; border-radius: 4px; border: 2px solid #5865F2; background: transparent; }
        QCheckBox::indicator:checked { background: #5865F2; border: 2px solid #5865F2; image: url(none); }
        QCheckBox::indicator:checked:pressed { background: #4752C4; border-color: #4752C4; }

        QLabel { color: #313338; }

        QProgressBar { border: none; background-color: #E3E5E8; border-radius: 4px; text-align: center; color: #313338; font-weight: bold; }
        QProgressBar::chunk { background-color: #5865F2; border-radius: 4px; }

        QListWidget { background-color: #FFFFFF; border: 1px solid #E3E5E8; border-radius: 6px; color: #313338; outline: none; padding: 4px; }
        QListWidget::item { padding: 6px; border-radius: 4px; }
        QListWidget::item:selected { background-color: #E3E5E8; color: #000000; }

        QComboBox { background-color: #FFFFFF; color: #313338; border: 1px solid #D4D7DC; border-radius: 6px; padding: 4px 10px; }
        QComboBox:hover { border: 1px solid #5865F2; }
        QComboBox::drop-down { border: none; width: 20px; }
        QComboBox QAbstractItemView { background-color: #FFFFFF; color: #313338; border: 1px solid #D4D7DC; border-radius: 6px; selection-background-color: #E3E5E8; selection-color: #000000; outline: none; }
        """
        app.setStyleSheet(qss + cls._typography_qss())
