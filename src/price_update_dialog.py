"""
Price Update Dialog
Manual current price update for selected holding.
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


class PriceUpdateDialog(QDialog):

    def __init__(self, holding, parent=None):
        super().__init__(parent)

        self.holding = holding

        self.setWindowTitle("Update Current Price")
        self.setMinimumWidth(350)

        self.symbol = QLineEdit()
        self.current_price = QLineEdit()

        self.symbol.setText(str(holding["symbol"]))
        self.symbol.setEnabled(False)

        self.current_price.setText(
            str(holding["current_price"])
        )

        form = QFormLayout()
        form.addRow("Symbol", self.symbol)
        form.addRow("Current Price", self.current_price)

        self.btn_save = QPushButton("Update")
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

    def validate_data(self):

        current_price = self.current_price.text().strip()

        if not current_price:
            QMessageBox.warning(
                self,
                "Validation Error",
                "Please enter current price."
            )
            return

        try:
            current_price = float(current_price)

        except ValueError:
            QMessageBox.warning(
                self,
                "Validation Error",
                "Current price must be numeric."
            )
            return

        if current_price <= 0:
            QMessageBox.warning(
                self,
                "Validation Error",
                "Current price must be greater than zero."
            )
            return

        self.accept()

    def get_data(self):

        return {
            "symbol": self.symbol.text().strip().upper(),
            "current_price": float(
                self.current_price.text().strip()
            )
        }