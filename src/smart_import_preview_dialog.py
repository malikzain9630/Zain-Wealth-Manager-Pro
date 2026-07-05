"""
Smart Import Preview Dialog
Phase 10A - Preview imported portfolio rows before applying them.

This dialog:
- Shows imported rows in editable table
- Allows selecting/unselecting rows
- Shows confidence score
- Returns selected cleaned rows

It does NOT directly update portfolio.
"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QBrush
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QAbstractItemView,
    QHeaderView,
    QMessageBox,
    QFrame,
    QDialogButtonBox,
)

from services.smart_import_service import (
    get_import_summary,
    parse_number,
    normalize_symbol,
    is_valid_symbol,
)


class SmartImportPreviewDialog(QDialog):
    """
    Preview dialog for smart portfolio import.
    """

    def __init__(self, parent=None, rows=None, file_path=""):
        super().__init__(parent)

        self.rows = rows or []
        self.file_path = file_path
        self.summary_labels = {}

        self.setWindowTitle("Smart Portfolio Import Preview")
        self.resize(1250, 760)

        self.init_ui()
        self.load_rows()

    def init_ui(self):

        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        heading = QLabel("📥 Smart Portfolio Import Preview")
        heading.setAlignment(Qt.AlignCenter)
        heading.setStyleSheet("""
            font-size:22px;
            font-weight:bold;
            padding:8px;
        """)

        self.file_label = QLabel(f"File: {self.file_path}")
        self.file_label.setWordWrap(True)
        self.file_label.setStyleSheet("""
            font-size:12px;
            color:#555555;
            padding:4px;
        """)

        summary_layout = self.create_summary_cards()
        button_layout = self.create_action_buttons()

        self.table = self.create_table()

        note = QLabel(
            "Please review imported rows carefully. "
            "PDF/image extraction may contain mistakes. "
            "Only checked rows will be imported."
        )
        note.setWordWrap(True)
        note.setStyleSheet("""
            font-size:12px;
            color:#555555;
            padding:4px;
        """)

        self.buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        self.buttons.button(QDialogButtonBox.Ok).setText("Import Selected")
        self.buttons.button(QDialogButtonBox.Cancel).setText("Cancel")

        self.buttons.accepted.connect(self.validate_and_accept)
        self.buttons.rejected.connect(self.reject)

        main_layout.addWidget(heading)
        main_layout.addWidget(self.file_label)
        main_layout.addLayout(summary_layout)
        main_layout.addLayout(button_layout)
        main_layout.addWidget(self.table)
        main_layout.addWidget(note)
        main_layout.addWidget(self.buttons)

    def create_summary_cards(self):

        layout = QHBoxLayout()

        cards = [
            ("Rows Detected", "total_rows"),
            ("Selected Rows", "selected_rows"),
            ("Investment Value", "total_investment"),
            ("Current Value", "total_current"),
            ("Estimated P/L", "estimated_profit"),
            ("Low Confidence", "low_confidence_rows"),
        ]

        for title, key in cards:
            layout.addWidget(self.create_card(title, key))

        return layout

    def create_card(self, title, key):

        card = QFrame()
        card.setFrameShape(QFrame.StyledPanel)
        card.setMinimumHeight(76)
        card.setStyleSheet("""
            QFrame {
                border:1px solid #cccccc;
                border-radius:8px;
                background-color:#f8f9fa;
            }
        """)

        layout = QVBoxLayout()
        card.setLayout(layout)

        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            font-size:12px;
            font-weight:bold;
            color:#444444;
        """)

        value_label = QLabel("0")
        value_label.setAlignment(Qt.AlignCenter)
        value_label.setStyleSheet("""
            font-size:16px;
            font-weight:bold;
            color:green;
        """)

        layout.addWidget(title_label)
        layout.addWidget(value_label)

        self.summary_labels[key] = value_label

        return card

    def create_action_buttons(self):

        layout = QHBoxLayout()

        select_all_btn = QPushButton("✅ Select All")
        unselect_all_btn = QPushButton("⬜ Unselect All")
        validate_btn = QPushButton("🔍 Validate Rows")
        remove_invalid_btn = QPushButton("🧹 Uncheck Invalid")

        buttons = [
            select_all_btn,
            unselect_all_btn,
            validate_btn,
            remove_invalid_btn,
        ]

        for button in buttons:
            button.setMinimumHeight(36)
            layout.addWidget(button)

        select_all_btn.clicked.connect(self.select_all_rows)
        unselect_all_btn.clicked.connect(self.unselect_all_rows)
        validate_btn.clicked.connect(self.validate_rows_message)
        remove_invalid_btn.clicked.connect(self.uncheck_invalid_rows)

        return layout

    def create_table(self):

        table = QTableWidget()
        table.setColumnCount(10)

        table.setHorizontalHeaderLabels([
            "Import?",
            "Symbol",
            "Shares",
            "Avg Price",
            "Current Price",
            "Investment Value",
            "Current Value",
            "Confidence",
            "Source",
            "Remarks",
        ])

        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setSelectionMode(QAbstractItemView.SingleSelection)
        table.setEditTriggers(QAbstractItemView.DoubleClicked | QAbstractItemView.SelectedClicked)
        table.setAlternatingRowColors(True)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.verticalHeader().setVisible(False)
        table.itemChanged.connect(self.table_item_changed)

        return table

    def load_rows(self):

        self.table.blockSignals(True)

        self.table.setRowCount(0)
        self.table.setRowCount(len(self.rows))

        for row_index, row_data in enumerate(self.rows):

            checkbox_item = QTableWidgetItem()
            checkbox_item.setFlags(
                Qt.ItemIsUserCheckable
                | Qt.ItemIsEnabled
                | Qt.ItemIsSelectable
            )
            checkbox_item.setCheckState(Qt.Checked)
            checkbox_item.setTextAlignment(Qt.AlignCenter)

            self.table.setItem(row_index, 0, checkbox_item)

            values = [
                row_data.get("symbol", ""),
                row_data.get("shares", 0),
                row_data.get("avg_price", 0),
                row_data.get("current_price", 0),
                row_data.get("investment_value", 0),
                row_data.get("current_value", 0),
                row_data.get("confidence", 0),
                row_data.get("source", ""),
                row_data.get("remarks", ""),
            ]

            for col_offset, value in enumerate(values, start=1):

                item = QTableWidgetItem(str(value))
                item.setTextAlignment(Qt.AlignCenter)

                if col_offset in [5, 6]:
                    item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
                elif col_offset == 7:
                    item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
                else:
                    item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable)

                if col_offset == 7:
                    self.apply_confidence_color(item, value)

                self.table.setItem(row_index, col_offset, item)

        self.table.blockSignals(False)

        self.update_calculated_values()
        self.update_summary_cards()

    def table_item_changed(self, item):

        if item.column() in [1, 2, 3, 4]:
            self.update_row_calculated_values(item.row())

        self.update_summary_cards()

    def update_calculated_values(self):

        for row in range(self.table.rowCount()):
            self.update_row_calculated_values(row)

    def update_row_calculated_values(self, row):

        symbol = self.get_cell_text(row, 1)
        shares = parse_number(self.get_cell_text(row, 2))
        avg_price = parse_number(self.get_cell_text(row, 3))
        current_price = parse_number(self.get_cell_text(row, 4))

        investment_value = shares * avg_price
        current_value = shares * current_price

        self.set_readonly_cell(row, 5, f"{investment_value:.2f}")
        self.set_readonly_cell(row, 6, f"{current_value:.2f}")

        confidence = self.calculate_row_confidence(
            symbol,
            shares,
            avg_price,
            current_price
        )

        confidence_item = QTableWidgetItem(str(confidence))
        confidence_item.setTextAlignment(Qt.AlignCenter)
        confidence_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
        self.apply_confidence_color(confidence_item, confidence)
        self.table.setItem(row, 7, confidence_item)

    def set_readonly_cell(self, row, column, text):

        item = QTableWidgetItem(text)
        item.setTextAlignment(Qt.AlignCenter)
        item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)

        try:
            number = float(text)
        except Exception:
            number = 0

        if number > 0:
            item.setForeground(QBrush(QColor("green")))

        self.table.setItem(row, column, item)

    def calculate_row_confidence(self, symbol, shares, avg_price, current_price):

        score = 0

        if is_valid_symbol(symbol):
            score += 35

        if shares > 0:
            score += 25

        if avg_price > 0:
            score += 20

        if current_price > 0:
            score += 20

        return score

    def apply_confidence_color(self, item, value):

        try:
            confidence = int(float(value))
        except Exception:
            confidence = 0

        if confidence >= 80:
            item.setForeground(QBrush(QColor("green")))
        elif confidence >= 60:
            item.setForeground(QBrush(QColor("orange")))
        else:
            item.setForeground(QBrush(QColor("red")))

        item.setToolTip("Green = high confidence, orange = review, red = likely issue")

    def update_summary_cards(self):

        selected_rows = self.get_selected_preview_rows(validate=False)
        summary = get_import_summary(selected_rows)

        self.summary_labels["total_rows"].setText(str(self.table.rowCount()))
        self.summary_labels["selected_rows"].setText(str(summary["total_rows"]))
        self.summary_labels["total_investment"].setText(
            f"PKR {summary['total_investment']:,.2f}"
        )
        self.summary_labels["total_current"].setText(
            f"PKR {summary['total_current']:,.2f}"
        )
        self.summary_labels["estimated_profit"].setText(
            f"PKR {summary['estimated_profit']:,.2f}"
        )
        self.summary_labels["low_confidence_rows"].setText(
            str(summary["low_confidence_rows"])
        )

        if summary["estimated_profit"] >= 0:
            self.summary_labels["estimated_profit"].setStyleSheet("""
                font-size:16px;
                font-weight:bold;
                color:green;
            """)
        else:
            self.summary_labels["estimated_profit"].setStyleSheet("""
                font-size:16px;
                font-weight:bold;
                color:red;
            """)

    def get_selected_preview_rows(self, validate=True):

        selected_rows = []

        for row in range(self.table.rowCount()):

            checkbox_item = self.table.item(row, 0)

            if checkbox_item is None:
                continue

            if checkbox_item.checkState() != Qt.Checked:
                continue

            symbol = normalize_symbol(self.get_cell_text(row, 1))
            shares = parse_number(self.get_cell_text(row, 2))
            avg_price = parse_number(self.get_cell_text(row, 3))
            current_price = parse_number(self.get_cell_text(row, 4))

            investment_value = shares * avg_price
            current_value = shares * current_price

            confidence = self.calculate_row_confidence(
                symbol,
                shares,
                avg_price,
                current_price
            )

            remarks = self.get_cell_text(row, 9)

            if validate:

                if not is_valid_symbol(symbol):
                    raise ValueError(
                        f"Row {row + 1}: Invalid stock symbol."
                    )

                if shares <= 0:
                    raise ValueError(
                        f"Row {row + 1}: Shares must be greater than zero."
                    )

                if avg_price < 0:
                    raise ValueError(
                        f"Row {row + 1}: Average price cannot be negative."
                    )

                if current_price < 0:
                    raise ValueError(
                        f"Row {row + 1}: Current price cannot be negative."
                    )

            selected_rows.append({
                "symbol": symbol,
                "shares": round(shares, 4),
                "avg_price": round(avg_price, 4),
                "current_price": round(current_price, 4),
                "investment_value": round(investment_value, 2),
                "current_value": round(current_value, 2),
                "confidence": confidence,
                "source": self.get_cell_text(row, 8),
                "remarks": remarks,
            })

        return selected_rows

    def validate_rows_message(self):

        try:
            selected_rows = self.get_selected_preview_rows(validate=True)

            QMessageBox.information(
                self,
                "Validation Successful",
                f"{len(selected_rows)} selected rows are valid."
            )

        except Exception as e:
            QMessageBox.warning(
                self,
                "Validation Error",
                str(e)
            )

    def uncheck_invalid_rows(self):

        count = 0

        for row in range(self.table.rowCount()):

            symbol = self.get_cell_text(row, 1)
            shares = parse_number(self.get_cell_text(row, 2))
            avg_price = parse_number(self.get_cell_text(row, 3))
            current_price = parse_number(self.get_cell_text(row, 4))

            confidence = self.calculate_row_confidence(
                symbol,
                shares,
                avg_price,
                current_price
            )

            if confidence < 70:

                item = self.table.item(row, 0)

                if item:
                    item.setCheckState(Qt.Unchecked)
                    count += 1

        self.update_summary_cards()

        QMessageBox.information(
            self,
            "Invalid Rows Unchecked",
            f"{count} low-confidence rows were unchecked."
        )

    def select_all_rows(self):

        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)

            if item:
                item.setCheckState(Qt.Checked)

        self.update_summary_cards()

    def unselect_all_rows(self):

        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)

            if item:
                item.setCheckState(Qt.Unchecked)

        self.update_summary_cards()

    def validate_and_accept(self):

        try:
            selected_rows = self.get_selected_preview_rows(validate=True)

            if not selected_rows:
                QMessageBox.warning(
                    self,
                    "No Rows Selected",
                    "Please select at least one valid row to import."
                )
                return

            low_confidence = [
                row for row in selected_rows
                if int(row.get("confidence", 0)) < 70
            ]

            if low_confidence:

                confirm = QMessageBox.question(
                    self,
                    "Low Confidence Rows",
                    f"{len(low_confidence)} selected rows have low confidence.\n\n"
                    "Do you still want to continue?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )

                if confirm != QMessageBox.Yes:
                    return

            self.accept()

        except Exception as e:
            QMessageBox.warning(
                self,
                "Import Validation Error",
                str(e)
            )

    def get_data(self):

        return self.get_selected_preview_rows(validate=True)

    def get_cell_text(self, row, column):

        item = self.table.item(row, column)

        if item is None:
            return ""

        return item.text().strip()
