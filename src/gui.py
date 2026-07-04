import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QBrush
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
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

from services.report_service import create_reports
from services.portfolio_service import (
    get_all_holdings,
    add_new_holding,
    update_existing_holding,
    remove_holding,
)
from holding_dialog import HoldingDialog


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


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Zain Wealth Manager Pro")
        self.resize(1400, 750)

        self.summary_labels = {}
        self.all_holdings = []

        self.init_ui()
        self.load_portfolio()

    def init_ui(self):

        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QHBoxLayout()
        central.setLayout(main_layout)

        sidebar = self.create_sidebar()

        content_layout = QVBoxLayout()

        heading = QLabel("📊 Portfolio Manager")
        heading.setAlignment(Qt.AlignCenter)
        heading.setStyleSheet("""
            font-size:22px;
            font-weight:bold;
            padding:10px;
        """)

        summary_layout = self.create_summary_cards()
        search_layout = self.create_search_bar()
        self.table = self.create_table()

        content_layout.addWidget(heading)
        content_layout.addLayout(summary_layout)
        content_layout.addLayout(search_layout)
        content_layout.addWidget(self.table)

        main_layout.addLayout(sidebar, 1)
        main_layout.addLayout(content_layout, 5)

        self.statusBar().showMessage("Ready")

    def create_sidebar(self):

        sidebar = QVBoxLayout()

        title = QLabel("💼 Zain Wealth Manager Pro")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            font-size:20px;
            font-weight:bold;
            padding:15px;
        """)

        sidebar.addWidget(title)

        buttons = [
            ("📊 Dashboard", None),
            ("➕ Add Holding", self.open_add_dialog),
            ("✏ Edit Holding", self.open_edit_dialog),
            ("🗑 Delete Holding", self.delete_selected_holding),
            ("🔄 Refresh", self.load_portfolio),
            ("📂 Import Portfolio", None),
            ("📈 Update Prices", None),
            ("📄 Excel / PDF Report", self.generate_reports),
            ("💾 Backup", None),
            ("♻ Restore", None),
            ("⚙ Settings", None),
            ("❌ Exit", self.close),
        ]

        for text, action in buttons:

            btn = QPushButton(text)
            btn.setMinimumHeight(45)

            if action:
                btn.clicked.connect(action)
            else:
                btn.setEnabled(False)

            sidebar.addWidget(btn)

        sidebar.addStretch()

        return sidebar

    def create_summary_cards(self):

        layout = QHBoxLayout()

        cards = [
            ("Total Investment", "investment"),
            ("Current Value", "current"),
            ("Profit / Loss", "profit"),
            ("Profit %", "profit_percent"),
            ("Total Holdings", "holdings"),
        ]

        for title, key in cards:

            card = self.create_card(title, key)
            layout.addWidget(card)

        return layout

    def create_card(self, title, key):

        card = QFrame()
        card.setFrameShape(QFrame.StyledPanel)
        card.setMinimumHeight(95)

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

    def create_search_bar(self):

        layout = QHBoxLayout()

        search_label = QLabel("Search Symbol:")
        search_label.setStyleSheet("""
            font-size:14px;
            font-weight:bold;
        """)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Type symbol e.g. FFC, MEBL, SYS")
        self.search_input.setMinimumHeight(35)
        self.search_input.textChanged.connect(self.apply_filter)

        clear_btn = QPushButton("Clear")
        clear_btn.setMinimumHeight(35)
        clear_btn.clicked.connect(self.clear_search)

        layout.addWidget(search_label)
        layout.addWidget(self.search_input)
        layout.addWidget(clear_btn)

        return layout

    def create_table(self):

        table = QTableWidget()

        table.setColumnCount(9)

        table.setHorizontalHeaderLabels([
            "Symbol",
            "Shares",
            "Average Price",
            "Current Price",
            "Investment Value",
            "Current Value",
            "Profit / Loss",
            "Profit %",
            "Allocation %",
        ])

        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setSelectionMode(QAbstractItemView.SingleSelection)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.setAlternatingRowColors(True)
        table.setSortingEnabled(True)

        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.verticalHeader().setVisible(False)

        return table

    def load_portfolio(self):

        try:
            self.all_holdings = get_all_holdings()

            self.display_holdings(self.all_holdings)
            self.update_summary_cards(self.all_holdings)

            self.statusBar().showMessage(
                f"Portfolio loaded successfully. Total Holdings: {len(self.all_holdings)}"
            )

        except Exception as e:

            QMessageBox.critical(
                self,
                "Error",
                f"Failed to load portfolio.\n\n{str(e)}"
            )

    def display_holdings(self, holdings):

        self.table.setSortingEnabled(False)

        total_current_value = self.calculate_total_current_value(self.all_holdings)

        self.table.setRowCount(0)
        self.table.setRowCount(len(holdings))

        for row, item in enumerate(holdings):

            symbol = str(item["symbol"]).upper()
            shares = float(item["shares"])
            avg_price = float(item["avg_price"])
            current_price = float(item["current_price"])

            investment_value = shares * avg_price
            current_value = shares * current_price
            profit_loss = current_value - investment_value

            if investment_value > 0:
                profit_percent = (profit_loss / investment_value) * 100
            else:
                profit_percent = 0

            if total_current_value > 0:
                allocation_percent = (current_value / total_current_value) * 100
            else:
                allocation_percent = 0

            row_items = [
                self.create_table_item(symbol, symbol),
                self.create_table_item(self.format_quantity(shares), shares),
                self.create_table_item(self.format_number(avg_price), avg_price),
                self.create_table_item(self.format_number(current_price), current_price),
                self.create_table_item(self.format_currency(investment_value), investment_value),
                self.create_table_item(self.format_currency(current_value), current_value),
                self.create_table_item(self.format_currency(profit_loss), profit_loss),
                self.create_table_item(f"{profit_percent:.2f}%", profit_percent),
                self.create_table_item(f"{allocation_percent:.2f}%", allocation_percent),
            ]

            for column, table_item in enumerate(row_items):

                table_item.setTextAlignment(Qt.AlignCenter)

                if column in [6, 7]:

                    if profit_loss >= 0:
                        table_item.setForeground(QBrush(QColor("green")))
                    else:
                        table_item.setForeground(QBrush(QColor("red")))

                self.table.setItem(row, column, table_item)

        self.table.setSortingEnabled(True)

    def calculate_total_current_value(self, holdings):

        total = 0

        for item in holdings:

            shares = float(item["shares"])
            current_price = float(item["current_price"])

            total += shares * current_price

        return total

    def create_table_item(self, text, value):

        item = SortableTableWidgetItem(text, value)
        item.setData(Qt.UserRole, value)

        return item

    def apply_filter(self):

        search_text = self.search_input.text().strip().upper()

        if not search_text:

            filtered_holdings = self.all_holdings

        else:

            filtered_holdings = []

            for item in self.all_holdings:

                symbol = str(item["symbol"]).upper()

                if search_text in symbol:
                    filtered_holdings.append(item)

        self.display_holdings(filtered_holdings)

        self.statusBar().showMessage(
            f"Filtered Holdings: {len(filtered_holdings)} / {len(self.all_holdings)}"
        )

    def clear_search(self):

        self.search_input.clear()
        self.display_holdings(self.all_holdings)

        self.statusBar().showMessage(
            f"Search cleared. Total Holdings: {len(self.all_holdings)}"
        )

    def update_summary_cards(self, holdings):

        total_investment = 0
        current_value = 0

        for item in holdings:

            shares = float(item["shares"])
            avg_price = float(item["avg_price"])
            current_price = float(item["current_price"])

            total_investment += shares * avg_price
            current_value += shares * current_price

        profit = current_value - total_investment

        if total_investment > 0:
            profit_percent = (profit / total_investment) * 100
        else:
            profit_percent = 0

        self.summary_labels["investment"].setText(
            self.format_currency(total_investment)
        )

        self.summary_labels["current"].setText(
            self.format_currency(current_value)
        )

        self.summary_labels["profit"].setText(
            self.format_currency(profit)
        )

        self.summary_labels["profit_percent"].setText(
            f"{profit_percent:.2f}%"
        )

        self.summary_labels["holdings"].setText(
            str(len(holdings))
        )

        if profit >= 0:
            self.summary_labels["profit"].setStyleSheet("""
                font-size:17px;
                font-weight:bold;
                color:green;
            """)
            self.summary_labels["profit_percent"].setStyleSheet("""
                font-size:17px;
                font-weight:bold;
                color:green;
            """)
        else:
            self.summary_labels["profit"].setStyleSheet("""
                font-size:17px;
                font-weight:bold;
                color:red;
            """)
            self.summary_labels["profit_percent"].setStyleSheet("""
                font-size:17px;
                font-weight:bold;
                color:red;
            """)

    def format_quantity(self, value):

        if float(value).is_integer():
            return f"{int(value):,}"

        return f"{value:,.2f}"

    def format_number(self, value):

        return f"{value:,.2f}"

    def format_currency(self, value):

        return f"PKR {value:,.2f}"

    def generate_reports(self):

        try:
            create_reports()

            QMessageBox.information(
                self,
                "Success",
                "Excel and PDF Reports Generated Successfully!"
            )

            self.statusBar().showMessage(
                "Reports generated successfully."
            )

        except Exception as e:

            QMessageBox.critical(
                self,
                "Error",
                str(e)
            )

    def open_add_dialog(self):

        dialog = HoldingDialog(self)

        if dialog.exec():

            try:
                data = dialog.get_data()

                add_new_holding(
                    data["symbol"],
                    data["shares"],
                    data["avg_price"],
                    data["current_price"]
                )

                QMessageBox.information(
                    self,
                    "Success",
                    "Holding added successfully."
                )

                self.load_portfolio()

            except Exception as e:

                QMessageBox.critical(
                    self,
                    "Error",
                    str(e)
                )

    def open_edit_dialog(self):

        selected = self.get_selected_holding()

        if not selected:
            QMessageBox.warning(
                self,
                "No Selection",
                "Please select a holding to edit."
            )
            return

        dialog = HoldingDialog(self, selected)

        if dialog.exec():

            try:
                data = dialog.get_data()

                update_existing_holding(
                    data["symbol"],
                    data["shares"],
                    data["avg_price"],
                    data["current_price"]
                )

                QMessageBox.information(
                    self,
                    "Success",
                    "Holding updated successfully."
                )

                self.load_portfolio()

            except Exception as e:

                QMessageBox.critical(
                    self,
                    "Error",
                    str(e)
                )

    def delete_selected_holding(self):

        selected = self.get_selected_holding()

        if not selected:
            QMessageBox.warning(
                self,
                "No Selection",
                "Please select a holding to delete."
            )
            return

        symbol = selected["symbol"]

        confirm = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete {symbol}?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if confirm != QMessageBox.Yes:
            return

        try:
            remove_holding(symbol)

            QMessageBox.information(
                self,
                "Success",
                f"{symbol} deleted successfully."
            )

            self.load_portfolio()

        except Exception as e:

            QMessageBox.critical(
                self,
                "Error",
                str(e)
            )

    def get_selected_holding(self):

        selected_row = self.table.currentRow()

        if selected_row < 0:
            return None

        symbol_item = self.table.item(selected_row, 0)
        shares_item = self.table.item(selected_row, 1)
        avg_price_item = self.table.item(selected_row, 2)
        current_price_item = self.table.item(selected_row, 3)

        if (
            symbol_item is None
            or shares_item is None
            or avg_price_item is None
            or current_price_item is None
        ):
            return None

        try:
            shares_value = shares_item.data(Qt.UserRole)
            avg_price_value = avg_price_item.data(Qt.UserRole)
            current_price_value = current_price_item.data(Qt.UserRole)

            return {
                "symbol": symbol_item.text().strip().upper(),
                "shares": float(shares_value),
                "avg_price": float(avg_price_value),
                "current_price": float(current_price_value),
            }

        except (ValueError, TypeError):
            QMessageBox.warning(
                self,
                "Invalid Data",
                "Selected holding contains invalid numeric data."
            )
            return None


if __name__ == "__main__":

    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())