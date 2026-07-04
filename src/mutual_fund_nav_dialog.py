"""
Mutual Fund NAV Update Dialog
Manual current NAV update for selected mutual fund.
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


class MutualFundNavDialog(QDialog):

    def __init__(self, fund_data, parent=None):
        super().__init__(parent)

        self.fund_data = fund_data

        self.setWindowTitle("Update Current NAV")
        self.setMinimumWidth(350)

        self.fund = QLineEdit()
        self.current_nav = QLineEdit()

        self.fund.setText(str(fund_data["fund"]))
        self.fund.setEnabled(False)

        self.current_nav.setText(
            str(fund_data["current_nav"])
        )

        form = QFormLayout()
        form.addRow("Fund", self.fund)
        form.addRow("Current NAV", self.current_nav)

        self.btn_update = QPushButton("Update")
        self.btn_cancel = QPushButton("Cancel")

        self.btn_update.clicked.connect(self.validate_data)
        self.btn_cancel.clicked.connect(self.reject)

        buttons = QHBoxLayout()
        buttons.addWidget(self.btn_update)
        buttons.addWidget(self.btn_cancel)

        layout = QVBoxLayout()
        layout.addLayout(form)
        layout.addLayout(buttons)

        self.setLayout(layout)

    def validate_data(self):

        current_nav = self.current_nav.text().strip()

        if not current_nav:
            QMessageBox.warning(
                self,
                "Validation Error",
                "Please enter current NAV."
            )
            return

        try:
            current_nav = float(current_nav)

        except ValueError:
            QMessageBox.warning(
                self,
                "Validation Error",
                "Current NAV must be numeric."
            )
            return

        if current_nav <= 0:
            QMessageBox.warning(
                self,
                "Validation Error",
                "Current NAV must be greater than zero."
            )
            return

        self.accept()

    def get_data(self):

        return {
            "fund": self.fund.text().strip(),
            "current_nav": float(
                self.current_nav.text().strip()
            )
        }