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
)

from services.report_service import create_reports
from services.portfolio_service import get_all_holdings


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Zain Wealth Manager Pro")
        self.resize(1200, 700)

        # ================= Main Widget =================

        central = QWidget()
        self.setCentralWidget(central)

        layout = QHBoxLayout()
        central.setLayout(layout)

        # ================= Sidebar =================

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
            "📊 Dashboard",
            "📂 Import Portfolio",
            "📈 Update Prices",
            "📄 Excel Report",
            "📑 PDF Report",
            "💾 Backup",
            "♻ Restore",
            "⚙ Settings",
            "❌ Exit",
        ]

        for text in buttons:

            btn = QPushButton(text)
            btn.setMinimumHeight(45)

            if text == "📄 Excel Report":
                btn.clicked.connect(self.generate_excel)

            elif text == "❌ Exit":
                btn.clicked.connect(self.close)

            sidebar.addWidget(btn)

        sidebar.addStretch()

        # ================= Portfolio Table =================

        self.table = QTableWidget()

        self.table.setColumnCount(4)

        self.table.setHorizontalHeaderLabels([
            "Symbol",
            "Shares",
            "Average Price",
            "Current Price"
        ])

        # Layout

        layout.addLayout(sidebar, 1)
        layout.addWidget(self.table, 4)

        self.load_portfolio()

    # ==================================================

    def generate_excel(self):

        try:

            create_reports()

            QMessageBox.information(
                self,
                "Success",
                "Excel & PDF Reports Generated Successfully!"
            )

        except Exception as e:

            QMessageBox.critical(
                self,
                "Error",
                str(e)
            )

    # ==================================================

    def load_portfolio(self):

        holdings = get_all_holdings()

        self.table.setRowCount(len(holdings))

        for row, item in enumerate(holdings):

            self.table.setItem(
                row,
                0,
                QTableWidgetItem(str(item["symbol"]))
            )

            self.table.setItem(
                row,
                1,
                QTableWidgetItem(str(item["shares"]))
            )

            self.table.setItem(
                row,
                2,
                QTableWidgetItem(str(item["avg_price"]))
            )

            self.table.setItem(
                row,
                3,
                QTableWidgetItem(str(item["current_price"]))
            )


if __name__ == "__main__":

    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())