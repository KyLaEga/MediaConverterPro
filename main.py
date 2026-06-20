import sys

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QFileDialog, QCheckBox,
    QProgressBar, QListWidget, QMessageBox, QComboBox
)
from PySide6.QtGui import QShortcut, QKeySequence, QFontDatabase
from PySide6.QtCore import QThread, Signal

from theme import ThemeManager
from converter import OptimizedMediaConverter
from translations import TRANSLATIONS

class ConversionWorker(QThread):
    progress = Signal(int)
    log = Signal(str)
    done = Signal()  # renamed to avoid shadowing QThread.finished
    error = Signal(str)

    def __init__(self, source_paths, cbz_out, pdf_out, zip_out, make_cbz, make_pdf, make_zip, lang):
        super().__init__()
        self.source_paths = source_paths
        self.cbz_out = cbz_out
        self.pdf_out = pdf_out
        self.zip_out = zip_out
        self.make_cbz = make_cbz
        self.make_pdf = make_pdf
        self.make_zip = make_zip
        self.lang = lang
        self.tr = TRANSLATIONS[lang]
        self.converter = OptimizedMediaConverter()

    def run(self):
        try:
            self.log.emit(self.tr["status_scan"])
            targets = self.converter.find_comics(self.source_paths, cancel_check=self.isInterruptionRequested)

            if not targets:
                self.log.emit(self.tr["status_no_comics"])
                self.done.emit()
                return

            total = len(targets)
            self.log.emit(self.tr["status_found"].format(count=total))

            for i, target in enumerate(targets):
                if self.isInterruptionRequested():
                    break

                temp_dir = None
                try:
                    self.log.emit(self.tr["status_processing"].format(current=i+1, total=total, name=target.name))

                    is_pdf_source = target.is_file() and target.suffix.lower() == '.pdf'
                    # Only a real .cbz is already in target format; a .zip of images
                    # is still worth repackaging into .cbz.
                    is_cbz_source = target.is_file() and target.suffix.lower() == '.cbz'
                    is_zip_source = target.is_file() and target.suffix.lower() == '.zip'

                    needs_cbz = self.make_cbz and self.cbz_out and not is_cbz_source
                    needs_pdf = self.make_pdf and self.pdf_out and not is_pdf_source
                    needs_zip = self.make_zip and self.zip_out and not is_zip_source

                    if not needs_cbz and not needs_pdf and not needs_zip:
                        self.log.emit(self.tr["status_skip_all_same"].format(name=target.name))
                        continue

                    try:
                        images, temp_dir = self.converter.extract_and_prepare(target, cancel_check=self.isInterruptionRequested)
                        if not images:
                            self.log.emit(self.tr["status_skip"].format(name=target.name))
                            continue

                        filename = target.stem if target.is_file() else target.name

                        if needs_cbz:
                            base = temp_dir if temp_dir else target
                            cbz_path = self.converter.to_cbz(images, filename, self.cbz_out, base_dir=base, cancel_check=self.isInterruptionRequested)
                            self.log.emit(self.tr["status_success_cbz"].format(name=cbz_path.name))
                        elif self.make_cbz and self.cbz_out:
                            self.log.emit(self.tr["status_skip_format"].format(fmt="CBZ", name=target.name))

                        if needs_pdf:
                            pdf_path = self.converter.to_pdf(images, filename, self.pdf_out, cancel_check=self.isInterruptionRequested)
                            self.log.emit(self.tr["status_success_pdf"].format(name=pdf_path.name))
                        elif self.make_pdf and self.pdf_out:
                            self.log.emit(self.tr["status_skip_format"].format(fmt="PDF", name=target.name))

                        if needs_zip:
                            base = temp_dir if temp_dir else target
                            zip_path = self.converter.to_zip(images, filename, self.zip_out, base_dir=base, cancel_check=self.isInterruptionRequested)
                            self.log.emit(self.tr["status_success_zip"].format(name=zip_path.name))
                        elif self.make_zip and self.zip_out:
                            self.log.emit(self.tr["status_skip_format"].format(fmt="ZIP", name=target.name))

                    except InterruptedError:
                        self.log.emit(self.tr["status_interrupted"])
                        break
                    except Exception as e:
                        self.log.emit(self.tr["status_error_target"].format(name=target.name, error=str(e)))
                    finally:
                        self.converter.cleanup(temp_dir)
                finally:
                    # Always advance the progress bar, even on skip/error/cancel, so it reaches 100%.
                    self.progress.emit(int(((i + 1) / total) * 100))

            if not self.isInterruptionRequested():
                self.log.emit(self.tr["status_done"])
            self.done.emit()

        except InterruptedError:
            self.log.emit(self.tr["status_interrupted"])
            self.done.emit()
        except Exception as e:
            self.error.emit(str(e))

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.lang = "ru"
        self.is_dark = False  # Start with light theme as requested
        self.tr = TRANSLATIONS[self.lang]
        
        self.setWindowTitle("ComiConv")
        self.setWindowIcon(ThemeManager.make_icon("book", "#5865F2"))
        self.resize(750, 650)
        
        central = QWidget(self)
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Top bar: Header + Lang + Theme
        top_layout = QHBoxLayout()
        self.header = QLabel()
        self.header.setProperty("txt", "h1")
        top_layout.addWidget(self.header)
        
        top_layout.addStretch()
        
        self.combo_lang = QComboBox()
        self.combo_lang.addItems(["RU", "EN"])
        self.combo_lang.currentTextChanged.connect(self._change_lang)
        top_layout.addWidget(self.combo_lang)
        
        self.btn_theme = QPushButton()
        self.btn_theme.setObjectName("secondary")
        self.btn_theme.clicked.connect(self._toggle_theme)
        top_layout.addWidget(self.btn_theme)
        
        self.btn_help = QPushButton()
        self.btn_help.setObjectName("secondary")
        self.btn_help.setIcon(ThemeManager.make_icon("info", ThemeManager.colors()["text"]))
        self.btn_help.clicked.connect(self._show_help)
        top_layout.addWidget(self.btn_help)
        
        layout.addLayout(top_layout)
        
        # Source Selection
        self.source_label = QLabel()
        self.source_label.setProperty("txt", "body")
        layout.addWidget(self.source_label)
        
        self.source_list = QListWidget()
        self.source_list.setFixedHeight(100)
        self.source_list.setSelectionMode(QListWidget.ExtendedSelection)
        self.source_list.itemDoubleClicked.connect(lambda item: self._remove_selected_source())
        QShortcut(QKeySequence("Delete"), self.source_list, self._remove_selected_source)
        QShortcut(QKeySequence("Backspace"), self.source_list, self._remove_selected_source)
        layout.addWidget(self.source_list)
        
        btn_layout = QHBoxLayout()
        self.btn_add_files = QPushButton()
        self.btn_add_files.setObjectName("secondary")
        self.btn_add_folder = QPushButton()
        self.btn_add_folder.setObjectName("secondary")
        self.btn_remove_selected = QPushButton()
        self.btn_remove_selected.setObjectName("secondary")
        self.btn_clear = QPushButton()
        self.btn_clear.setObjectName("secondary")
        
        btn_layout.addWidget(self.btn_add_files)
        btn_layout.addWidget(self.btn_add_folder)
        btn_layout.addWidget(self.btn_remove_selected)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_clear)
        layout.addLayout(btn_layout)
        
        self.btn_add_files.clicked.connect(self._add_files)
        self.btn_add_folder.clicked.connect(self._add_folder)
        self.btn_remove_selected.clicked.connect(self._remove_selected_source)
        self.btn_clear.clicked.connect(self.source_list.clear)
        
        # Checkboxes
        formats_layout = QHBoxLayout()
        self.chk_cbz = QCheckBox()
        self.chk_cbz.setChecked(True)
        self.chk_pdf = QCheckBox()
        self.chk_pdf.setChecked(True)
        self.chk_zip = QCheckBox()
        self.chk_zip.setChecked(False)
        formats_layout.addWidget(self.chk_cbz)
        formats_layout.addWidget(self.chk_pdf)
        formats_layout.addWidget(self.chk_zip)
        formats_layout.addStretch()
        layout.addLayout(formats_layout)

        # Output Folders
        self.cbz_picker, self.cbz_lbl, self.input_cbz, self.btn_cbz_browse = self._create_folder_picker()
        self.pdf_picker, self.pdf_lbl, self.input_pdf, self.btn_pdf_browse = self._create_folder_picker()
        self.zip_picker, self.zip_lbl, self.input_zip, self.btn_zip_browse = self._create_folder_picker()
        layout.addWidget(self.cbz_picker)
        layout.addWidget(self.pdf_picker)
        layout.addWidget(self.zip_picker)
        
        # Start Button
        self.btn_start = QPushButton()
        self.btn_start.setObjectName("primary")
        self.btn_start.setMinimumHeight(ThemeManager.BUTTON_HEIGHT_PRIMARY)
        self.btn_start.clicked.connect(self.on_start_clicked)
        layout.addWidget(self.btn_start)
        
        # Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(8)
        self.progress_bar.setTextVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Log Panel
        self.log_label = QLabel()
        self.log_label.setProperty("txt", "caption")
        layout.addWidget(self.log_label)
        self.log_list = QListWidget()
        layout.addWidget(self.log_list)

        self.chk_cbz.stateChanged.connect(self._toggle_pickers)
        self.chk_pdf.stateChanged.connect(self._toggle_pickers)
        self.chk_zip.stateChanged.connect(self._toggle_pickers)

        self.worker = None
        self._apply_translations()
        self._toggle_pickers()  # sync picker visibility with the checkbox defaults

    def _apply_translations(self):
        self.tr = TRANSLATIONS[self.lang]
        self.setWindowTitle(self.tr["app_title"])
        self.header.setText(self.tr["app_title"])
        self.source_label.setText(self.tr["source_label"])
        self.btn_add_files.setText(self.tr["btn_add_files"])
        self.btn_add_folder.setText(self.tr["btn_add_folder"])
        self.btn_remove_selected.setText(self.tr["btn_remove_selected"])
        self.btn_clear.setText(self.tr["btn_clear"])
        self.chk_cbz.setText(self.tr["chk_cbz"])
        self.chk_pdf.setText(self.tr["chk_pdf"])
        self.chk_zip.setText(self.tr["chk_zip"])
        self.cbz_lbl.setText(self.tr["cbz_out_label"])
        self.pdf_lbl.setText(self.tr["pdf_out_label"])
        self.zip_lbl.setText(self.tr["zip_out_label"])
        self.input_cbz.setPlaceholderText(self.tr["placeholder_folder"])
        self.input_pdf.setPlaceholderText(self.tr["placeholder_folder"])
        self.input_zip.setPlaceholderText(self.tr["placeholder_folder"])
        if self.worker is not None and self.worker.isRunning():
            self.btn_start.setText(self.tr["btn_cancel"])
        else:
            self.btn_start.setText(self.tr["btn_start"])
        self.log_label.setText(self.tr["log_label"])
        self.btn_theme.setText(self.tr["theme_toggle"])
        self.btn_help.setText(self.tr["btn_help"])

    def _change_lang(self, lang_code):
        self.lang = lang_code.lower()
        self._apply_translations()

    def _toggle_theme(self):
        self.is_dark = not self.is_dark
        if self.is_dark:
            ThemeManager.apply_modern_dark(QApplication.instance())
        else:
            ThemeManager.apply_modern_light(QApplication.instance())
            
        # Re-apply icons with new text color
        color = ThemeManager.colors()["text"]
        self.btn_cbz_browse.setIcon(ThemeManager.make_icon("folder", color))
        self.btn_pdf_browse.setIcon(ThemeManager.make_icon("folder", color))
        self.btn_help.setIcon(ThemeManager.make_icon("info", color))

    def _show_help(self):
        msg = QMessageBox(self)
        msg.setWindowTitle(self.tr["help_title"])
        msg.setText(self.tr["help_text"])
        msg.setIcon(QMessageBox.Information)
        msg.exec()

    def _add_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, self.tr["dlg_select_archives"], "", "Comics (*.zip *.cbz *.pdf)"
        )
        if files:
            for f in files:
                self._add_unique_source(f)
                
    def _add_folder(self):
        folder = QFileDialog.getExistingDirectory(self, self.tr["dlg_select_folder"])
        if folder:
            self._add_unique_source(folder)
            
    def _add_unique_source(self, path):
        for i in range(self.source_list.count()):
            if self.source_list.item(i).text() == path:
                return
        self.source_list.addItem(path)

    def _remove_selected_source(self):
        for item in self.source_list.selectedItems():
            self.source_list.takeItem(self.source_list.row(item))

    def _create_folder_picker(self):
        widget = QWidget()
        lay = QVBoxLayout(widget)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(5)
        
        lbl = QLabel()
        lbl.setProperty("txt", "body")
        lay.addWidget(lbl)
        
        row = QHBoxLayout()
        input_field = QLineEdit()
        input_field.setReadOnly(True)
        
        btn_browse = QPushButton()
        btn_browse.setIcon(ThemeManager.make_icon("folder", ThemeManager.colors()["text"]))
        btn_browse.setFixedSize(ThemeManager.BUTTON_HEIGHT_ICON, ThemeManager.BUTTON_HEIGHT_ICON)
        btn_browse.setObjectName("secondary")
        
        row.addWidget(input_field)
        row.addWidget(btn_browse)
        lay.addLayout(row)
        
        btn_browse.clicked.connect(lambda: self._browse_folder(input_field))
        
        return widget, lbl, input_field, btn_browse

    def _browse_folder(self, line_edit):
        folder = QFileDialog.getExistingDirectory(self, self.tr["dlg_select_out_folder"])
        if folder:
            line_edit.setText(folder)

    def _toggle_pickers(self):
        self.cbz_picker.setVisible(self.chk_cbz.isChecked())
        self.pdf_picker.setVisible(self.chk_pdf.isChecked())
        self.zip_picker.setVisible(self.chk_zip.isChecked())
        # While a conversion runs the button acts as "Cancel" — never disable it here,
        # otherwise unchecking every format would make the run impossible to cancel.
        if self.worker is None or not self.worker.isRunning():
            self.btn_start.setEnabled(
                self.chk_cbz.isChecked() or self.chk_pdf.isChecked() or self.chk_zip.isChecked()
            )

    def append_log(self, text):
        self.log_list.addItem(text)
        # Cap the log so very large batches don't grow memory without bound.
        while self.log_list.count() > 1000:
            self.log_list.takeItem(0)
        self.log_list.scrollToBottom()

    def on_start_clicked(self):
        if self.worker is not None and self.worker.isRunning():
            self.btn_start.setEnabled(False)
            self.append_log(self.tr["status_interrupting"])
            self.worker.requestInterruption()
        else:
            self.start_conversion()

    def start_conversion(self):
        source_paths = [self.source_list.item(i).text() for i in range(self.source_list.count())]
        cbz_out = self.input_cbz.text()
        pdf_out = self.input_pdf.text()
        zip_out = self.input_zip.text()

        make_cbz = self.chk_cbz.isChecked()
        make_pdf = self.chk_pdf.isChecked()
        make_zip = self.chk_zip.isChecked()

        if not source_paths:
            QMessageBox.warning(self, self.tr["msg_error"], self.tr["msg_select_source"])
            return

        if make_cbz and not cbz_out:
            QMessageBox.warning(self, self.tr["msg_error"], self.tr["msg_select_cbz"])
            return

        if make_pdf and not pdf_out:
            QMessageBox.warning(self, self.tr["msg_error"], self.tr["msg_select_pdf"])
            return

        if make_zip and not zip_out:
            QMessageBox.warning(self, self.tr["msg_error"], self.tr["msg_select_zip"])
            return

        self.btn_start.setText(self.tr["btn_cancel"])
        self.btn_start.setObjectName("secondary")
        self.btn_start.style().unpolish(self.btn_start)
        self.btn_start.style().polish(self.btn_start)
        
        self.progress_bar.setValue(0)
        self.log_list.clear()

        self.worker = ConversionWorker(source_paths, cbz_out, pdf_out, zip_out, make_cbz, make_pdf, make_zip, self.lang)
        self.worker.log.connect(self.append_log)
        self.worker.progress.connect(self.progress_bar.setValue)
        self.worker.error.connect(self.handle_error)
        self.worker.done.connect(self.conversion_finished)
        self.worker.start()

    def _reset_start_button(self):
        self.btn_start.setText(self.tr["btn_start"])
        self.btn_start.setObjectName("primary")
        # Re-enable according to the selected formats (avoid isRunning() race here).
        self.btn_start.setEnabled(
            self.chk_cbz.isChecked() or self.chk_pdf.isChecked() or self.chk_zip.isChecked()
        )
        self.btn_start.style().unpolish(self.btn_start)
        self.btn_start.style().polish(self.btn_start)

    def handle_error(self, msg):
        self.append_log(f"{self.tr['msg_critical']} {msg}")
        QMessageBox.critical(self, self.tr["msg_error"], f"{self.tr['msg_critical']}\n{msg}")
        self._reset_start_button()

    def conversion_finished(self):
        self._reset_start_button()

    def closeEvent(self, event):
        # Stop the worker gracefully so the QThread is not destroyed while running.
        if self.worker is not None and self.worker.isRunning():
            self.worker.requestInterruption()
            self.worker.quit()
            if not self.worker.wait(5000):
                self.worker.terminate()
                self.worker.wait()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Use "Outfit" only if it is actually available; otherwise keep the system default.
    if "Outfit" in QFontDatabase.families():
        font = app.font()
        font.setFamily("Outfit")
        app.setFont(font)
    
    ThemeManager.apply_modern_light(app)
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
