import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QPushButton,
    QMessageBox,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QAbstractItemView,
    QHeaderView,
)

from services.report_service import create_reports
from services.portfolio_service import (
    get_all_holdings,
    add_new_holding,
    update_existing_holding,
    remove_holding,
)
from holding_dialog import HoldingDialog


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Zain Wealth Manager Pro")
        self.resize(1200, 700)

        self.init_ui()
        self.load_portfolio()

    def init_ui(self):

        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QHBoxLayout()
        central.setLayout(main_layout)

        sidebar = self.create_sidebar()
        self.table = self.create_table()

        main_layout.addLayout(sidebar, 1)
        main_layout.addWidget(self.table, 4)

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

    def create_table(self):

        table = QTableWidget()

        table.setColumnCount(4)

        table.setHorizontalHeaderLabels([
            "Symbol",
            "Shares",
            "Average Price",
            "Current Price",
        ])

        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setSelectionMode(QAbstractItemView.SingleSelection)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.setAlternatingRowColors(True)

        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.verticalHeader().setVisible(False)

        return table

    def load_portfolio(self):

        try:
            holdings = get_all_holdings()

            self.table.setRowCount(0)
            self.table.setRowCount(len(holdings))

            for row, item in enumerate(holdings):

                symbol_item = QTableWidgetItem(str(item["symbol"]))
                shares_item = QTableWidgetItem(str(item["shares"]))
                avg_price_item = QTableWidgetItem(str(item["avg_price"]))
                current_price_item = QTableWidgetItem(str(item["current_price"]))

                symbol_item.setTextAlignment(Qt.AlignCenter)
                shares_item.setTextAlignment(Qt.AlignCenter)
                avg_price_item.setTextAlignment(Qt.AlignCenter)
                current_price_item.setTextAlignment(Qt.AlignCenter)

                self.table.setItem(row, 0, symbol_item)
                self.table.setItem(row, 1, shares_item)
                self.table.setItem(row, 2, avg_price_item)
                self.table.setItem(row, 3, current_price_item)

            self.statusBar().showMessage(
                f"Portfolio loaded successfully. Total Holdings: {len(holdings)}"
            )

        except Exception as e:

            QMessageBox.critical(
                self,
                "Error",
                f"Failed to load portfolio.\n\n{str(e)}"
            )

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
            return {
                "symbol": symbol_item.text().strip().upper(),
                "shares": float(shares_item.text()),
                "avg_price": float(avg_price_item.text()),
                "current_price": float(current_price_item.text()),
            }

        except ValueError:
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