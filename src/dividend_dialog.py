"""
Dividend Dialog
Add / Edit dividend income records.
"""

from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QDialog,
    QFormLayout,
    QLineEdit,
    QPushButton,
    QHBoxLayout,
    QVBoxLayout,
    QMessageBox,
    QDateEdit
)


class DividendDialog(QDialog):

    def __init__(self, parent=None, dividend_data=None):

        if isinstance(parent, dict) and dividend_data is None:
            dividend_data = parent
            parent = None

        super().__init__(parent)

        self.dividend_data = dividend_data
        self.dividend_id = None

        self.setWindowTitle("Add Dividend")
        self.setMinimumWidth(450)

        self.symbol = QLineEdit()
        self.shares = QLineEdit()
        self.dividend_per_share = QLineEdit()
        self.tax_amount = QLineEdit()
        self.payment_date = QDateEdit()
        self.remarks = QLineEdit()

        self.gross_amount = QLineEdit()
        self.net_amount = QLineEdit()

        self.gross_amount.setReadOnly(True)
        self.net_amount.setReadOnly(True)

        self.payment_date.setCalendarPopup(True)
        self.payment_date.setDisplayFormat("yyyy-MM-dd")
        self.payment_date.setDate(QDate.currentDate())

        self.tax_amount.setText("0")

        self.btn_save = QPushButton("Save")
        self.btn_cancel = QPushButton("Cancel")

        self.setup_ui()
        self.connect_signals()

        if dividend_data:
            self.load_data(dividend_data)

        self.update_calculation()

    def setup_ui(self):

        form = QFormLayout()

        form.addRow("Stock Symbol", self.symbol)
        form.addRow("Shares", self.shares)
        form.addRow("Dividend Per Share", self.dividend_per_share)
        form.addRow("Tax Amount", self.tax_amount)
        form.addRow("Payment Date", self.payment_date)
        form.addRow("Remarks", self.remarks)
        form.addRow("Gross Amount", self.gross_amount)
        form.addRow("Net Amount", self.net_amount)

        buttons = QHBoxLayout()
        buttons.addWidget(self.btn_save)
        buttons.addWidget(self.btn_cancel)

        layout = QVBoxLayout()
        layout.addLayout(form)
        layout.addLayout(buttons)

        self.setLayout(layout)

    def connect_signals(self):

        self.shares.textChanged.connect(self.update_calculation)
        self.dividend_per_share.textChanged.connect(self.update_calculation)
        self.tax_amount.textChanged.connect(self.update_calculation)

        self.btn_save.clicked.connect(self.validate_data)
        self.btn_cancel.clicked.connect(self.reject)

    def load_data(self, dividend_data):

        self.setWindowTitle("Edit Dividend")

        self.dividend_id = dividend_data.get("id")

        self.symbol.setText(str(dividend_data.get("symbol", "")))
        self.shares.setText(str(dividend_data.get("shares", "")))
        self.dividend_per_share.setText(
            str(dividend_data.get("dividend_per_share", ""))
        )
        self.tax_amount.setText(str(dividend_data.get("tax_amount", 0)))
        self.remarks.setText(str(dividend_data.get("remarks", "")))

        date_text = str(dividend_data.get("payment_date", ""))

        date_value = QDate.fromString(date_text, "yyyy-MM-dd")

        if date_value.isValid():
            self.payment_date.setDate(date_value)
        else:
            self.payment_date.setDate(QDate.currentDate())

    def update_calculation(self):

        try:
            shares = float(self.shares.text().strip())
            dividend_per_share = float(
                self.dividend_per_share.text().strip()
            )

            tax_text = self.tax_amount.text().strip()

            if not tax_text:
                tax_amount = 0
            else:
                tax_amount = float(tax_text)

            gross_amount = shares * dividend_per_share
            net_amount = gross_amount - tax_amount

            self.gross_amount.setText(f"{gross_amount:,.2f}")
            self.net_amount.setText(f"{net_amount:,.2f}")

        except ValueError:

            self.gross_amount.setText("0.00")
            self.net_amount.setText("0.00")

    def validate_data(self):

        symbol = self.symbol.text().strip().upper()
        shares = self.shares.text().strip()
        dividend_per_share = self.dividend_per_share.text().strip()
        tax_amount = self.tax_amount.text().strip()

        if not symbol:
            QMessageBox.warning(
                self,
                "Validation Error",
                "Please enter stock symbol."
            )
            return

        if not shares:
            QMessageBox.warning(
                self,
                "Validation Error",
                "Please enter shares."
            )
            return

        if not dividend_per_share:
            QMessageBox.warning(
                self,
                "Validation Error",
                "Please enter dividend per share."
            )
            return

        if tax_amount == "":
            tax_amount = "0"
            self.tax_amount.setText("0")

        try:
            shares = float(shares)
            dividend_per_share = float(dividend_per_share)
            tax_amount = float(tax_amount)

        except ValueError:
            QMessageBox.warning(
                self,
                "Validation Error",
                "Shares, Dividend Per Share and Tax Amount must be numeric."
            )
            return

        if shares <= 0:
            QMessageBox.warning(
                self,
                "Validation Error",
                "Shares must be greater than zero."
            )
            return

        if dividend_per_share <= 0:
            QMessageBox.warning(
                self,
                "Validation Error",
                "Dividend per share must be greater than zero."
            )
            return

        if tax_amount < 0:
            QMessageBox.warning(
                self,
                "Validation Error",
                "Tax amount cannot be negative."
            )
            return

        gross_amount = shares * dividend_per_share
        net_amount = gross_amount - tax_amount

        if net_amount < 0:
            QMessageBox.warning(
                self,
                "Validation Error",
                "Tax amount cannot be greater than gross amount."
            )
            return

        self.accept()

    def get_data(self):

        data = {
            "symbol": self.symbol.text().strip().upper(),
            "shares": float(self.shares.text().strip()),
            "dividend_per_share": float(
                self.dividend_per_share.text().strip()
            ),
            "tax_amount": float(
                self.tax_amount.text().strip()
                if self.tax_amount.text().strip()
                else 0
            ),
            "payment_date": self.payment_date.date().toString("yyyy-MM-dd"),
            "remarks": self.remarks.text().strip()
        }

        if self.dividend_id:
            data["id"] = self.dividend_id

        return data