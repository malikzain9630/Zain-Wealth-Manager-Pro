"""
Dividend & Income Tracker Window
"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QBrush
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QMessageBox,
    QLabel,
    QLineEdit,
    QTableWidget,
    QTableWidgetItem,
    QAbstractItemView,
    QHeaderView,
    QFrame,
)

from services.settings_service import load_settings
from services.dividend_service import (
    get_all_dividends,
    add_new_dividend,
    update_existing_dividend,
    remove_dividend,
)

from dividend_dialog import DividendDialog


class SortableTableWidgetItem(QTableWidgetItem):

    def __init__(self, text, sort_value=None):
        super().__init__(text)

        if sort_value is None:
            self.sort_value = text
        else:
            self.sort_value = sort_value

    def __lt__(self, other):

        if isinstance(other, SortableTableWidgetItem):

            try:
                return float(self.sort_value) < float(other.sort_value)

            except (ValueError, TypeError):
                return str(self.sort_value) < str(other.sort_value)

        return super().__lt__(other)


class DividendWindow(QWidget):
    """
    Dividend & Income Tracker main window.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.settings = load_settings()
        self.summary_labels = {}
        self.dividends = []

        self.setWindowTitle("Dividend & Income Tracker")
        self.resize(1250, 700)

        self.init_ui()
        self.load_dividends()

    def init_ui(self):

        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        heading = QLabel("💰 Dividend & Income Tracker")
        heading.setAlignment(Qt.AlignCenter)
        heading.setStyleSheet("""
            font-size:22px;
            font-weight:bold;
            padding:10px;
        """)

        summary_layout = self.create_summary_cards()
        button_layout = self.create_buttons()
        search_layout = self.create_search_bar()
        self.table = self.create_table()

        main_layout.addWidget(heading)
        main_layout.addLayout(summary_layout)
        main_layout.addLayout(button_layout)
        main_layout.addLayout(search_layout)
        main_layout.addWidget(self.table)

    def create_summary_cards(self):

        layout = QHBoxLayout()

        cards = [
            ("Gross Dividend", "gross"),
            ("Tax Deducted", "tax"),
            ("Net Received", "net"),
            ("Total Records", "records"),
        ]

        for title, key in cards:

            card = self.create_card(title, key)
            layout.addWidget(card)

        return layout

    def create_card(self, title, key):

        card = QFrame()
        card.setFrameShape(QFrame.StyledPanel)
        card.setMinimumHeight(90)

        card.setStyleSheet("""
            QFrame {
                border: 1px solid #cccccc;
                border-radius: 8px;
                background-color: #f8f9fa;
            }
        """)

        layout = QVBoxLayout()
        card.setLayout(layout)

        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            font-size:13px;
            font-weight:bold;
            color:#444444;
        """)

        value_label = QLabel("0")
        value_label.setAlignment(Qt.AlignCenter)
        value_label.setStyleSheet("""
            font-size:17px;
            font-weight:bold;
            color:#000000;
        """)

        layout.addWidget(title_label)
        layout.addWidget(value_label)

        self.summary_labels[key] = value_label

        return card

    def create_buttons(self):

        layout = QHBoxLayout()

        btn_add = QPushButton("➕ Add Dividend")
        btn_edit = QPushButton("✏ Edit Dividend")
        btn_delete = QPushButton("🗑 Delete Dividend")
        btn_refresh = QPushButton("🔄 Refresh")
        btn_close = QPushButton("❌ Close")

        buttons = [
            btn_add,
            btn_edit,
            btn_delete,
            btn_refresh,
            btn_close,
        ]

        for btn in buttons:
            btn.setMinimumHeight(38)
            layout.addWidget(btn)

        btn_add.clicked.connect(self.open_add_dialog)
        btn_edit.clicked.connect(self.open_edit_dialog)
        btn_delete.clicked.connect(self.delete_selected_dividend)
        btn_refresh.clicked.connect(self.load_dividends)
        btn_close.clicked.connect(self.close)

        return layout

    def create_search_bar(self):

        layout = QHBoxLayout()

        search_label = QLabel("Search:")
        search_label.setStyleSheet("""
            font-size:14px;
            font-weight:bold;
        """)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(
            "Search by symbol, date or remarks e.g. FFC, 2026-06, final dividend"
        )
        self.search_input.setMinimumHeight(35)
        self.search_input.textChanged.connect(self.apply_filter)

        clear_btn = QPushButton("Clear")
        clear_btn.setMinimumHeight(35)
        clear_btn.clicked.connect(self.clear_search)

        self.search_result_label = QLabel("")
        self.search_result_label.setStyleSheet("""
            font-size:13px;
            font-weight:bold;
        """)

        layout.addWidget(search_label)
        layout.addWidget(self.search_input)
        layout.addWidget(clear_btn)
        layout.addWidget(self.search_result_label)

        return layout

    def create_table(self):

        table = QTableWidget()

        table.setColumnCount(9)

        table.setHorizontalHeaderLabels([
            "ID",
            "Symbol",
            "Shares",
            "Dividend / Share",
            "Gross Amount",
            "Tax Amount",
            "Net Amount",
            "Payment Date",
            "Remarks",
        ])

        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setSelectionMode(QAbstractItemView.SingleSelection)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.setAlternatingRowColors(True)
        table.setSortingEnabled(True)

        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.verticalHeader().setVisible(False)

        table.setColumnHidden(0, True)

        return table

    def load_dividends(self):

        try:
            self.dividends = get_all_dividends()

            self.search_input.clear()

            self.display_dividends(self.dividends)
            self.update_summary_cards(self.dividends)
            self.update_search_result_label(self.dividends)

        except Exception as e:

            QMessageBox.critical(
                self,
                "Error",
                f"Failed to load dividends.\n\n{str(e)}"
            )

    def display_dividends(self, dividends):

        self.table.setSortingEnabled(False)

        self.table.setRowCount(0)
        self.table.setRowCount(len(dividends))

        for row, item in enumerate(dividends):

            dividend_id = int(item["id"])
            symbol = str(item["symbol"]).upper()
            shares = float(item["shares"])
            dividend_per_share = float(item["dividend_per_share"])
            gross_amount = float(item["gross_amount"])
            tax_amount = float(item["tax_amount"])
            net_amount = float(item["net_amount"])
            payment_date = str(item["payment_date"])
            remarks = str(item["remarks"])

            row_items = [
                self.create_table_item(str(dividend_id), dividend_id),
                self.create_table_item(symbol, symbol),
                self.create_table_item(self.format_quantity(shares), shares),
                self.create_table_item(self.format_number(dividend_per_share), dividend_per_share),
                self.create_table_item(self.format_currency(gross_amount), gross_amount),
                self.create_table_item(self.format_currency(tax_amount), tax_amount),
                self.create_table_item(self.format_currency(net_amount), net_amount),
                self.create_table_item(payment_date, payment_date),
                self.create_table_item(remarks, remarks),
            ]

            for column, table_item in enumerate(row_items):

                table_item.setTextAlignment(Qt.AlignCenter)

                if column == 6:
                    table_item.setForeground(QBrush(QColor("green")))

                if column == 5 and tax_amount > 0:
                    table_item.setForeground(QBrush(QColor("red")))

                self.table.setItem(row, column, table_item)

        self.table.setSortingEnabled(True)

    def apply_filter(self):

        search_text = self.search_input.text().strip().lower()

        if not search_text:

            filtered_dividends = self.dividends

        else:

            filtered_dividends = []

            for item in self.dividends:

                symbol = str(item["symbol"]).lower()
                payment_date = str(item["payment_date"]).lower()
                remarks = str(item["remarks"]).lower()

                if (
                    search_text in symbol
                    or search_text in payment_date
                    or search_text in remarks
                ):
                    filtered_dividends.append(item)

        self.display_dividends(filtered_dividends)
        self.update_summary_cards(filtered_dividends)
        self.update_search_result_label(filtered_dividends)

    def clear_search(self):

        self.search_input.clear()

        self.display_dividends(self.dividends)
        self.update_summary_cards(self.dividends)
        self.update_search_result_label(self.dividends)

    def update_search_result_label(self, dividends):

        self.search_result_label.setText(
            f"Showing: {len(dividends)} / {len(self.dividends)}"
        )

    def update_summary_cards(self, dividends):

        gross_amount = 0
        tax_amount = 0
        net_amount = 0

        for item in dividends:

            gross_amount += float(item["gross_amount"])
            tax_amount += float(item["tax_amount"])
            net_amount += float(item["net_amount"])

        self.summary_labels["gross"].setText(
            self.format_currency(gross_amount)
        )

        self.summary_labels["tax"].setText(
            self.format_currency(tax_amount)
        )

        self.summary_labels["net"].setText(
            self.format_currency(net_amount)
        )

        self.summary_labels["records"].setText(
            str(len(dividends))
        )

        self.summary_labels["net"].setStyleSheet("""
            font-size:17px;
            font-weight:bold;
            color:green;
        """)

        self.summary_labels["tax"].setStyleSheet("""
            font-size:17px;
            font-weight:bold;
            color:red;
        """)

    def open_add_dialog(self):

        dialog = DividendDialog(self)

        if dialog.exec():

            try:
                data = dialog.get_data()

                add_new_dividend(
                    data["symbol"],
                    data["shares"],
                    data["dividend_per_share"],
                    data["tax_amount"],
                    data["payment_date"],
                    data["remarks"]
                )

                QMessageBox.information(
                    self,
                    "Success",
                    "Dividend record added successfully."
                )

                self.load_dividends()

            except Exception as e:

                QMessageBox.critical(
                    self,
                    "Error",
                    str(e)
                )

    def open_edit_dialog(self):

        selected = self.get_selected_dividend()

        if not selected:
            QMessageBox.warning(
                self,
                "No Selection",
                "Please select a dividend record to edit."
            )
            return

        dialog = DividendDialog(self, selected)

        if dialog.exec():

            try:
                data = dialog.get_data()

                update_existing_dividend(
                    data["id"],
                    data["symbol"],
                    data["shares"],
                    data["dividend_per_share"],
                    data["tax_amount"],
                    data["payment_date"],
                    data["remarks"]
                )

                QMessageBox.information(
                    self,
                    "Success",
                    "Dividend record updated successfully."
                )

                self.load_dividends()

            except Exception as e:

                QMessageBox.critical(
                    self,
                    "Error",
                    str(e)
                )

    def delete_selected_dividend(self):

        selected = self.get_selected_dividend()

        if not selected:
            QMessageBox.warning(
                self,
                "No Selection",
                "Please select a dividend record to delete."
            )
            return

        dividend_id = selected["id"]
        symbol = selected["symbol"]
        payment_date = selected["payment_date"]

        confirm = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete dividend record?\n\n"
            f"Symbol: {symbol}\n"
            f"Date: {payment_date}",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if confirm != QMessageBox.Yes:
            return

        try:
            remove_dividend(dividend_id)

            QMessageBox.information(
                self,
                "Success",
                "Dividend record deleted successfully."
            )

            self.load_dividends()

        except Exception as e:

            QMessageBox.critical(
                self,
                "Error",
                str(e)
            )

    def get_selected_dividend(self):

        selected_row = self.table.currentRow()

        if selected_row < 0:
            return None

        id_item = self.table.item(selected_row, 0)
        symbol_item = self.table.item(selected_row, 1)
        shares_item = self.table.item(selected_row, 2)
        dividend_per_share_item = self.table.item(selected_row, 3)
        gross_amount_item = self.table.item(selected_row, 4)
        tax_amount_item = self.table.item(selected_row, 5)
        net_amount_item = self.table.item(selected_row, 6)
        payment_date_item = self.table.item(selected_row, 7)
        remarks_item = self.table.item(selected_row, 8)

        if (
            id_item is None
            or symbol_item is None
            or shares_item is None
            or dividend_per_share_item is None
            or gross_amount_item is None
            or tax_amount_item is None
            or net_amount_item is None
            or payment_date_item is None
        ):
            return None

        try:
            remarks = ""

            if remarks_item:
                remarks = remarks_item.text().strip()

            return {
                "id": int(id_item.data(Qt.UserRole)),
                "symbol": symbol_item.text().strip().upper(),
                "shares": float(shares_item.data(Qt.UserRole)),
                "dividend_per_share": float(
                    dividend_per_share_item.data(Qt.UserRole)
                ),
                "gross_amount": float(
                    gross_amount_item.data(Qt.UserRole)
                ),
                "tax_amount": float(
                    tax_amount_item.data(Qt.UserRole)
                ),
                "net_amount": float(
                    net_amount_item.data(Qt.UserRole)
                ),
                "payment_date": payment_date_item.text().strip(),
                "remarks": remarks,
            }

        except (ValueError, TypeError):

            QMessageBox.warning(
                self,
                "Invalid Data",
                "Selected dividend record contains invalid data."
            )

            return None

    def create_table_item(self, text, value):

        item = SortableTableWidgetItem(text, value)
        item.setData(Qt.UserRole, value)

        return item

    def get_currency(self):

        currency = str(
            self.settings.get("currency", "PKR")
        ).strip().upper()

        if not currency:
            currency = "PKR"

        return currency

    def format_currency(self, value):

        return f"{self.get_currency()} {float(value):,.2f}"

    def format_number(self, value):

        return f"{float(value):,.4f}"

    def format_quantity(self, value):

        if float(value).is_integer():
            return f"{int(value):,}"

        return f"{float(value):,.2f}"
