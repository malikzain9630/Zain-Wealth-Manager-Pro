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
    QFileDialog,
)

from services.report_service import create_reports
from services.portfolio_service import (
    get_all_holdings,
    add_new_holding,
    update_existing_holding,
    remove_holding,
)
from services.backup_service import create_backup, restore_backup
from services.import_service import import_portfolio_csv
from services.price_service import import_price_csv, update_single_price
from services.settings_service import load_settings, update_settings
from holding_dialog import HoldingDialog
from price_update_dialog import PriceUpdateDialog
from settings_dialog import SettingsDialog
from mutual_fund_window import MutualFundWindow
from charts_window import ChartsWindow
from dividend_window import DividendWindow
from dividend_charts_window import DividendChartsWindow
from dividend_yield_window import DividendYieldWindow
from services.mutual_fund_service import get_mutual_fund_summary


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
        self.resize(1450, 780)

        self.summary_labels = {}
        self.all_holdings = []
        self.settings = load_settings()
        self.mutual_fund_window = None
        self.charts_window = None
        self.dividend_window = None
        self.dividend_charts_window = None
        self.dividend_yield_window = None

        self.init_ui()
        self.apply_theme()
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

        combined_summary_heading = QLabel("🌐 Overall Wealth Summary")
        combined_summary_heading.setAlignment(Qt.AlignCenter)
        combined_summary_heading.setStyleSheet("""
            font-size:16px;
            font-weight:bold;
            padding:6px;
        """)

        combined_summary_layout = self.create_combined_summary_cards()

        self.concentration_alert = QLabel("")
        self.concentration_alert.setAlignment(Qt.AlignCenter)
        self.concentration_alert.setMinimumHeight(35)

        search_layout = self.create_search_bar()
        self.table = self.create_table()

        content_layout.addWidget(heading)
        content_layout.addLayout(summary_layout)
        content_layout.addWidget(combined_summary_heading)
        content_layout.addLayout(combined_summary_layout)
        content_layout.addWidget(self.concentration_alert)
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
            ("📂 Import Portfolio", self.import_portfolio),
            ("📈 Update Prices CSV", self.update_prices),
            ("✍ Manual Price Update", self.manual_price_update),
            ("🏦 Mutual Funds", self.open_mutual_funds),
            ("📈 Charts", self.open_charts),
            ("💰 Dividends", self.open_dividends),
            ("📊 Dividend Charts", self.open_dividend_charts),
            ("💸 Dividend Yield", self.open_dividend_yield),
            ("📄 Excel / PDF Report", self.generate_reports),
            ("💾 Backup", self.backup_database),
            ("♻ Restore", self.restore_database),
            ("⚙ Settings", self.open_settings),
            ("❌ Exit", self.close),
        ]

        for text, action in buttons:

            btn = QPushButton(text)
            btn.setMinimumHeight(42)

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

    def create_combined_summary_cards(self):

        layout = QHBoxLayout()

        cards = [
            ("PSX Current Value", "combined_psx_current"),
            ("MF Current Value", "combined_mf_current"),
            ("Total Investment", "combined_investment"),
            ("Total Current Value", "combined_current"),
            ("Total Profit / Loss", "combined_profit"),
            ("Total Profit %", "combined_profit_percent"),
        ]

        for title, key in cards:

            card = self.create_card(title, key)
            layout.addWidget(card)

        return layout

    def create_card(self, title, key):

        card = QFrame()
        card.setObjectName("SummaryCard")
        card.setFrameShape(QFrame.StyledPanel)
        card.setMinimumHeight(95)

        layout = QVBoxLayout()
        card.setLayout(layout)

        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            font-size:13px;
            font-weight:bold;
        """)

        value_label = QLabel("0")
        value_label.setAlignment(Qt.AlignCenter)
        value_label.setStyleSheet("""
            font-size:17px;
            font-weight:bold;
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
            self.update_combined_summary_cards(self.all_holdings)
            self.update_concentration_alert(self.all_holdings)

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

    def get_concentration_limit(self):

        try:
            return float(
                self.settings.get("concentration_limit", 30)
            )

        except (ValueError, TypeError):
            return 30.0

    def update_concentration_alert(self, holdings):

        limit = self.get_concentration_limit()

        if not holdings:

            self.concentration_alert.setText(
                "ℹ No holdings available for concentration analysis."
            )

            self.set_alert_style("neutral")

            return

        total_current_value = self.calculate_total_current_value(holdings)

        if total_current_value <= 0:

            self.concentration_alert.setText(
                "ℹ Portfolio value is zero. Concentration analysis is not available."
            )

            self.set_alert_style("neutral")

            return

        highest_symbol = ""
        highest_allocation = 0

        for item in holdings:

            symbol = str(item["symbol"]).upper()
            shares = float(item["shares"])
            current_price = float(item["current_price"])

            current_value = shares * current_price
            allocation = (current_value / total_current_value) * 100

            if allocation > highest_allocation:
                highest_allocation = allocation
                highest_symbol = symbol

        if highest_allocation >= limit:

            self.concentration_alert.setText(
                f"⚠ Concentration Alert: {highest_symbol} is {highest_allocation:.2f}% "
                f"of your PSX portfolio. Limit: {limit:.0f}%."
            )

            self.set_alert_style("warning")

        else:

            self.concentration_alert.setText(
                f"✅ Portfolio concentration looks balanced. Highest holding: "
                f"{highest_symbol} at {highest_allocation:.2f}%. Limit: {limit:.0f}%."
            )

            self.set_alert_style("success")

    def set_alert_style(self, alert_type):

        if alert_type == "warning":

            self.concentration_alert.setStyleSheet("""
                QLabel {
                    font-size:14px;
                    font-weight:bold;
                    color:#8a4b00;
                    background-color:#fff3cd;
                    border:1px solid #ffecb5;
                    border-radius:6px;
                    padding:6px;
                }
            """)

        elif alert_type == "success":

            self.concentration_alert.setStyleSheet("""
                QLabel {
                    font-size:14px;
                    font-weight:bold;
                    color:#0f5132;
                    background-color:#d1e7dd;
                    border:1px solid #badbcc;
                    border-radius:6px;
                    padding:6px;
                }
            """)

        else:

            self.concentration_alert.setStyleSheet("""
                QLabel {
                    font-size:14px;
                    font-weight:bold;
                    color:#555555;
                    background-color:#f1f1f1;
                    border:1px solid #dddddd;
                    border-radius:6px;
                    padding:6px;
                }
            """)

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

    def update_combined_summary_cards(self, holdings):

        psx_investment = 0
        psx_current = 0

        for item in holdings:

            shares = float(item["shares"])
            avg_price = float(item["avg_price"])
            current_price = float(item["current_price"])

            psx_investment += shares * avg_price
            psx_current += shares * current_price

        try:
            mutual_summary = get_mutual_fund_summary()

            mutual_investment = float(mutual_summary.get("total_investment", 0))
            mutual_current = float(mutual_summary.get("total_current", 0))

        except Exception:
            mutual_investment = 0
            mutual_current = 0

        combined_investment = psx_investment + mutual_investment
        combined_current = psx_current + mutual_current
        combined_profit = combined_current - combined_investment

        if combined_investment > 0:
            combined_profit_percent = (combined_profit / combined_investment) * 100
        else:
            combined_profit_percent = 0

        self.summary_labels["combined_psx_current"].setText(
            self.format_currency(psx_current)
        )

        self.summary_labels["combined_mf_current"].setText(
            self.format_currency(mutual_current)
        )

        self.summary_labels["combined_investment"].setText(
            self.format_currency(combined_investment)
        )

        self.summary_labels["combined_current"].setText(
            self.format_currency(combined_current)
        )

        self.summary_labels["combined_profit"].setText(
            self.format_currency(combined_profit)
        )

        self.summary_labels["combined_profit_percent"].setText(
            f"{combined_profit_percent:.2f}%"
        )

        if combined_profit >= 0:
            color = "green"
        else:
            color = "red"

        self.summary_labels["combined_profit"].setStyleSheet(f"""
            font-size:17px;
            font-weight:bold;
            color:{color};
        """)

        self.summary_labels["combined_profit_percent"].setStyleSheet(f"""
            font-size:17px;
            font-weight:bold;
            color:{color};
        """)

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

    def get_currency(self):

        currency = str(
            self.settings.get("currency", "PKR")
        ).strip().upper()

        if not currency:
            currency = "PKR"

        return currency

    def format_currency(self, value):

        currency = self.get_currency()

        return f"{currency} {value:,.2f}"

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

    def import_portfolio(self):

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Portfolio CSV File",
            "",
            "CSV Files (*.csv)"
        )

        if not file_path:
            return

        try:
            result = import_portfolio_csv(file_path)

            message = (
                "Portfolio Import Completed.\n\n"
                f"Added: {result['added']}\n"
                f"Updated: {result['updated']}\n"
                f"Skipped: {result['skipped']}"
            )

            if result["errors"]:
                message += "\n\nErrors:\n"
                message += "\n".join(result["errors"][:10])

                if len(result["errors"]) > 10:
                    message += f"\n...and {len(result['errors']) - 10} more errors."

            QMessageBox.information(
                self,
                "Import Result",
                message
            )

            self.load_portfolio()

        except Exception as e:

            QMessageBox.critical(
                self,
                "Import Error",
                str(e)
            )

    def update_prices(self):

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Prices CSV File",
            "",
            "CSV Files (*.csv)"
        )

        if not file_path:
            return

        try:
            result = import_price_csv(file_path)

            message = (
                "Price Update Completed.\n\n"
                f"Updated: {result['updated']}\n"
                f"Skipped: {result['skipped']}"
            )

            if result["errors"]:
                message += "\n\nErrors:\n"
                message += "\n".join(result["errors"][:10])

                if len(result["errors"]) > 10:
                    message += f"\n...and {len(result['errors']) - 10} more errors."

            QMessageBox.information(
                self,
                "Price Update Result",
                message
            )

            self.load_portfolio()

        except Exception as e:

            QMessageBox.critical(
                self,
                "Price Update Error",
                str(e)
            )

    def manual_price_update(self):

        selected = self.get_selected_holding()

        if not selected:
            QMessageBox.warning(
                self,
                "No Selection",
                "Please select a holding to update price."
            )
            return

        dialog = PriceUpdateDialog(selected, self)

        if dialog.exec():

            try:
                data = dialog.get_data()

                update_single_price(
                    data["symbol"],
                    data["current_price"]
                )

                QMessageBox.information(
                    self,
                    "Success",
                    f"{data['symbol']} current price updated successfully."
                )

                self.load_portfolio()

            except Exception as e:

                QMessageBox.critical(
                    self,
                    "Price Update Error",
                    str(e)
                )

    def backup_database(self):

        try:
            backup_file = create_backup()

            QMessageBox.information(
                self,
                "Backup Created",
                f"Backup created successfully:\n\n{backup_file}"
            )

            self.statusBar().showMessage(
                "Database backup created successfully."
            )

        except Exception as e:

            QMessageBox.critical(
                self,
                "Backup Error",
                str(e)
            )

    def restore_database(self):

        confirm = QMessageBox.question(
            self,
            "Confirm Restore",
            "Restoring backup will replace current database data.\n\nDo you want to continue?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if confirm != QMessageBox.Yes:
            return

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Backup Database File",
            "",
            "Database Files (*.db *.sqlite *.sqlite3)"
        )

        if not file_path:
            return

        try:
            restored_path = restore_backup(file_path)

            QMessageBox.information(
                self,
                "Restore Completed",
                f"Database restored successfully:\n\n{restored_path}"
            )

            self.load_portfolio()

            self.statusBar().showMessage(
                "Database restored successfully."
            )

        except Exception as e:

            QMessageBox.critical(
                self,
                "Restore Error",
                str(e)
            )

    def open_mutual_funds(self):

        try:
            self.mutual_fund_window = MutualFundWindow(self)
            self.mutual_fund_window.show()

            self.statusBar().showMessage(
                "Mutual Funds Manager opened."
            )

        except Exception as e:

            QMessageBox.critical(
                self,
                "Mutual Funds Error",
                str(e)
            )

    def open_charts(self):

        try:
            self.charts_window = ChartsWindow(self)
            self.charts_window.show()

            self.statusBar().showMessage(
                "Charts & Visual Analytics opened."
            )

        except Exception as e:

            QMessageBox.critical(
                self,
                "Charts Error",
                str(e)
            )

    def open_dividends(self):

        try:
            self.dividend_window = DividendWindow(self)
            self.dividend_window.show()

            self.statusBar().showMessage(
                "Dividend & Income Tracker opened."
            )

        except Exception as e:

            QMessageBox.critical(
                self,
                "Dividend Tracker Error",
                str(e)
            )


    def open_dividend_charts(self):

        try:
            self.dividend_charts_window = DividendChartsWindow(self)
            self.dividend_charts_window.show()

            self.statusBar().showMessage(
                "Dividend Charts opened."
            )

        except Exception as e:

            QMessageBox.critical(
                self,
                "Dividend Charts Error",
                str(e)
            )


    def open_dividend_yield(self):

        try:
            self.dividend_yield_window = DividendYieldWindow(self)
            self.dividend_yield_window.show()

            self.statusBar().showMessage(
                "Dividend Yield & Passive Income Forecast opened."
            )

        except Exception as e:

            QMessageBox.critical(
                self,
                "Dividend Yield Error",
                str(e)
            )

    def open_settings(self):

        dialog = SettingsDialog(self)

        if dialog.exec():

            try:
                data = dialog.get_data()

                self.settings = update_settings(data)

                self.apply_theme()
                self.load_portfolio()

                QMessageBox.information(
                    self,
                    "Settings Saved",
                    "Settings saved successfully."
                )

                self.statusBar().showMessage(
                    "Settings updated successfully."
                )

            except Exception as e:

                QMessageBox.critical(
                    self,
                    "Settings Error",
                    str(e)
                )

    def apply_theme(self):

        theme = str(
            self.settings.get("theme", "light")
        ).strip().lower()

        if theme == "dark":

            self.setStyleSheet("""
                QMainWindow {
                    background-color: #1e1e1e;
                    color: #ffffff;
                }

                QWidget {
                    background-color: #1e1e1e;
                    color: #ffffff;
                }

                QLabel {
                    color: #ffffff;
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

                QPushButton:disabled {
                    background-color: #444444;
                    color: #888888;
                }

                QLineEdit {
                    background-color: #2d2d30;
                    color: #ffffff;
                    border: 1px solid #555555;
                    border-radius: 5px;
                    padding: 5px;
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

                QStatusBar {
                    background-color: #2d2d30;
                    color: #ffffff;
                }
            """)

        else:

            self.setStyleSheet("""
                QMainWindow {
                    background-color: #ffffff;
                    color: #000000;
                }

                QWidget {
                    background-color: #ffffff;
                    color: #000000;
                }

                QLabel {
                    color: #000000;
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

                QPushButton:disabled {
                    background-color: #eeeeee;
                    color: #999999;
                }

                QLineEdit {
                    background-color: #ffffff;
                    color: #000000;
                    border: 1px solid #cccccc;
                    border-radius: 5px;
                    padding: 5px;
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

                QStatusBar {
                    background-color: #f8f9fa;
                    color: #000000;
                }
            """)

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
