"""
Mutual Fund Dialog
Add / Edit mutual fund holdings.
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


class MutualFundDialog(QDialog):

    def __init__(self, parent=None, fund_data=None):

        if isinstance(parent, dict) and fund_data is None:
            fund_data = parent
            parent = None

        super().__init__(parent)

        self.setWindowTitle("Add Mutual Fund")
        self.setMinimumWidth(400)

        self.fund = QLineEdit()
        self.units = QLineEdit()
        self.avg_nav = QLineEdit()
        self.current_nav = QLineEdit()

        form = QFormLayout()
        form.addRow("Fund Name", self.fund)
        form.addRow("Units", self.units)
        form.addRow("Average NAV", self.avg_nav)
        form.addRow("Current NAV", self.current_nav)

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

        if fund_data:
            self.setWindowTitle("Edit Mutual Fund")

            self.fund.setText(str(fund_data["fund"]))
            self.fund.setEnabled(False)

            self.units.setText(str(fund_data["units"]))
            self.avg_nav.setText(str(fund_data["avg_nav"]))
            self.current_nav.setText(str(fund_data["current_nav"]))

    def validate_data(self):

        fund = self.fund.text().strip()
        units = self.units.text().strip()
        avg_nav = self.avg_nav.text().strip()
        current_nav = self.current_nav.text().strip()

        if not fund:
            QMessageBox.warning(
                self,
                "Validation Error",
                "Please enter fund name."
            )
            return

        try:
            units = float(units)
            avg_nav = float(avg_nav)
            current_nav = float(current_nav)

        except ValueError:
            QMessageBox.warning(
                self,
                "Validation Error",
                "Units, Average NAV and Current NAV must be numeric."
            )
            return

        if units <= 0:
            QMessageBox.warning(
                self,
                "Validation Error",
                "Units must be greater than zero."
            )
            return

        if avg_nav <= 0:
            QMessageBox.warning(
                self,
                "Validation Error",
                "Average NAV must be greater than zero."
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
            "units": float(self.units.text().strip()),
            "avg_nav": float(self.avg_nav.text().strip()),
            "current_nav": float(self.current_nav.text().strip())
        }