"""
Mutual Fund Manager Window
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
    QFileDialog,
)

from services.settings_service import load_settings
from services.mutual_fund_service import (
    get_all_mutual_funds,
    add_new_mutual_fund,
    update_existing_mutual_fund,
    remove_mutual_fund,
    update_mutual_fund_nav,
)
from services.mutual_fund_nav_import_service import import_mutual_fund_nav_csv

from mutual_fund_dialog import MutualFundDialog
from mutual_fund_nav_dialog import MutualFundNavDialog


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


class MutualFundWindow(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.settings = load_settings()
        self.summary_labels = {}
        self.funds = []

        self.setWindowTitle("Mutual Funds Manager")
        self.resize(1200, 680)

        self.init_ui()
        self.load_funds()

    def init_ui(self):

        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        heading = QLabel("🏦 Mutual Funds Manager")
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
            ("Total Investment", "investment"),
            ("Current Value", "current"),
            ("Profit / Loss", "profit"),
            ("Profit %", "profit_percent"),
            ("Total Funds", "funds"),
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

        btn_add = QPushButton("➕ Add Mutual Fund")
        btn_edit = QPushButton("✏ Edit Mutual Fund")
        btn_delete = QPushButton("🗑 Delete Mutual Fund")
        btn_nav_update = QPushButton("✍ Manual NAV Update")
        btn_nav_csv = QPushButton("📈 Update NAV CSV")
        btn_refresh = QPushButton("🔄 Refresh")
        btn_close = QPushButton("❌ Close")

        buttons = [
            btn_add,
            btn_edit,
            btn_delete,
            btn_nav_update,
            btn_nav_csv,
            btn_refresh,
            btn_close,
        ]

        for btn in buttons:
            btn.setMinimumHeight(38)
            layout.addWidget(btn)

        btn_add.clicked.connect(self.open_add_dialog)
        btn_edit.clicked.connect(self.open_edit_dialog)
        btn_delete.clicked.connect(self.delete_selected_fund)
        btn_nav_update.clicked.connect(self.manual_nav_update)
        btn_nav_csv.clicked.connect(self.update_nav_from_csv)
        btn_refresh.clicked.connect(self.load_funds)
        btn_close.clicked.connect(self.close)

        return layout

    def create_search_bar(self):

        layout = QHBoxLayout()

        search_label = QLabel("Search Fund:")
        search_label.setStyleSheet("""
            font-size:14px;
            font-weight:bold;
        """)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(
            "Type fund name e.g. KMIF, MIF, Meezan"
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

        table.setColumnCount(8)

        table.setHorizontalHeaderLabels([
            "Fund",
            "Units",
            "Average NAV",
            "Current NAV",
            "Investment Value",
            "Current Value",
            "Profit / Loss",
            "Profit %",
        ])

        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setSelectionMode(QAbstractItemView.SingleSelection)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.setAlternatingRowColors(True)
        table.setSortingEnabled(True)

        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.verticalHeader().setVisible(False)

        return table

    def load_funds(self):

        try:
            self.funds = get_all_mutual_funds()

            self.search_input.clear()

            self.display_funds(self.funds)
            self.update_summary_cards(self.funds)
            self.update_search_result_label(self.funds)

        except Exception as e:

            QMessageBox.critical(
                self,
                "Error",
                f"Failed to load mutual funds.\n\n{str(e)}"
            )

    def display_funds(self, funds):

        self.table.setSortingEnabled(False)

        self.table.setRowCount(0)
        self.table.setRowCount(len(funds))

        for row, item in enumerate(funds):

            fund = str(item["fund"])
            units = float(item["units"])
            avg_nav = float(item["avg_nav"])
            current_nav = float(item["current_nav"])
            investment_value = float(item["investment_value"])
            current_value = float(item["current_value"])
            profit_loss = float(item["profit_loss"])
            profit_percent = float(item["profit_percent"])

            row_items = [
                self.create_table_item(fund, fund),
                self.create_table_item(self.format_quantity(units), units),
                self.create_table_item(self.format_number(avg_nav), avg_nav),
                self.create_table_item(self.format_number(current_nav), current_nav),
                self.create_table_item(self.format_currency(investment_value), investment_value),
                self.create_table_item(self.format_currency(current_value), current_value),
                self.create_table_item(self.format_currency(profit_loss), profit_loss),
                self.create_table_item(f"{profit_percent:.2f}%", profit_percent),
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

    def apply_filter(self):

        search_text = self.search_input.text().strip().lower()

        if not search_text:

            filtered_funds = self.funds

        else:

            filtered_funds = []

            for item in self.funds:

                fund_name = str(item["fund"]).lower()

                if search_text in fund_name:
                    filtered_funds.append(item)

        self.display_funds(filtered_funds)
        self.update_summary_cards(filtered_funds)
        self.update_search_result_label(filtered_funds)

    def clear_search(self):

        self.search_input.clear()

        self.display_funds(self.funds)
        self.update_summary_cards(self.funds)
        self.update_search_result_label(self.funds)

    def update_search_result_label(self, funds):

        self.search_result_label.setText(
            f"Showing: {len(funds)} / {len(self.funds)}"
        )

    def update_summary_cards(self, funds):

        total_investment = 0
        total_current = 0

        for fund in funds:

            total_investment += float(fund["investment_value"])
            total_current += float(fund["current_value"])

        profit_loss = total_current - total_investment

        if total_investment > 0:
            profit_percent = (profit_loss / total_investment) * 100
        else:
            profit_percent = 0

        self.summary_labels["investment"].setText(
            self.format_currency(total_investment)
        )

        self.summary_labels["current"].setText(
            self.format_currency(total_current)
        )

        self.summary_labels["profit"].setText(
            self.format_currency(profit_loss)
        )

        self.summary_labels["profit_percent"].setText(
            f"{profit_percent:.2f}%"
        )

        self.summary_labels["funds"].setText(
            str(len(funds))
        )

        if profit_loss >= 0:
            color = "green"
        else:
            color = "red"

        self.summary_labels["profit"].setStyleSheet(f"""
            font-size:17px;
            font-weight:bold;
            color:{color};
        """)

        self.summary_labels["profit_percent"].setStyleSheet(f"""
            font-size:17px;
            font-weight:bold;
            color:{color};
        """)

    def open_add_dialog(self):

        dialog = MutualFundDialog(self)

        if dialog.exec():

            try:
                data = dialog.get_data()

                add_new_mutual_fund(
                    data["fund"],
                    data["units"],
                    data["avg_nav"],
                    data["current_nav"]
                )

                QMessageBox.information(
                    self,
                    "Success",
                    "Mutual fund added successfully."
                )

                self.load_funds()

            except Exception as e:

                QMessageBox.critical(
                    self,
                    "Error",
                    str(e)
                )

    def open_edit_dialog(self):

        selected = self.get_selected_fund()

        if not selected:
            QMessageBox.warning(
                self,
                "No Selection",
                "Please select a mutual fund to edit."
            )
            return

        dialog = MutualFundDialog(self, selected)

        if dialog.exec():

            try:
                data = dialog.get_data()

                update_existing_mutual_fund(
                    data["fund"],
                    data["units"],
                    data["avg_nav"],
                    data["current_nav"]
                )

                QMessageBox.information(
                    self,
                    "Success",
                    "Mutual fund updated successfully."
                )

                self.load_funds()

            except Exception as e:

                QMessageBox.critical(
                    self,
                    "Error",
                    str(e)
                )

    def manual_nav_update(self):

        selected = self.get_selected_fund()

        if not selected:
            QMessageBox.warning(
                self,
                "No Selection",
                "Please select a mutual fund to update NAV."
            )
            return

        dialog = MutualFundNavDialog(selected, self)

        if dialog.exec():

            try:
                data = dialog.get_data()

                update_mutual_fund_nav(
                    data["fund"],
                    data["current_nav"]
                )

                QMessageBox.information(
                    self,
                    "Success",
                    f"{data['fund']} current NAV updated successfully."
                )

                self.load_funds()

            except Exception as e:

                QMessageBox.critical(
                    self,
                    "NAV Update Error",
                    str(e)
                )

    def update_nav_from_csv(self):

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Mutual Fund NAV CSV File",
            "",
            "CSV Files (*.csv)"
        )

        if not file_path:
            return

        try:
            result = import_mutual_fund_nav_csv(file_path)

            message = (
                "Mutual Fund NAV CSV Update Completed.\n\n"
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
                "NAV CSV Update Result",
                message
            )

            self.load_funds()

        except Exception as e:

            QMessageBox.critical(
                self,
                "NAV CSV Update Error",
                str(e)
            )

    def delete_selected_fund(self):

        selected = self.get_selected_fund()

        if not selected:
            QMessageBox.warning(
                self,
                "No Selection",
                "Please select a mutual fund to delete."
            )
            return

        fund = selected["fund"]

        confirm = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete {fund}?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if confirm != QMessageBox.Yes:
            return

        try:
            remove_mutual_fund(fund)

            QMessageBox.information(
                self,
                "Success",
                f"{fund} deleted successfully."
            )

            self.load_funds()

        except Exception as e:

            QMessageBox.critical(
                self,
                "Error",
                str(e)
            )

    def get_selected_fund(self):

        selected_row = self.table.currentRow()

        if selected_row < 0:
            return None

        fund_item = self.table.item(selected_row, 0)
        units_item = self.table.item(selected_row, 1)
        avg_nav_item = self.table.item(selected_row, 2)
        current_nav_item = self.table.item(selected_row, 3)

        if (
            fund_item is None
            or units_item is None
            or avg_nav_item is None
            or current_nav_item is None
        ):
            return None

        try:
            return {
                "fund": fund_item.text().strip(),
                "units": float(units_item.data(Qt.UserRole)),
                "avg_nav": float(avg_nav_item.data(Qt.UserRole)),
                "current_nav": float(current_nav_item.data(Qt.UserRole)),
            }

        except (ValueError, TypeError):

            QMessageBox.warning(
                self,
                "Invalid Data",
                "Selected mutual fund contains invalid numeric data."
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

        return f"{self.get_currency()} {value:,.2f}"

    def format_number(self, value):

        return f"{value:,.4f}"

    def format_quantity(self, value):

        return f"{value:,.4f}"
