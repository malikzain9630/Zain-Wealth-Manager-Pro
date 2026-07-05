"""
Dividend Yield & Passive Income Forecast Window
Shows dividend yield, monthly forecast and yearly passive income estimate.
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
from services.dividend_yield_service import (
    get_dividend_yield_by_stock,
    get_passive_income_forecast,
    get_monthly_income_trend,
    get_yearly_income_trend,
    get_top_dividend_stocks,
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


class DividendYieldWindow(QWidget):
    """
    Dividend Yield & Passive Income Forecast window.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.settings = load_settings()
        self.summary_labels = {}

        self.setWindowTitle("Dividend Yield & Passive Income Forecast")
        self.resize(1250, 760)

        self.init_ui()
        self.apply_theme()
        self.load_data()

    def init_ui(self):

        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        self.heading = QLabel("💸 Dividend Yield & Passive Income Forecast")
        self.heading.setAlignment(Qt.AlignCenter)

        summary_layout = self.create_summary_cards()
        button_layout = self.create_buttons()

        self.tabs = QTabWidget()

        self.yield_table = self.create_yield_table()
        self.monthly_table = self.create_monthly_table()
        self.yearly_table = self.create_yearly_table()
        self.top_stocks_table = self.create_top_stocks_table()

        self.tabs.addTab(self.yield_table, "Stock-wise Yield")
        self.tabs.addTab(self.monthly_table, "Monthly Income Trend")
        self.tabs.addTab(self.yearly_table, "Yearly Income Trend")
        self.tabs.addTab(self.top_stocks_table, "Top Dividend Stocks")

        main_layout.addWidget(self.heading)
        main_layout.addLayout(summary_layout)
        main_layout.addLayout(button_layout)
        main_layout.addWidget(self.tabs)

    def create_summary_cards(self):

        layout = QHBoxLayout()

        cards = [
            ("Total Net Received", "total_net_received"),
            ("Current Year Net", "current_year_net"),
            ("Monthly Forecast", "monthly_forecast"),
            ("Yearly Forecast", "yearly_forecast"),
            ("Top Dividend Stock", "top_stock"),
            ("Total Records", "total_records"),
        ]

        for title, key in cards:

            card = self.create_card(title, key)
            layout.addWidget(card)

        return layout

    def create_card(self, title, key):

        card = QFrame()
        card.setObjectName("SummaryCard")
        card.setFrameShape(QFrame.StyledPanel)
        card.setMinimumHeight(90)

        layout = QVBoxLayout()
        card.setLayout(layout)

        title_label = QLabel(title)
        title_label.setObjectName("CardTitle")
        title_label.setAlignment(Qt.AlignCenter)

        value_label = QLabel("0")
        value_label.setObjectName("CardValue")
        value_label.setAlignment(Qt.AlignCenter)

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

        btn_refresh.clicked.connect(self.load_data)
        btn_close.clicked.connect(self.close)

        layout.addWidget(btn_refresh)
        layout.addWidget(btn_close)

        return layout

    def create_yield_table(self):

        table = QTableWidget()
        table.setColumnCount(11)

        table.setHorizontalHeaderLabels([
            "Symbol",
            "Shares",
            "Avg Price",
            "Current Price",
            "Investment Value",
            "Current Value",
            "Gross Dividend",
            "Tax",
            "Net Dividend",
            "Yield on Cost %",
            "Current Yield %",
        ])

        self.setup_table(table)

        return table

    def create_monthly_table(self):

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

    def create_yearly_table(self):

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

    def create_top_stocks_table(self):

        table = QTableWidget()
        table.setColumnCount(6)

        table.setHorizontalHeaderLabels([
            "Rank",
            "Symbol",
            "Net Dividend",
            "Yield on Cost %",
            "Current Yield %",
            "Records",
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

    def load_data(self):

        try:
            self.settings = load_settings()

            self.update_summary_cards()
            self.display_yield_table()
            self.display_monthly_table()
            self.display_yearly_table()
            self.display_top_stocks_table()
            self.apply_theme()

        except Exception as e:

            QMessageBox.critical(
                self,
                "Dividend Yield Error",
                f"Failed to load dividend yield forecast.\n\n{str(e)}"
            )

    def update_summary_cards(self):

        forecast = get_passive_income_forecast()
        top_stocks = get_top_dividend_stocks(1)

        top_symbol = "-"

        if top_stocks:
            top_symbol = str(top_stocks[0]["symbol"]).upper()

        self.summary_labels["total_net_received"].setText(
            self.format_currency(forecast["total_net_received"])
        )

        self.summary_labels["current_year_net"].setText(
            self.format_currency(forecast["current_year_net"])
        )

        self.summary_labels["monthly_forecast"].setText(
            self.format_currency(forecast["monthly_forecast"])
        )

        self.summary_labels["yearly_forecast"].setText(
            self.format_currency(forecast["yearly_forecast"])
        )

        self.summary_labels["top_stock"].setText(top_symbol)

        self.summary_labels["total_records"].setText(
            str(forecast["total_records"])
        )

        self.summary_labels["monthly_forecast"].setStyleSheet("""
            font-size:17px;
            font-weight:bold;
            color:green;
        """)

        self.summary_labels["yearly_forecast"].setStyleSheet("""
            font-size:17px;
            font-weight:bold;
            color:green;
        """)

    def display_yield_table(self):

        rows = get_dividend_yield_by_stock()

        self.yield_table.setSortingEnabled(False)
        self.yield_table.setRowCount(0)
        self.yield_table.setRowCount(len(rows))

        for row, item in enumerate(rows):

            row_items = [
                self.create_table_item(item["symbol"], item["symbol"]),
                self.create_table_item(self.format_quantity(item["shares"]), item["shares"]),
                self.create_table_item(self.format_number(item["avg_price"]), item["avg_price"]),
                self.create_table_item(self.format_number(item["current_price"]), item["current_price"]),
                self.create_table_item(self.format_currency(item["investment_value"]), item["investment_value"]),
                self.create_table_item(self.format_currency(item["current_value"]), item["current_value"]),
                self.create_table_item(self.format_currency(item["gross_dividend"]), item["gross_dividend"]),
                self.create_table_item(self.format_currency(item["tax_amount"]), item["tax_amount"]),
                self.create_table_item(self.format_currency(item["net_dividend"]), item["net_dividend"]),
                self.create_table_item(f"{item['yield_on_cost']:.2f}%", item["yield_on_cost"]),
                self.create_table_item(f"{item['current_yield']:.2f}%", item["current_yield"]),
            ]

            self.set_row_items(self.yield_table, row, row_items)

        self.yield_table.setSortingEnabled(True)

    def display_monthly_table(self):

        rows = get_monthly_income_trend()

        self.monthly_table.setSortingEnabled(False)
        self.monthly_table.setRowCount(0)
        self.monthly_table.setRowCount(len(rows))

        for row, item in enumerate(rows):

            row_items = [
                self.create_table_item(item["month"], item["month"]),
                self.create_table_item(str(item["records"]), item["records"]),
                self.create_table_item(self.format_currency(item["gross_amount"]), item["gross_amount"]),
                self.create_table_item(self.format_currency(item["tax_amount"]), item["tax_amount"]),
                self.create_table_item(self.format_currency(item["net_amount"]), item["net_amount"]),
            ]

            self.set_row_items(self.monthly_table, row, row_items)

        self.monthly_table.setSortingEnabled(True)

    def display_yearly_table(self):

        rows = get_yearly_income_trend()

        self.yearly_table.setSortingEnabled(False)
        self.yearly_table.setRowCount(0)
        self.yearly_table.setRowCount(len(rows))

        for row, item in enumerate(rows):

            row_items = [
                self.create_table_item(item["year"], item["year"]),
                self.create_table_item(str(item["records"]), item["records"]),
                self.create_table_item(self.format_currency(item["gross_amount"]), item["gross_amount"]),
                self.create_table_item(self.format_currency(item["tax_amount"]), item["tax_amount"]),
                self.create_table_item(self.format_currency(item["net_amount"]), item["net_amount"]),
            ]

            self.set_row_items(self.yearly_table, row, row_items)

        self.yearly_table.setSortingEnabled(True)

    def display_top_stocks_table(self):

        rows = get_top_dividend_stocks(10)

        self.top_stocks_table.setSortingEnabled(False)
        self.top_stocks_table.setRowCount(0)
        self.top_stocks_table.setRowCount(len(rows))

        for row, item in enumerate(rows):

            rank = row + 1

            row_items = [
                self.create_table_item(str(rank), rank),
                self.create_table_item(item["symbol"], item["symbol"]),
                self.create_table_item(self.format_currency(item["net_dividend"]), item["net_dividend"]),
                self.create_table_item(f"{item['yield_on_cost']:.2f}%", item["yield_on_cost"]),
                self.create_table_item(f"{item['current_yield']:.2f}%", item["current_yield"]),
                self.create_table_item(str(item["dividend_records"]), item["dividend_records"]),
            ]

            self.set_row_items(self.top_stocks_table, row, row_items)

        self.top_stocks_table.setSortingEnabled(True)

    def set_row_items(self, table, row, row_items):

        for column, table_item in enumerate(row_items):

            table_item.setTextAlignment(Qt.AlignCenter)

            text = table_item.text()

            if "PKR" in text or "%" in text:

                value = table_item.data(Qt.UserRole)

                try:
                    value = float(value)
                except (ValueError, TypeError):
                    value = 0

                if value > 0:
                    table_item.setForeground(QBrush(QColor("green")))
                elif value < 0:
                    table_item.setForeground(QBrush(QColor("red")))

            table.setItem(row, column, table_item)

    def create_table_item(self, text, value):

        item = SortableTableWidgetItem(text, value)
        item.setData(Qt.UserRole, value)

        return item

    def apply_theme(self):

        theme = str(
            self.settings.get("theme", "light")
        ).strip().lower()

        if theme == "dark":

            self.setStyleSheet("""
                QWidget {
                    background-color: #1e1e1e;
                    color: #ffffff;
                }

                QLabel {
                    color: #ffffff;
                }

                QLabel#CardTitle {
                    font-size:13px;
                    font-weight:bold;
                    color:#dddddd;
                }

                QLabel#CardValue {
                    font-size:17px;
                    font-weight:bold;
                    color:#ffffff;
                }

                QPushButton {
                    background-color: #2d2d30;
                    color: #ffffff;
                    border: 1px solid #555555;
                    border-radius: 5px;
                    padding: 6px;
                }

                QPushButton:hover {
                    background-color: #3e3e42;
                }

                QTableWidget {
                    background-color: #252526;
                    color: #ffffff;
                    gridline-color: #555555;
                    alternate-background-color: #2d2d30;
                }

                QHeaderView::section {
                    background-color: #333333;
                    color: #ffffff;
                    padding: 5px;
                    border: 1px solid #555555;
                }

                QFrame#SummaryCard {
                    border: 1px solid #555555;
                    border-radius: 8px;
                    background-color: #2d2d30;
                }

                QTabWidget::pane {
                    border: 1px solid #555555;
                }

                QTabBar::tab {
                    background: #2d2d30;
                    color: #ffffff;
                    padding: 8px;
                    border: 1px solid #555555;
                }

                QTabBar::tab:selected {
                    background: #3e3e42;
                    font-weight: bold;
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
                    background-color: #ffffff;
                    color: #000000;
                }

                QLabel {
                    color: #000000;
                }

                QLabel#CardTitle {
                    font-size:13px;
                    font-weight:bold;
                    color:#444444;
                }

                QLabel#CardValue {
                    font-size:17px;
                    font-weight:bold;
                    color:#000000;
                }

                QPushButton {
                    background-color: #f5f5f5;
                    color: #000000;
                    border: 1px solid #cccccc;
                    border-radius: 5px;
                    padding: 6px;
                }

                QPushButton:hover {
                    background-color: #e8e8e8;
                }

                QTableWidget {
                    background-color: #ffffff;
                    color: #000000;
                    gridline-color: #dddddd;
                    alternate-background-color: #f8f9fa;
                }

                QHeaderView::section {
                    background-color: #f1f1f1;
                    color: #000000;
                    padding: 5px;
                    border: 1px solid #cccccc;
                }

                QFrame#SummaryCard {
                    border: 1px solid #cccccc;
                    border-radius: 8px;
                    background-color: #f8f9fa;
                }

                QTabWidget::pane {
                    border: 1px solid #cccccc;
                }

                QTabBar::tab {
                    background: #f5f5f5;
                    color: #000000;
                    padding: 8px;
                    border: 1px solid #cccccc;
                }

                QTabBar::tab:selected {
                    background: #ffffff;
                    font-weight: bold;
                }
            """)

            self.heading.setStyleSheet("""
                font-size:24px;
                font-weight:bold;
                padding:10px;
                color:#000000;
            """)

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

        return f"{float(value):,.2f}"

    def format_quantity(self, value):

        value = float(value)

        if value.is_integer():
            return f"{int(value):,}"

        return f"{value:,.4f}"
