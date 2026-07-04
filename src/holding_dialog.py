"""
Holding Dialog
"""

from PySide6.QtWidgets import (
    QDialog,
    QFormLayout,
    QLineEdit,
    QPushButton,
    QHBoxLayout,
    QVBoxLayout,
    QMessageBox
)


class HoldingDialog(QDialog):

    def __init__(self, parent=None, holding=None):

        if isinstance(parent, dict) and holding is None:
            holding = parent
            parent = None

        super().__init__(parent)

        self.setWindowTitle("Add Holding")
        self.setMinimumWidth(350)

        self.symbol = QLineEdit()
        self.shares = QLineEdit()
        self.avg_price = QLineEdit()
        self.current_price = QLineEdit()

        form = QFormLayout()
        form.addRow("Symbol", self.symbol)
        form.addRow("Shares", self.shares)
        form.addRow("Average Price", self.avg_price)
        form.addRow("Current Price", self.current_price)

        self.btn_save = QPushButton("Save")
        self.btn_cancel = QPushButton("Cancel")

        self.btn_save.clicked.connect(self.validate_data)
        self.btn_cancel.clicked.connect(self.reject)

        buttons = QHBoxLayout()
        buttons.addWidget(self.btn_save)
        buttons.addWidget(self.btn_cancel)

        layout = QVBoxLayout()
        layout.addLayout(form)
        layout.addLayout(buttons)

        self.setLayout(layout)

        if holding:
            self.setWindowTitle("Edit Holding")

            self.symbol.setText(str(holding["symbol"]))
            self.symbol.setEnabled(False)

            self.shares.setText(str(holding["shares"]))
            self.avg_price.setText(str(holding["avg_price"]))
            self.current_price.setText(str(holding["current_price"]))

    def validate_data(self):

        symbol = self.symbol.text().strip().upper()
        shares = self.shares.text().strip()
        avg_price = self.avg_price.text().strip()
        current_price = self.current_price.text().strip()

        if not symbol:
            QMessageBox.warning(self, "Validation Error", "Please enter Symbol.")
            return

        try:
            shares = float(shares)
            avg_price = float(avg_price)
            current_price = float(current_price)

        except ValueError:
            QMessageBox.warning(
                self,
                "Validation Error",
                "Shares, Average Price and Current Price must be numeric."
            )
            return

        if shares <= 0:
            QMessageBox.warning(self, "Validation Error", "Shares must be greater than zero.")
            return

        if avg_price <= 0:
            QMessageBox.warning(self, "Validation Error", "Average Price must be greater than zero.")
            return

        if current_price <= 0:
            QMessageBox.warning(self, "Validation Error", "Current Price must be greater than zero.")
            return

        self.accept()

    def get_data(self):

        return {
            "symbol": self.symbol.text().strip().upper(),
            "shares": float(self.shares.text().strip()),
            "avg_price": float(self.avg_price.text().strip()),
            "current_price": float(self.current_price.text().strip())
        }