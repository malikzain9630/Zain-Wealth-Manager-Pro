"""
Wealth Asset Transaction Dialog
Dialog to add transactions for Phase 10 wealth assets.
"""

from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QGridLayout,
    QLabel,
    QComboBox,
    QDoubleSpinBox,
    QTextEdit,
    QDateEdit,
    QCheckBox,
    QDialogButtonBox,
    QMessageBox,
    QGroupBox,
)

from services.wealth_asset_service import (
    get_all_wealth_assets,
    get_transaction_types,
)


class WealthAssetTransactionDialog(QDialog):
    """
    Add wealth asset transaction dialog.
    """

    def __init__(self, parent=None, asset_id=None):
        super().__init__(parent)

        self.asset_id = asset_id
        self.assets = []

        self.setWindowTitle("Add Wealth Asset Transaction")
        self.resize(620, 430)

        self.init_ui()
        self.load_assets()

    def init_ui(self):

        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        form_group = QGroupBox("Transaction Details")
        form_layout = QGridLayout()
        form_group.setLayout(form_layout)

        self.asset_combo = QComboBox()
        self.asset_combo.setMinimumHeight(34)

        self.transaction_type_combo = QComboBox()
        self.transaction_type_combo.setMinimumHeight(34)
        self.transaction_type_combo.addItems(get_transaction_types())

        self.amount_spin = QDoubleSpinBox()
        self.amount_spin.setRange(0.01, 999999999999)
        self.amount_spin.setDecimals(2)
        self.amount_spin.setSingleStep(1000)
        self.amount_spin.setMinimumHeight(34)

        self.transaction_date_edit = QDateEdit()
        self.transaction_date_edit.setCalendarPopup(True)
        self.transaction_date_edit.setDisplayFormat("yyyy-MM-dd")
        self.transaction_date_edit.setDate(QDate.currentDate())
        self.transaction_date_edit.setMinimumHeight(34)

        self.update_balance_checkbox = QCheckBox("Update asset balance automatically")
        self.update_balance_checkbox.setChecked(True)

        self.remarks_input = QTextEdit()
        self.remarks_input.setPlaceholderText("Optional remarks")
        self.remarks_input.setMinimumHeight(90)

        form_layout.addWidget(QLabel("Asset:"), 0, 0)
        form_layout.addWidget(self.asset_combo, 0, 1)

        form_layout.addWidget(QLabel("Transaction Type:"), 1, 0)
        form_layout.addWidget(self.transaction_type_combo, 1, 1)

        form_layout.addWidget(QLabel("Amount (PKR):"), 2, 0)
        form_layout.addWidget(self.amount_spin, 2, 1)

        form_layout.addWidget(QLabel("Transaction Date:"), 3, 0)
        form_layout.addWidget(self.transaction_date_edit, 3, 1)

        form_layout.addWidget(QLabel("Balance Update:"), 4, 0)
        form_layout.addWidget(self.update_balance_checkbox, 4, 1)

        form_layout.addWidget(QLabel("Remarks:"), 5, 0)
        form_layout.addWidget(self.remarks_input, 5, 1)

        note = QLabel(
            "Note: Amounts are saved in PKR. "
            "Contribution, Employer Contribution, Profit and Adjustment increase balance. "
            "Withdrawal decreases balance."
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

    def load_assets(self):

        self.assets = get_all_wealth_assets()

        self.asset_combo.clear()

        if not self.assets:
            self.asset_combo.addItem("No active assets found", None)
            return

        selected_index = 0

        for index, asset in enumerate(self.assets):

            asset_id = asset["id"]
            asset_type = asset["asset_type"]
            account_name = asset["account_name"]
            institution = asset.get("institution", "")

            if institution:
                label = f"{asset_type} - {account_name} ({institution})"
            else:
                label = f"{asset_type} - {account_name}"

            self.asset_combo.addItem(label, asset_id)

            if self.asset_id is not None and int(asset_id) == int(self.asset_id):
                selected_index = index

        self.asset_combo.setCurrentIndex(selected_index)

    def validate_and_accept(self):

        selected_asset_id = self.asset_combo.currentData()

        if selected_asset_id is None:
            QMessageBox.warning(
                self,
                "No Asset Found",
                "Please add a wealth asset first."
            )
            return

        amount = self.amount_spin.value()

        if amount <= 0:
            QMessageBox.warning(
                self,
                "Invalid Amount",
                "Transaction amount must be greater than zero."
            )
            return

        self.accept()

    def get_data(self):

        return {
            "asset_id": self.asset_combo.currentData(),
            "transaction_type": self.transaction_type_combo.currentText(),
            "amount": float(self.amount_spin.value()),
            "transaction_date": self.transaction_date_edit.date().toString("yyyy-MM-dd"),
            "remarks": self.remarks_input.toPlainText().strip(),
            "update_balance": self.update_balance_checkbox.isChecked(),
        }
