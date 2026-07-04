"""
Dividend Summary Window
Shows stock-wise, monthly and yearly dividend income summaries.
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
    QTableWidget,
    QTableWidgetItem,
    QAbstractItemView,
    QHeaderView,
    QFrame,
    QTabWidget,
)

from services.settings_service import load_settings
from services.dividend_service import (
    get_income_summary,
    get_income_summary_by_symbol,
    get_income_summary_by_month,
    get_income_summary_by_year,
)


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


class DividendSummaryWindow(QWidget):
    """
    Dividend income summary window.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.settings = load_settings()
        self.summary_labels = {}

        self.setWindowTitle("Dividend Income Summary")
        self.resize(1100, 700)

        self.init_ui()
        self.load_summary()

    def init_ui(self):

        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        heading = QLabel("📊 Dividend Income Summary")
        heading.setAlignment(Qt.AlignCenter)
        heading.setStyleSheet("""
            font-size:22px;
            font-weight:bold;
            padding:10px;
        """)

        summary_layout = self.create_summary_cards()
        button_layout = self.create_buttons()

        self.tabs = QTabWidget()

        self.symbol_table = self.create_symbol_table()
        self.month_table = self.create_month_table()
        self.year_table = self.create_year_table()

        self.tabs.addTab(self.symbol_table, "Stock-wise Summary")
        self.tabs.addTab(self.month_table, "Monthly Summary")
        self.tabs.addTab(self.year_table, "Yearly Summary")

        main_layout.addWidget(heading)
        main_layout.addLayout(summary_layout)
        main_layout.addLayout(button_layout)
        main_layout.addWidget(self.tabs)

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

        btn_refresh = QPushButton("🔄 Refresh")
        btn_close = QPushButton("❌ Close")

        btn_refresh.setMinimumHeight(38)
        btn_close.setMinimumHeight(38)

        btn_refresh.clicked.connect(self.load_summary)
        btn_close.clicked.connect(self.close)

        layout.addWidget(btn_refresh)
        layout.addWidget(btn_close)

        return layout

    def create_symbol_table(self):

        table = QTableWidget()

        table.setColumnCount(5)

        table.setHorizontalHeaderLabels([
            "Symbol",
            "Records",
            "Gross Amount",
            "Tax Amount",
            "Net Amount",
        ])

        self.setup_table(table)

        return table

    def create_month_table(self):

        table = QTableWidget()

        table.setColumnCount(5)

        table.setHorizontalHeaderLabels([
            "Month",
            "Records",
            "Gross Amount",
            "Tax Amount",
            "Net Amount",
        ])

        self.setup_table(table)

        return table

    def create_year_table(self):

        table = QTableWidget()

        table.setColumnCount(5)

        table.setHorizontalHeaderLabels([
            "Year",
            "Records",
            "Gross Amount",
            "Tax Amount",
            "Net Amount",
        ])

        self.setup_table(table)

        return table

    def setup_table(self, table):

        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setSelectionMode(QAbstractItemView.SingleSelection)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.setAlternatingRowColors(True)
        table.setSortingEnabled(True)

        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.verticalHeader().setVisible(False)

    def load_summary(self):

        try:
            self.settings = load_settings()

            overall_summary = get_income_summary()
            symbol_summary = get_income_summary_by_symbol()
            month_summary = get_income_summary_by_month()
            year_summary = get_income_summary_by_year()

            self.update_summary_cards(overall_summary)
            self.display_symbol_summary(symbol_summary)
            self.display_month_summary(month_summary)
            self.display_year_summary(year_summary)

        except Exception as e:

            QMessageBox.critical(
                self,
                "Error",
                f"Failed to load dividend summary.\n\n{str(e)}"
            )

    def update_summary_cards(self, summary):

        gross_amount = float(summary["gross_amount"])
        tax_amount = float(summary["tax_amount"])
        net_amount = float(summary["net_amount"])
        records = int(summary["total_records"])

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
            str(records)
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

    def display_symbol_summary(self, summary):

        self.symbol_table.setSortingEnabled(False)
        self.symbol_table.setRowCount(0)
        self.symbol_table.setRowCount(len(summary))

        for row, item in enumerate(summary):

            symbol = str(item["symbol"]).upper()
            records = int(item["records"])
            gross_amount = float(item["gross_amount"])
            tax_amount = float(item["tax_amount"])
            net_amount = float(item["net_amount"])

            row_items = [
                self.create_table_item(symbol, symbol),
                self.create_table_item(str(records), records),
                self.create_table_item(self.format_currency(gross_amount), gross_amount),
                self.create_table_item(self.format_currency(tax_amount), tax_amount),
                self.create_table_item(self.format_currency(net_amount), net_amount),
            ]

            self.set_row_items(self.symbol_table, row, row_items)

        self.symbol_table.setSortingEnabled(True)

    def display_month_summary(self, summary):

        self.month_table.setSortingEnabled(False)
        self.month_table.setRowCount(0)
        self.month_table.setRowCount(len(summary))

        for row, item in enumerate(summary):

            month = str(item["month"])
            records = int(item["records"])
            gross_amount = float(item["gross_amount"])
            tax_amount = float(item["tax_amount"])
            net_amount = float(item["net_amount"])

            row_items = [
                self.create_table_item(month, month),
                self.create_table_item(str(records), records),
                self.create_table_item(self.format_currency(gross_amount), gross_amount),
                self.create_table_item(self.format_currency(tax_amount), tax_amount),
                self.create_table_item(self.format_currency(net_amount), net_amount),
            ]

            self.set_row_items(self.month_table, row, row_items)

        self.month_table.setSortingEnabled(True)

    def display_year_summary(self, summary):

        self.year_table.setSortingEnabled(False)
        self.year_table.setRowCount(0)
        self.year_table.setRowCount(len(summary))

        for row, item in enumerate(summary):

            year = str(item["year"])
            records = int(item["records"])
            gross_amount = float(item["gross_amount"])
            tax_amount = float(item["tax_amount"])
            net_amount = float(item["net_amount"])

            row_items = [
                self.create_table_item(year, year),
                self.create_table_item(str(records), records),
                self.create_table_item(self.format_currency(gross_amount), gross_amount),
                self.create_table_item(self.format_currency(tax_amount), tax_amount),
                self.create_table_item(self.format_currency(net_amount), net_amount),
            ]

            self.set_row_items(self.year_table, row, row_items)

        self.year_table.setSortingEnabled(True)

    def set_row_items(self, table, row, row_items):

        for column, table_item in enumerate(row_items):

            table_item.setTextAlignment(Qt.AlignCenter)

            if column == 3:
                table_item.setForeground(QBrush(QColor("red")))

            if column == 4:
                table_item.setForeground(QBrush(QColor("green")))

            table.setItem(row, column, table_item)

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
