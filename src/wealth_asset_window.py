"""
Wealth Asset Window
Main Phase 10 window for:
- Provident Fund
- Pension / MTPF
- Bank Cash
- Other Assets
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
    QTabWidget,
)

from services.settings_service import load_settings
from services.currency_service import format_currency as format_display_currency
from services.currency_service import get_conversion_note
from services.wealth_asset_service import (
    initialize_wealth_assets,
    get_all_wealth_assets,
    get_all_wealth_asset_transactions,
    get_phase10_dashboard_summary,
    add_new_wealth_asset,
    update_existing_wealth_asset,
    remove_wealth_asset,
    add_new_wealth_asset_transaction,
    remove_wealth_asset_transaction,
)

from wealth_asset_dialog import WealthAssetDialog
from wealth_asset_transaction_dialog import WealthAssetTransactionDialog


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


class WealthAssetWindow(QWidget):
    """
    Wealth Assets Manager window.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        initialize_wealth_assets()

        self.settings = load_settings()
        self.summary_labels = {}
        self.all_assets = []
        self.all_transactions = []

        self.setWindowTitle("PF, Pension & Bank Cash Manager")
        self.resize(1350, 820)

        self.init_ui()
        self.apply_theme()
        self.load_data()

    def init_ui(self):

        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        self.heading = QLabel("🏦 PF, Pension & Bank Cash Manager")
        self.heading.setAlignment(Qt.AlignCenter)

        summary_layout = self.create_summary_cards()
        button_layout = self.create_buttons()
        search_layout = self.create_search_bar()

        self.conversion_note = QLabel("")
        self.conversion_note.setAlignment(Qt.AlignCenter)
        self.conversion_note.setMinimumHeight(28)

        self.tabs = QTabWidget()

        self.assets_table = self.create_assets_table()
        self.transactions_table = self.create_transactions_table()

        self.tabs.addTab(self.assets_table, "Wealth Assets")
        self.tabs.addTab(self.transactions_table, "Transactions")

        main_layout.addWidget(self.heading)
        main_layout.addLayout(summary_layout)
        main_layout.addWidget(self.conversion_note)
        main_layout.addLayout(button_layout)
        main_layout.addLayout(search_layout)
        main_layout.addWidget(self.tabs)

    def create_summary_cards(self):

        main_layout = QVBoxLayout()

        first_row = QHBoxLayout()
        second_row = QHBoxLayout()

        first_row_cards = [
            ("Provident Fund", "provident_fund"),
            ("Pension / MTPF", "pension_mtpf"),
            ("Bank Cash", "bank_cash"),
            ("Other Assets", "other_assets"),
        ]

        second_row_cards = [
            ("Total Manual Wealth", "total_balance"),
            ("Monthly Contribution", "monthly_contribution"),
            ("Employer Contribution", "employer_contribution"),
            ("Total Monthly Saving", "total_monthly_saving"),
        ]

        for title, key in first_row_cards:
            first_row.addWidget(self.create_card(title, key))

        for title, key in second_row_cards:
            second_row.addWidget(self.create_card(title, key))

        main_layout.addLayout(first_row)
        main_layout.addLayout(second_row)

        return main_layout

    def create_card(self, title, key):

        card = QFrame()
        card.setObjectName("SummaryCard")
        card.setFrameShape(QFrame.StyledPanel)
        card.setMinimumHeight(88)

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

        btn_add_asset = QPushButton("➕ Add Asset")
        btn_edit_asset = QPushButton("✏ Edit Asset")
        btn_delete_asset = QPushButton("🗑 Delete Asset")
        btn_add_transaction = QPushButton("➕ Add Transaction")
        btn_delete_transaction = QPushButton("🗑 Delete Transaction")
        btn_refresh = QPushButton("🔄 Refresh")
        btn_close = QPushButton("❌ Close")

        buttons = [
            btn_add_asset,
            btn_edit_asset,
            btn_delete_asset,
            btn_add_transaction,
            btn_delete_transaction,
            btn_refresh,
            btn_close,
        ]

        for button in buttons:
            button.setMinimumHeight(38)
            layout.addWidget(button)

        btn_add_asset.clicked.connect(self.open_add_asset_dialog)
        btn_edit_asset.clicked.connect(self.open_edit_asset_dialog)
        btn_delete_asset.clicked.connect(self.delete_selected_asset)
        btn_add_transaction.clicked.connect(self.open_add_transaction_dialog)
        btn_delete_transaction.clicked.connect(self.delete_selected_transaction)
        btn_refresh.clicked.connect(self.load_data)
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
            "Search asset type, account name, institution, remarks..."
        )
        self.search_input.setMinimumHeight(35)
        self.search_input.textChanged.connect(self.apply_filter)

        clear_btn = QPushButton("Clear")
        clear_btn.setMinimumHeight(35)
        clear_btn.clicked.connect(self.clear_search)

        layout.addWidget(search_label)
        layout.addWidget(self.search_input)
        layout.addWidget(clear_btn)

        return layout

    def create_assets_table(self):

        table = QTableWidget()
        table.setColumnCount(11)

        table.setHorizontalHeaderLabels([
            "ID",
            "Asset Type",
            "Account Name",
            "Institution",
            "Current Balance",
            "Monthly Contribution",
            "Employer Contribution",
            "Start Date",
            "Last Updated",
            "Status",
            "Remarks",
        ])

        self.setup_table(table)
        table.setColumnHidden(0, True)

        return table

    def create_transactions_table(self):

        table = QTableWidget()
        table.setColumnCount(9)

        table.setHorizontalHeaderLabels([
            "ID",
            "Asset ID",
            "Asset",
            "Institution",
            "Transaction Type",
            "Amount",
            "Date",
            "Remarks",
            "Created At",
        ])

        self.setup_table(table)
        table.setColumnHidden(0, True)
        table.setColumnHidden(1, True)

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

            self.all_assets = get_all_wealth_assets()
            self.all_transactions = get_all_wealth_asset_transactions()

            self.update_summary_cards()
            self.update_conversion_note()
            self.display_assets(self.all_assets)
            self.display_transactions(self.all_transactions)
            self.apply_theme()

        except Exception as e:

            QMessageBox.critical(
                self,
                "Wealth Assets Error",
                f"Failed to load wealth assets.\n\n{str(e)}"
            )

    def update_summary_cards(self):

        summary = get_phase10_dashboard_summary()

        self.summary_labels["provident_fund"].setText(
            self.format_currency(summary["provident_fund"])
        )

        self.summary_labels["pension_mtpf"].setText(
            self.format_currency(summary["pension_mtpf"])
        )

        self.summary_labels["bank_cash"].setText(
            self.format_currency(summary["bank_cash"])
        )

        self.summary_labels["other_assets"].setText(
            self.format_currency(summary["other_assets"])
        )

        self.summary_labels["total_balance"].setText(
            self.format_currency(summary["total_balance"])
        )

        self.summary_labels["monthly_contribution"].setText(
            self.format_currency(summary["monthly_contribution"])
        )

        self.summary_labels["employer_contribution"].setText(
            self.format_currency(summary["employer_contribution"])
        )

        self.summary_labels["total_monthly_saving"].setText(
            self.format_currency(summary["total_monthly_saving"])
        )

        positive_keys = [
            "provident_fund",
            "pension_mtpf",
            "bank_cash",
            "other_assets",
            "total_balance",
            "monthly_contribution",
            "employer_contribution",
            "total_monthly_saving",
        ]

        for key in positive_keys:

            self.summary_labels[key].setStyleSheet("""
                font-size:17px;
                font-weight:bold;
                color:green;
            """)

    def update_conversion_note(self):

        try:
            self.conversion_note.setText(get_conversion_note())

        except Exception:
            self.conversion_note.setText("Base currency: PKR")

    def display_assets(self, assets):

        self.assets_table.setSortingEnabled(False)
        self.assets_table.setRowCount(0)
        self.assets_table.setRowCount(len(assets))

        for row, item in enumerate(assets):

            status = "Active"

            if int(item.get("is_active", 1)) != 1:
                status = "Inactive"

            row_items = [
                self.create_table_item(str(item["id"]), item["id"]),
                self.create_table_item(item["asset_type"], item["asset_type"]),
                self.create_table_item(item["account_name"], item["account_name"]),
                self.create_table_item(item.get("institution", ""), item.get("institution", "")),
                self.create_table_item(
                    self.format_currency(item["current_balance"]),
                    item["current_balance"]
                ),
                self.create_table_item(
                    self.format_currency(item["monthly_contribution"]),
                    item["monthly_contribution"]
                ),
                self.create_table_item(
                    self.format_currency(item["employer_contribution"]),
                    item["employer_contribution"]
                ),
                self.create_table_item(item.get("start_date", ""), item.get("start_date", "")),
                self.create_table_item(item.get("last_updated", ""), item.get("last_updated", "")),
                self.create_table_item(status, status),
                self.create_table_item(item.get("remarks", ""), item.get("remarks", "")),
            ]

            self.set_row_items(self.assets_table, row, row_items)

        self.assets_table.setSortingEnabled(True)

    def display_transactions(self, transactions):

        self.transactions_table.setSortingEnabled(False)
        self.transactions_table.setRowCount(0)
        self.transactions_table.setRowCount(len(transactions))

        for row, item in enumerate(transactions):

            asset_label = f"{item.get('asset_type', '')} - {item.get('account_name', '')}"

            row_items = [
                self.create_table_item(str(item["id"]), item["id"]),
                self.create_table_item(str(item["asset_id"]), item["asset_id"]),
                self.create_table_item(asset_label, asset_label),
                self.create_table_item(item.get("institution", ""), item.get("institution", "")),
                self.create_table_item(item["transaction_type"], item["transaction_type"]),
                self.create_table_item(
                    self.format_currency(item["amount"]),
                    item["amount"]
                ),
                self.create_table_item(item["transaction_date"], item["transaction_date"]),
                self.create_table_item(item.get("remarks", ""), item.get("remarks", "")),
                self.create_table_item(item.get("created_at", ""), item.get("created_at", "")),
            ]

            self.set_row_items(self.transactions_table, row, row_items)

        self.transactions_table.setSortingEnabled(True)

    def set_row_items(self, table, row, row_items):

        for column, table_item in enumerate(row_items):

            table_item.setTextAlignment(Qt.AlignCenter)

            value = table_item.data(Qt.UserRole)

            try:
                numeric_value = float(value)
            except (ValueError, TypeError):
                numeric_value = None

            if numeric_value is not None and numeric_value > 0:
                table_item.setForeground(QBrush(QColor("green")))

            table.setItem(row, column, table_item)

    def create_table_item(self, text, value):

        item = SortableTableWidgetItem(text, value)
        item.setData(Qt.UserRole, value)

        return item

    def apply_filter(self):

        search_text = self.search_input.text().strip().lower()

        if not search_text:
            self.display_assets(self.all_assets)
            self.display_transactions(self.all_transactions)
            return

        filtered_assets = []

        for item in self.all_assets:

            searchable_text = " ".join([
                str(item.get("asset_type", "")),
                str(item.get("account_name", "")),
                str(item.get("institution", "")),
                str(item.get("remarks", "")),
            ]).lower()

            if search_text in searchable_text:
                filtered_assets.append(item)

        filtered_transactions = []

        for item in self.all_transactions:

            searchable_text = " ".join([
                str(item.get("asset_type", "")),
                str(item.get("account_name", "")),
                str(item.get("institution", "")),
                str(item.get("transaction_type", "")),
                str(item.get("transaction_date", "")),
                str(item.get("remarks", "")),
            ]).lower()

            if search_text in searchable_text:
                filtered_transactions.append(item)

        self.display_assets(filtered_assets)
        self.display_transactions(filtered_transactions)

    def clear_search(self):

        self.search_input.clear()
        self.display_assets(self.all_assets)
        self.display_transactions(self.all_transactions)

    def open_add_asset_dialog(self):

        dialog = WealthAssetDialog(self)

        if dialog.exec():

            try:
                data = dialog.get_data()
                add_new_wealth_asset(data)

                QMessageBox.information(
                    self,
                    "Success",
                    "Wealth asset added successfully."
                )

                self.load_data()

            except Exception as e:

                QMessageBox.critical(
                    self,
                    "Add Asset Error",
                    str(e)
                )

    def open_edit_asset_dialog(self):

        selected = self.get_selected_asset()

        if not selected:
            QMessageBox.warning(
                self,
                "No Selection",
                "Please select a wealth asset to edit."
            )
            return

        dialog = WealthAssetDialog(self, selected)

        if dialog.exec():

            try:
                data = dialog.get_data()
                update_existing_wealth_asset(selected["id"], data)

                QMessageBox.information(
                    self,
                    "Success",
                    "Wealth asset updated successfully."
                )

                self.load_data()

            except Exception as e:

                QMessageBox.critical(
                    self,
                    "Edit Asset Error",
                    str(e)
                )

    def delete_selected_asset(self):

        selected = self.get_selected_asset()

        if not selected:
            QMessageBox.warning(
                self,
                "No Selection",
                "Please select a wealth asset to delete."
            )
            return

        confirm = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Delete asset '{selected['account_name']}'?\n\n"
            "Its transactions will also be deleted.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if confirm != QMessageBox.Yes:
            return

        try:
            remove_wealth_asset(selected["id"])

            QMessageBox.information(
                self,
                "Success",
                "Wealth asset deleted successfully."
            )

            self.load_data()

        except Exception as e:

            QMessageBox.critical(
                self,
                "Delete Asset Error",
                str(e)
            )

    def open_add_transaction_dialog(self):

        selected_asset = self.get_selected_asset()
        asset_id = None

        if selected_asset:
            asset_id = selected_asset["id"]

        dialog = WealthAssetTransactionDialog(self, asset_id)

        if dialog.exec():

            try:
                data = dialog.get_data()
                add_new_wealth_asset_transaction(data)

                QMessageBox.information(
                    self,
                    "Success",
                    "Transaction added successfully."
                )

                self.load_data()

            except Exception as e:

                QMessageBox.critical(
                    self,
                    "Transaction Error",
                    str(e)
                )

    def delete_selected_transaction(self):

        selected = self.get_selected_transaction()

        if not selected:
            QMessageBox.warning(
                self,
                "No Selection",
                "Please select a transaction to delete."
            )
            return

        confirm = QMessageBox.question(
            self,
            "Confirm Delete",
            "Delete selected transaction?\n\n"
            "Balance will not be reversed automatically.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if confirm != QMessageBox.Yes:
            return

        try:
            remove_wealth_asset_transaction(
                selected["id"],
                reverse_balance=False
            )

            QMessageBox.information(
                self,
                "Success",
                "Transaction deleted successfully."
            )

            self.load_data()

        except Exception as e:

            QMessageBox.critical(
                self,
                "Delete Transaction Error",
                str(e)
            )

    def get_selected_asset(self):

        selected_row = self.assets_table.currentRow()

        if selected_row < 0:
            return None

        id_item = self.assets_table.item(selected_row, 0)

        if id_item is None:
            return None

        asset_id = id_item.data(Qt.UserRole)

        for asset in self.all_assets:

            if int(asset["id"]) == int(asset_id):
                return asset

        return None

    def get_selected_transaction(self):

        selected_row = self.transactions_table.currentRow()

        if selected_row < 0:
            return None

        id_item = self.transactions_table.item(selected_row, 0)

        if id_item is None:
            return None

        transaction_id = id_item.data(Qt.UserRole)

        for transaction in self.all_transactions:

            if int(transaction["id"]) == int(transaction_id):
                return transaction

        return None

    def format_currency(self, value):

        try:
            return format_display_currency(value)

        except Exception:
            return f"PKR {float(value):,.2f}"

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

            self.conversion_note.setStyleSheet("""
                font-size:12px;
                color:#dddddd;
                padding:4px;
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

            self.conversion_note.setStyleSheet("""
                font-size:12px;
                color:#555555;
                padding:4px;
            """)
