"""
Wealth Asset Dialog
Dialog to add/edit Phase 10 wealth assets:
- Provident Fund
- Pension / MTPF
- Bank Cash
- Other Assets
"""

from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QGridLayout,
    QLabel,
    QComboBox,
    QLineEdit,
    QDoubleSpinBox,
    QTextEdit,
    QDateEdit,
    QCheckBox,
    QDialogButtonBox,
    QMessageBox,
    QGroupBox,
)

from services.wealth_asset_service import get_asset_types


class WealthAssetDialog(QDialog):
    """
    Add/Edit wealth asset dialog.
    """

    def __init__(self, parent=None, asset_data=None):
        super().__init__(parent)

        self.asset_data = asset_data

        if self.asset_data:
            self.setWindowTitle("Edit Wealth Asset")
        else:
            self.setWindowTitle("Add Wealth Asset")

        self.resize(650, 560)

        self.init_ui()
        self.load_asset_data()

    def init_ui(self):

        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        form_group = QGroupBox("Asset Details")
        form_layout = QGridLayout()
        form_group.setLayout(form_layout)

        self.asset_type_combo = QComboBox()
        self.asset_type_combo.setMinimumHeight(34)
        self.asset_type_combo.addItems(get_asset_types())

        self.account_name_input = QLineEdit()
        self.account_name_input.setMinimumHeight(34)
        self.account_name_input.setPlaceholderText("Example: Akhuwat Provident Fund")

        self.institution_input = QLineEdit()
        self.institution_input.setMinimumHeight(34)
        self.institution_input.setPlaceholderText("Example: Akhuwat / Meezan / HBL")

        self.current_balance_spin = QDoubleSpinBox()
        self.current_balance_spin.setRange(0, 999999999999)
        self.current_balance_spin.setDecimals(2)
        self.current_balance_spin.setSingleStep(1000)
        self.current_balance_spin.setMinimumHeight(34)

        self.monthly_contribution_spin = QDoubleSpinBox()
        self.monthly_contribution_spin.setRange(0, 999999999999)
        self.monthly_contribution_spin.setDecimals(2)
        self.monthly_contribution_spin.setSingleStep(500)
        self.monthly_contribution_spin.setMinimumHeight(34)

        self.employer_contribution_spin = QDoubleSpinBox()
        self.employer_contribution_spin.setRange(0, 999999999999)
        self.employer_contribution_spin.setDecimals(2)
        self.employer_contribution_spin.setSingleStep(500)
        self.employer_contribution_spin.setMinimumHeight(34)

        self.start_date_edit = QDateEdit()
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setDisplayFormat("yyyy-MM-dd")
        self.start_date_edit.setDate(QDate.currentDate())
        self.start_date_edit.setMinimumHeight(34)

        self.last_updated_edit = QDateEdit()
        self.last_updated_edit.setCalendarPopup(True)
        self.last_updated_edit.setDisplayFormat("yyyy-MM-dd")
        self.last_updated_edit.setDate(QDate.currentDate())
        self.last_updated_edit.setMinimumHeight(34)

        self.active_checkbox = QCheckBox("Active")
        self.active_checkbox.setChecked(True)

        self.remarks_input = QTextEdit()
        self.remarks_input.setPlaceholderText("Optional remarks")
        self.remarks_input.setMinimumHeight(90)

        form_layout.addWidget(QLabel("Asset Type:"), 0, 0)
        form_layout.addWidget(self.asset_type_combo, 0, 1)

        form_layout.addWidget(QLabel("Account Name:"), 1, 0)
        form_layout.addWidget(self.account_name_input, 1, 1)

        form_layout.addWidget(QLabel("Institution:"), 2, 0)
        form_layout.addWidget(self.institution_input, 2, 1)

        form_layout.addWidget(QLabel("Current Balance (PKR):"), 3, 0)
        form_layout.addWidget(self.current_balance_spin, 3, 1)

        form_layout.addWidget(QLabel("Monthly Contribution (PKR):"), 4, 0)
        form_layout.addWidget(self.monthly_contribution_spin, 4, 1)

        form_layout.addWidget(QLabel("Employer Contribution (PKR):"), 5, 0)
        form_layout.addWidget(self.employer_contribution_spin, 5, 1)

        form_layout.addWidget(QLabel("Start Date:"), 6, 0)
        form_layout.addWidget(self.start_date_edit, 6, 1)

        form_layout.addWidget(QLabel("Last Updated:"), 7, 0)
        form_layout.addWidget(self.last_updated_edit, 7, 1)

        form_layout.addWidget(QLabel("Status:"), 8, 0)
        form_layout.addWidget(self.active_checkbox, 8, 1)

        form_layout.addWidget(QLabel("Remarks:"), 9, 0)
        form_layout.addWidget(self.remarks_input, 9, 1)

        note = QLabel(
            "Note: All balances are saved in PKR. "
            "Display conversion is handled from Settings."
        )
        note.setWordWrap(True)
        note.setStyleSheet("""
            color:#555555;
            font-size:12px;
            padding:4px;
        """)

        self.buttons = QDialogButtonBox(
            QDialogButtonBox.Save | QDialogButtonBox.Cancel
        )

        self.buttons.accepted.connect(self.validate_and_accept)
        self.buttons.rejected.connect(self.reject)

        main_layout.addWidget(form_group)
        main_layout.addWidget(note)
        main_layout.addWidget(self.buttons)

    def load_asset_data(self):

        if not self.asset_data:
            return

        asset_type = str(
            self.asset_data.get("asset_type", "Provident Fund")
        ).strip()

        index = self.asset_type_combo.findText(asset_type)

        if index >= 0:
            self.asset_type_combo.setCurrentIndex(index)

        self.account_name_input.setText(
            str(self.asset_data.get("account_name", ""))
        )

        self.institution_input.setText(
            str(self.asset_data.get("institution", ""))
        )

        self.current_balance_spin.setValue(
            self.safe_float(self.asset_data.get("current_balance", 0))
        )

        self.monthly_contribution_spin.setValue(
            self.safe_float(self.asset_data.get("monthly_contribution", 0))
        )

        self.employer_contribution_spin.setValue(
            self.safe_float(self.asset_data.get("employer_contribution", 0))
        )

        self.set_date_value(
            self.start_date_edit,
            self.asset_data.get("start_date", "")
        )

        self.set_date_value(
            self.last_updated_edit,
            self.asset_data.get("last_updated", "")
        )

        is_active = self.asset_data.get("is_active", 1)

        try:
            is_active = int(is_active)
        except (ValueError, TypeError):
            is_active = 1

        self.active_checkbox.setChecked(is_active == 1)

        self.remarks_input.setPlainText(
            str(self.asset_data.get("remarks", ""))
        )

    def set_date_value(self, date_edit, date_text):

        date_text = str(date_text or "").strip()

        if not date_text:
            date_edit.setDate(QDate.currentDate())
            return

        date = QDate.fromString(date_text, "yyyy-MM-dd")

        if not date.isValid():
            date = QDate.currentDate()

        date_edit.setDate(date)

    def validate_and_accept(self):

        account_name = self.account_name_input.text().strip()

        if not account_name:
            QMessageBox.warning(
                self,
                "Missing Account Name",
                "Please enter account name."
            )
            return

        current_balance = self.current_balance_spin.value()
        monthly_contribution = self.monthly_contribution_spin.value()
        employer_contribution = self.employer_contribution_spin.value()

        if current_balance < 0:
            QMessageBox.warning(
                self,
                "Invalid Balance",
                "Current balance cannot be negative."
            )
            return

        if monthly_contribution < 0:
            QMessageBox.warning(
                self,
                "Invalid Contribution",
                "Monthly contribution cannot be negative."
            )
            return

        if employer_contribution < 0:
            QMessageBox.warning(
                self,
                "Invalid Employer Contribution",
                "Employer contribution cannot be negative."
            )
            return

        self.accept()

    def get_data(self):

        is_active = 1

        if not self.active_checkbox.isChecked():
            is_active = 0

        return {
            "asset_type": self.asset_type_combo.currentText(),
            "account_name": self.account_name_input.text().strip(),
            "institution": self.institution_input.text().strip(),
            "current_balance": float(self.current_balance_spin.value()),
            "monthly_contribution": float(self.monthly_contribution_spin.value()),
            "employer_contribution": float(self.employer_contribution_spin.value()),
            "start_date": self.start_date_edit.date().toString("yyyy-MM-dd"),
            "last_updated": self.last_updated_edit.date().toString("yyyy-MM-dd"),
            "remarks": self.remarks_input.toPlainText().strip(),
            "is_active": is_active,
        }

    def safe_float(self, value):

        try:
            if value is None:
                return 0.0

            return float(value)

        except (ValueError, TypeError):
            return 0.0
