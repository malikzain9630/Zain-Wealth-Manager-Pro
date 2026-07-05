"""
Fund Statement Preview Dialog
Phase 10A - Smart Mutual Fund / MTPF Statement Import

Purpose:
- Preview extracted Al Meezan Mutual Fund / MTPF statement rows.
- Allow user to select/unselect rows before import.
- Allow basic correction of Units, NAV, Investment Value and remarks.
- Return only selected rows.

This dialog does not directly update the database.
"""

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QMessageBox,
    QFrame,
    QCheckBox,
    QAbstractItemView,
)
from PySide6.QtCore import Qt

try:
    from services.currency_service import format_currency as format_display_currency
except Exception:
    def format_display_currency(value, *args, **kwargs):
        try:
            return f"PKR {float(value):,.2f}"
        except Exception:
            return "PKR 0.00"

try:
    from services.settings_service import load_settings
except Exception:
    def load_settings():
        return {"theme": "Light"}


class FundStatementPreviewDialog(QDialog):
    """
    Preview extracted Mutual Fund / MTPF statement rows.
    """

    def __init__(self, rows=None, summary=None, parent=None):
        super().__init__(parent)

        self.rows = rows or []
        self.summary = summary or {}
        self.settings = load_settings()
        self.theme = self.settings.get("theme", "Light")

        self.setWindowTitle("Smart Fund Statement Preview")
        self.resize(1350, 720)

        self.table = None
        self.select_all_checkbox = None
        self.summary_labels = {}

        self.setup_ui()
        self.apply_theme()
        self.load_rows()

    def setup_ui(self):
        """
        Build UI.
        """

        main_layout = QVBoxLayout(self)

        title = QLabel("🧾 Smart Mutual Fund / MTPF Statement Preview")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 20px; font-weight: bold; padding: 10px;")
        main_layout.addWidget(title)

        note = QLabel(
            "Review extracted Al Meezan Mutual Fund / MTPF rows before import. "
            "Only checked rows will be imported/updated."
        )
        note.setAlignment(Qt.AlignCenter)
        note.setWordWrap(True)
        main_layout.addWidget(note)

        self.create_summary_cards(main_layout)
        self.create_controls(main_layout)
        self.create_table(main_layout)
        self.create_buttons(main_layout)

    def create_summary_cards(self, parent_layout):
        """
        Create summary cards.
        """

        cards_layout = QHBoxLayout()

        card_data = [
            ("total_rows", "Total Rows", self.summary.get("total_rows", len(self.rows))),
            ("suggested_rows", "Suggested Import", self.summary.get("suggested_rows", 0)),
            ("mutual_fund_rows", "Mutual Fund Rows", self.summary.get("mutual_fund_rows", 0)),
            ("pension_rows", "Pension / MTPF Rows", self.summary.get("pension_rows", 0)),
            ("total_value", "Total Value", format_display_currency(self.summary.get("total_value", 0))),
            ("total_gain_loss", "Total Gain/Loss", format_display_currency(self.summary.get("total_gain_loss", 0))),
        ]

        for key, title, value in card_data:
            card = self.make_card(title, value)
            self.summary_labels[key] = card.findChild(QLabel, "value_label")
            cards_layout.addWidget(card)

        parent_layout.addLayout(cards_layout)

    def make_card(self, title, value):
        """
        Create one summary card.
        """

        frame = QFrame()
        frame.setObjectName("summary_card")
        frame.setFrameShape(QFrame.StyledPanel)
        frame.setMinimumHeight(85)

        layout = QVBoxLayout(frame)

        title_label = QLabel(str(title))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-weight: bold;")

        value_label = QLabel(str(value))
        value_label.setObjectName("value_label")
        value_label.setAlignment(Qt.AlignCenter)
        value_label.setStyleSheet("font-size: 15px; font-weight: bold;")

        layout.addWidget(title_label)
        layout.addWidget(value_label)

        return frame

    def create_controls(self, parent_layout):
        """
        Create selection controls.
        """

        controls_layout = QHBoxLayout()

        self.select_all_checkbox = QCheckBox("Select All Suggested Rows")
        self.select_all_checkbox.setChecked(True)
        self.select_all_checkbox.stateChanged.connect(self.toggle_all_rows)

        controls_layout.addWidget(self.select_all_checkbox)
        controls_layout.addStretch()

        parent_layout.addLayout(controls_layout)

    def create_table(self, parent_layout):
        """
        Create preview table.
        """

        self.table = QTableWidget()
        self.table.setColumnCount(13)

        self.table.setHorizontalHeaderLabels([
            "Import?",
            "Category",
            "Fund Code",
            "Fund Name",
            "Unit Type",
            "Units",
            "NAV",
            "Investment Value",
            "FYTD Gain/Loss",
            "Total Gain/Loss",
            "Confidence",
            "Source",
            "Remarks",
        ])

        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setAlternatingRowColors(True)

        parent_layout.addWidget(self.table)

    def create_buttons(self, parent_layout):
        """
        Create bottom buttons.
        """

        buttons_layout = QHBoxLayout()

        self.import_btn = QPushButton("✅ Import Selected")
        self.cancel_btn = QPushButton("❌ Cancel")

        self.import_btn.clicked.connect(self.accept_import)
        self.cancel_btn.clicked.connect(self.reject)

        buttons_layout.addStretch()
        buttons_layout.addWidget(self.import_btn)
        buttons_layout.addWidget(self.cancel_btn)

        parent_layout.addLayout(buttons_layout)

    def load_rows(self):
        """
        Load rows into table.
        """

        self.table.setRowCount(len(self.rows))

        for row_index, row_data in enumerate(self.rows):

            checkbox = QCheckBox()
            checkbox.setChecked(bool(row_data.get("import_suggested", True)))

            checkbox_widget = QFrame()
            checkbox_layout = QHBoxLayout(checkbox_widget)
            checkbox_layout.setContentsMargins(0, 0, 0, 0)
            checkbox_layout.setAlignment(Qt.AlignCenter)
            checkbox_layout.addWidget(checkbox)

            self.table.setCellWidget(row_index, 0, checkbox_widget)

            values = [
                row_data.get("category", ""),
                row_data.get("fund_code", ""),
                row_data.get("fund_name", ""),
                row_data.get("unit_type", ""),
                row_data.get("units", 0),
                row_data.get("nav", 0),
                row_data.get("investment_value", 0),
                row_data.get("fytd_gain_loss", 0),
                row_data.get("total_gain_loss", 0),
                row_data.get("confidence", 0),
                row_data.get("source", ""),
                row_data.get("remarks", ""),
            ]

            for col_offset, value in enumerate(values, start=1):

                item = QTableWidgetItem(str(value))

                # Read-only columns:
                # Category, Fund Code, Confidence, Source
                if col_offset in [1, 2, 10, 11]:
                    item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
                else:
                    item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable)

                if col_offset == 10:
                    self.apply_confidence_color(item, value)

                if col_offset == 1:
                    self.apply_category_color(item, value)

                self.table.setItem(row_index, col_offset, item)

        self.table.resizeColumnsToContents()

    def apply_category_color(self, item, category):
        """
        Color category cell.
        """

        category = str(category or "").lower()

        if "pension" in category or "mtpf" in category:
            item.setToolTip("This row belongs to Pension / MTPF.")
        else:
            item.setToolTip("This row belongs to Mutual Funds.")

    def apply_confidence_color(self, item, confidence):
        """
        Apply confidence color.
        """

        try:
            confidence = float(confidence)
        except Exception:
            confidence = 0

        if confidence >= 85:
            item.setBackground(Qt.green)
            item.setForeground(Qt.black)
        elif confidence >= 60:
            item.setBackground(Qt.yellow)
            item.setForeground(Qt.black)
        else:
            item.setBackground(Qt.red)
            item.setForeground(Qt.white)

    def toggle_all_rows(self):
        """
        Toggle all import checkboxes.
        """

        checked = self.select_all_checkbox.isChecked()

        for row in range(self.table.rowCount()):

            checkbox = self.get_row_checkbox(row)

            if checkbox:
                checkbox.setChecked(checked)

    def get_row_checkbox(self, row):
        """
        Return checkbox from row.
        """

        widget = self.table.cellWidget(row, 0)

        if not widget:
            return None

        return widget.findChild(QCheckBox)

    def get_cell_text(self, row, column):
        """
        Get table cell text.
        """

        item = self.table.item(row, column)

        if not item:
            return ""

        return item.text().strip()

    def accept_import(self):
        """
        Validate selected rows before accepting.
        """

        selected_rows = self.get_selected_rows()

        if not selected_rows:
            QMessageBox.warning(
                self,
                "No Rows Selected",
                "Please select at least one row to import."
            )
            return

        invalid_rows = []

        for index, row in enumerate(selected_rows, start=1):

            if not row["fund_code"]:
                invalid_rows.append(f"Row {index}: Fund Code is missing.")

            if row["units"] < 0:
                invalid_rows.append(f"Row {index}: Units cannot be negative.")

            if row["nav"] < 0:
                invalid_rows.append(f"Row {index}: NAV cannot be negative.")

            if row["investment_value"] < 0:
                invalid_rows.append(f"Row {index}: Investment Value cannot be negative.")

        if invalid_rows:
            QMessageBox.warning(
                self,
                "Invalid Rows",
                "\n".join(invalid_rows[:10])
            )
            return

        self.accept()

    def get_selected_rows(self):
        """
        Return selected/checked rows.
        """

        selected = []

        for row in range(self.table.rowCount()):

            checkbox = self.get_row_checkbox(row)

            if not checkbox or not checkbox.isChecked():
                continue

            category = self.get_cell_text(row, 1)
            fund_code = self.get_cell_text(row, 2).upper()
            fund_name = self.get_cell_text(row, 3)
            unit_type = self.get_cell_text(row, 4)

            units = safe_float(self.get_cell_text(row, 5))
            nav = safe_float(self.get_cell_text(row, 6))
            investment_value = safe_float(self.get_cell_text(row, 7))
            fytd_gain_loss = safe_float(self.get_cell_text(row, 8))
            total_gain_loss = safe_float(self.get_cell_text(row, 9))
            confidence = int(safe_float(self.get_cell_text(row, 10)))
            source = self.get_cell_text(row, 11)
            remarks = self.get_cell_text(row, 12)

            selected.append({
                "category": category,
                "fund_code": fund_code,
                "fund_name": fund_name,
                "unit_type": unit_type,
                "units": round(units, 4),
                "nav": round(nav, 4),
                "investment_value": round(investment_value, 2),
                "fytd_gain_loss": round(fytd_gain_loss, 2),
                "total_gain_loss": round(total_gain_loss, 2),
                "confidence": confidence,
                "source": source,
                "remarks": remarks,
            })

        return selected

    def apply_theme(self):
        """
        Apply light/dark theme.
        """

        dark = str(self.theme).lower() == "dark"

        if dark:
            self.setStyleSheet("""
                QDialog {
                    background-color: #121212;
                    color: #ffffff;
                }
                QLabel {
                    color: #ffffff;
                }
                QFrame#summary_card {
                    background-color: #1f1f1f;
                    border: 1px solid #444444;
                    border-radius: 8px;
                }
                QTableWidget {
                    background-color: #1e1e1e;
                    color: #ffffff;
                    gridline-color: #444444;
                    alternate-background-color: #252525;
                }
                QHeaderView::section {
                    background-color: #2c2c2c;
                    color: #ffffff;
                    padding: 5px;
                    border: 1px solid #444444;
                }
                QPushButton {
                    background-color: #2c2c2c;
                    color: #ffffff;
                    border: 1px solid #555555;
                    padding: 8px;
                    border-radius: 5px;
                }
                QPushButton:hover {
                    background-color: #3a3a3a;
                }
                QCheckBox {
                    color: #ffffff;
                }
            """)
        else:
            self.setStyleSheet("""
                QDialog {
                    background-color: #f5f5f5;
                    color: #000000;
                }
                QFrame#summary_card {
                    background-color: #ffffff;
                    border: 1px solid #d0d0d0;
                    border-radius: 8px;
                }
                QTableWidget {
                    background-color: #ffffff;
                    color: #000000;
                    alternate-background-color: #f2f2f2;
                }
                QHeaderView::section {
                    background-color: #eeeeee;
                    color: #000000;
                    padding: 5px;
                    border: 1px solid #cccccc;
                }
                QPushButton {
                    padding: 8px;
                    border-radius: 5px;
                }
            """)


def safe_float(value):
    """
    Convert value to float safely.
    """

    try:

        if value is None:
            return 0.0

        if isinstance(value, (int, float)):
            return float(value)

        text = str(value).strip()
        text = text.replace(",", "")
        text = text.replace("PKR", "")
        text = text.replace("Rs.", "")
        text = text.replace("Rs", "")

        if not text:
            return 0.0

        return float(text)

    except Exception:
        return 0.0
