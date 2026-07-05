"""
Smart Import Window
Phase 10A - Smart Portfolio Import Engine

Purpose:
- Select CSV / Excel / PDF / Image file
- Read portfolio rows using smart_import_service
- Show preview dialog before import
- Import selected rows into PSX portfolio

Important:
- Direct import without preview is not allowed.
- Existing holdings can be updated or skipped.
"""

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFileDialog,
    QMessageBox,
    QTextEdit,
    QFrame,
    QCheckBox,
    QGroupBox,
)

from services.settings_service import load_settings
from services.smart_import_service import (
    read_portfolio_file,
    get_import_summary,
    SUPPORTED_EXTENSIONS,
)

from services.portfolio_service import (
    get_all_holdings,
    add_new_holding,
    update_existing_holding,
)

from smart_import_preview_dialog import SmartImportPreviewDialog


class SmartImportWindow(QWidget):
    """
    Smart Portfolio Import window.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.settings = load_settings()
        self.selected_file = ""
        self.import_result = None
        self.preview_rows = []

        self.setWindowTitle("Smart Portfolio Import")
        self.resize(950, 650)

        self.init_ui()
        self.apply_theme()

    def init_ui(self):

        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        self.heading = QLabel("📥 Smart Portfolio Import")
        self.heading.setAlignment(Qt.AlignCenter)

        description = QLabel(
            "Import PSX portfolio from CSV, Excel, text PDF, or screenshot. "
            "Data will be shown in preview before updating portfolio."
        )
        description.setWordWrap(True)
        description.setAlignment(Qt.AlignCenter)
        description.setStyleSheet("""
            font-size:13px;
            padding:6px;
        """)

        file_group = self.create_file_group()
        options_group = self.create_options_group()
        button_layout = self.create_buttons()

        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)
        self.log_box.setMinimumHeight(220)

        note = QLabel(
            "Recommended format: CSV or Excel with columns like Symbol, Shares, "
            "Avg Price, Current Price. PDF/Image extraction may need manual review."
        )
        note.setWordWrap(True)
        note.setStyleSheet("""
            font-size:12px;
            color:#555555;
            padding:5px;
        """)

        main_layout.addWidget(self.heading)
        main_layout.addWidget(description)
        main_layout.addWidget(file_group)
        main_layout.addWidget(options_group)
        main_layout.addLayout(button_layout)
        main_layout.addWidget(QLabel("Import Log:"))
        main_layout.addWidget(self.log_box)
        main_layout.addWidget(note)

        self.write_log("Smart Import ready.")
        self.write_log("Supported files: " + ", ".join(SUPPORTED_EXTENSIONS))

    def create_file_group(self):

        group = QGroupBox("Select Portfolio File")
        layout = QHBoxLayout()
        group.setLayout(layout)

        self.file_label = QLabel("No file selected")
        self.file_label.setWordWrap(True)
        self.file_label.setMinimumHeight(40)
        self.file_label.setFrameShape(QFrame.StyledPanel)
        self.file_label.setStyleSheet("""
            padding:8px;
            border:1px solid #cccccc;
            border-radius:5px;
        """)

        browse_btn = QPushButton("Browse File")
        browse_btn.setMinimumHeight(40)
        browse_btn.clicked.connect(self.browse_file)

        layout.addWidget(self.file_label)
        layout.addWidget(browse_btn)

        return group

    def create_options_group(self):

        group = QGroupBox("Import Options")
        layout = QVBoxLayout()
        group.setLayout(layout)

        self.update_existing_checkbox = QCheckBox(
            "Update existing holdings if symbol already exists"
        )
        self.update_existing_checkbox.setChecked(True)

        self.skip_low_confidence_checkbox = QCheckBox(
            "Auto-uncheck low confidence rows in preview"
        )
        self.skip_low_confidence_checkbox.setChecked(True)

        self.refresh_prices_note = QLabel(
            "Note: Import will use prices from selected file. "
            "Live/current price update will be handled later in Live Update Engine."
        )
        self.refresh_prices_note.setWordWrap(True)
        self.refresh_prices_note.setStyleSheet("""
            font-size:12px;
            color:#555555;
        """)

        layout.addWidget(self.update_existing_checkbox)
        layout.addWidget(self.skip_low_confidence_checkbox)
        layout.addWidget(self.refresh_prices_note)

        return group

    def create_buttons(self):

        layout = QHBoxLayout()

        self.read_btn = QPushButton("🔍 Read File")
        self.preview_btn = QPushButton("👁 Preview & Import")
        self.clear_btn = QPushButton("🧹 Clear")
        self.close_btn = QPushButton("❌ Close")

        buttons = [
            self.read_btn,
            self.preview_btn,
            self.clear_btn,
            self.close_btn,
        ]

        for button in buttons:
            button.setMinimumHeight(40)
            layout.addWidget(button)

        self.preview_btn.setEnabled(False)

        self.read_btn.clicked.connect(self.read_selected_file)
        self.preview_btn.clicked.connect(self.open_preview_dialog)
        self.clear_btn.clicked.connect(self.clear_import)
        self.close_btn.clicked.connect(self.close)

        return layout

    def browse_file(self):

        file_filter = (
            "Portfolio Files (*.csv *.xlsx *.xlsm *.pdf *.png *.jpg *.jpeg);;"
            "CSV Files (*.csv);;"
            "Excel Files (*.xlsx *.xlsm);;"
            "PDF Files (*.pdf);;"
            "Images (*.png *.jpg *.jpeg);;"
            "All Files (*.*)"
        )

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Portfolio File",
            "",
            file_filter
        )

        if not file_path:
            return

        self.selected_file = file_path
        self.file_label.setText(file_path)
        self.preview_btn.setEnabled(False)
        self.preview_rows = []
        self.import_result = None

        self.write_log(f"Selected file: {file_path}")

    def read_selected_file(self):

        if not self.selected_file:
            QMessageBox.warning(
                self,
                "No File Selected",
                "Please select a portfolio file first."
            )
            return

        try:
            self.write_log("Reading selected file...")

            self.import_result = read_portfolio_file(self.selected_file)

            errors = self.import_result.get("errors", [])
            warnings = self.import_result.get("warnings", [])

            for error in errors:
                self.write_log(f"ERROR: {error}")

            for warning in warnings:
                self.write_log(f"WARNING: {warning}")

            self.preview_rows = self.import_result.get("rows", [])

            if not self.preview_rows:
                self.preview_btn.setEnabled(False)

                QMessageBox.warning(
                    self,
                    "No Rows Detected",
                    "No valid portfolio rows were detected.\n\n"
                    "Please check file format or try CSV/Excel."
                )
                return

            summary = get_import_summary(self.preview_rows)

            self.write_log(f"Rows detected: {summary['total_rows']}")
            self.write_log(
                f"Investment value: PKR {summary['total_investment']:,.2f}"
            )
            self.write_log(
                f"Current value: PKR {summary['total_current']:,.2f}"
            )
            self.write_log(
                f"Estimated P/L: PKR {summary['estimated_profit']:,.2f}"
            )

            if summary["low_confidence_rows"] > 0:
                self.write_log(
                    f"Low confidence rows: {summary['low_confidence_rows']}"
                )

            self.preview_btn.setEnabled(True)

            QMessageBox.information(
                self,
                "File Read Successfully",
                f"{summary['total_rows']} portfolio rows detected.\n\n"
                "Please click Preview & Import to review rows."
            )

        except Exception as e:

            self.preview_btn.setEnabled(False)

            self.write_log(f"ERROR: {str(e)}")

            QMessageBox.critical(
                self,
                "Read File Error",
                str(e)
            )

    def open_preview_dialog(self):

        if not self.preview_rows:
            QMessageBox.warning(
                self,
                "No Preview Rows",
                "Please read a valid portfolio file first."
            )
            return

        dialog = SmartImportPreviewDialog(
            parent=self,
            rows=self.preview_rows,
            file_path=self.selected_file,
        )

        if self.skip_low_confidence_checkbox.isChecked():
            dialog.uncheck_invalid_rows()

        if dialog.exec():

            try:
                selected_rows = dialog.get_data()

                if not selected_rows:
                    QMessageBox.warning(
                        self,
                        "No Rows Selected",
                        "No rows were selected for import."
                    )
                    return

                result = self.import_rows_to_portfolio(selected_rows)

                message = (
                    "Smart import completed.\n\n"
                    f"Added: {result['added']}\n"
                    f"Updated: {result['updated']}\n"
                    f"Skipped: {result['skipped']}\n"
                    f"Errors: {result['errors']}"
                )

                self.write_log(message.replace("\n", " | "))

                QMessageBox.information(
                    self,
                    "Import Completed",
                    message
                )

                self.preview_btn.setEnabled(False)

            except Exception as e:

                self.write_log(f"IMPORT ERROR: {str(e)}")

                QMessageBox.critical(
                    self,
                    "Import Error",
                    str(e)
                )

    def import_rows_to_portfolio(self, rows):

        existing_holdings = get_all_holdings()
        existing_by_symbol = {}

        for holding in existing_holdings:

            symbol = str(holding.get("symbol", "")).strip().upper()

            if symbol:
                existing_by_symbol[symbol] = holding

        result = {
            "added": 0,
            "updated": 0,
            "skipped": 0,
            "errors": 0,
        }

        update_existing = self.update_existing_checkbox.isChecked()

        for row in rows:

            try:
                symbol = str(row["symbol"]).strip().upper()
                shares = float(row["shares"])
                avg_price = float(row["avg_price"])
                current_price = float(row["current_price"])

                if not symbol or shares <= 0:
                    result["skipped"] += 1
                    continue

                if symbol in existing_by_symbol:

                    if update_existing:
                        update_existing_holding(
                            symbol,
                            shares,
                            avg_price,
                            current_price
                        )
                        result["updated"] += 1
                    else:
                        result["skipped"] += 1

                else:
                    add_new_holding(
                        symbol,
                        shares,
                        avg_price,
                        current_price
                    )
                    result["added"] += 1

            except Exception as e:
                result["errors"] += 1
                self.write_log(
                    f"Row import error for {row.get('symbol', '')}: {str(e)}"
                )

        return result

    def clear_import(self):

        self.selected_file = ""
        self.import_result = None
        self.preview_rows = []
        self.file_label.setText("No file selected")
        self.preview_btn.setEnabled(False)
        self.log_box.clear()
        self.write_log("Smart Import cleared.")

    def write_log(self, message):

        self.log_box.append(str(message))

    def apply_theme(self):

        theme = str(
            self.settings.get("theme", "light")
        ).strip().lower()

        if theme == "dark":

            self.setStyleSheet("""
                QWidget {
                    background-color:#1e1e1e;
                    color:#ffffff;
                }

                QLabel {
                    color:#ffffff;
                }

                QGroupBox {
                    border:1px solid #555555;
                    border-radius:6px;
                    margin-top:10px;
                    padding:10px;
                    font-weight:bold;
                    color:#ffffff;
                }

                QGroupBox::title {
                    subcontrol-origin: margin;
                    left:10px;
                    padding:0 5px 0 5px;
                }

                QPushButton {
                    background-color:#2d2d30;
                    color:#ffffff;
                    border:1px solid #555555;
                    border-radius:5px;
                    padding:6px;
                }

                QPushButton:hover {
                    background-color:#3e3e42;
                }

                QTextEdit {
                    background-color:#252526;
                    color:#ffffff;
                    border:1px solid #555555;
                    border-radius:5px;
                }

                QCheckBox {
                    color:#ffffff;
                    font-size:13px;
                }
            """)

            self.heading.setStyleSheet("""
                font-size:24px;
                font-weight:bold;
                padding:10px;
                color:#ffffff;
            """)

        else:

            self.setStyleSheet("""
                QWidget {
                    background-color:#ffffff;
                    color:#000000;
                }

                QLabel {
                    color:#000000;
                }

                QGroupBox {
                    border:1px solid #cccccc;
                    border-radius:6px;
                    margin-top:10px;
                    padding:10px;
                    font-weight:bold;
                    color:#000000;
                }

                QGroupBox::title {
                    subcontrol-origin: margin;
                    left:10px;
                    padding:0 5px 0 5px;
                }

                QPushButton {
                    background-color:#f5f5f5;
                    color:#000000;
                    border:1px solid #cccccc;
                    border-radius:5px;
                    padding:6px;
                }

                QPushButton:hover {
                    background-color:#e8e8e8;
                }

                QTextEdit {
                    background-color:#ffffff;
                    color:#000000;
                    border:1px solid #cccccc;
                    border-radius:5px;
                }

                QCheckBox {
                    color:#000000;
                    font-size:13px;
                }
            """)

            self.heading.setStyleSheet("""
                font-size:24px;
                font-weight:bold;
                padding:10px;
                color:#000000;
            """)
