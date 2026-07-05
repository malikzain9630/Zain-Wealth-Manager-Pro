"""
Settings Dialog
Application settings window with multi-currency support.
"""

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QComboBox,
    QDoubleSpinBox,
    QLineEdit,
    QPushButton,
    QFileDialog,
    QDialogButtonBox,
    QGroupBox,
    QScrollArea,
    QWidget,
    QMessageBox,
)

from services.settings_service import (
    load_settings,
    SUPPORTED_CURRENCIES,
    DEFAULT_EXCHANGE_RATES,
)


CURRENCY_NAMES = {
    "PKR": "Pakistani Rupee",
    "USD": "US Dollar",
    "EUR": "Euro",
    "GBP": "British Pound",
    "SAR": "Saudi Riyal",
    "AED": "UAE Dirham",
    "CAD": "Canadian Dollar",
    "AUD": "Australian Dollar",
    "JPY": "Japanese Yen",
    "CNY": "Chinese Yuan",
}


class SettingsDialog(QDialog):
    """
    Settings dialog for app preferences.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.settings = load_settings()
        self.rate_inputs = {}

        self.setWindowTitle("Settings")
        self.resize(650, 650)

        self.init_ui()
        self.load_current_values()

    def init_ui(self):

        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        heading = QLabel("⚙ Settings")
        heading.setStyleSheet("""
            font-size:22px;
            font-weight:bold;
            padding:8px;
        """)

        main_layout.addWidget(heading)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        container = QWidget()
        container_layout = QVBoxLayout()
        container.setLayout(container_layout)

        container_layout.addWidget(self.create_general_group())
        container_layout.addWidget(self.create_currency_group())
        container_layout.addWidget(self.create_exchange_rates_group())
        container_layout.addStretch()

        scroll.setWidget(container)
        main_layout.addWidget(scroll)

        self.buttons = QDialogButtonBox(
            QDialogButtonBox.Save | QDialogButtonBox.Cancel
        )

        self.buttons.accepted.connect(self.validate_and_accept)
        self.buttons.rejected.connect(self.reject)

        main_layout.addWidget(self.buttons)

    def create_general_group(self):

        group = QGroupBox("General Settings")
        layout = QGridLayout()
        group.setLayout(layout)

        theme_label = QLabel("Theme:")
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["light", "dark"])
        self.theme_combo.setMinimumHeight(34)

        concentration_label = QLabel("Concentration Limit (%):")
        self.concentration_spin = QDoubleSpinBox()
        self.concentration_spin.setRange(1, 100)
        self.concentration_spin.setDecimals(2)
        self.concentration_spin.setSingleStep(1)
        self.concentration_spin.setMinimumHeight(34)

        backup_label = QLabel("Backup Folder:")
        self.backup_input = QLineEdit()
        self.backup_input.setMinimumHeight(34)

        browse_btn = QPushButton("Browse")
        browse_btn.setMinimumHeight(34)
        browse_btn.clicked.connect(self.browse_backup_folder)

        backup_layout = QHBoxLayout()
        backup_layout.addWidget(self.backup_input)
        backup_layout.addWidget(browse_btn)

        layout.addWidget(theme_label, 0, 0)
        layout.addWidget(self.theme_combo, 0, 1)

        layout.addWidget(concentration_label, 1, 0)
        layout.addWidget(self.concentration_spin, 1, 1)

        layout.addWidget(backup_label, 2, 0)
        layout.addLayout(backup_layout, 2, 1)

        return group

    def create_currency_group(self):

        group = QGroupBox("Display Currency")
        layout = QGridLayout()
        group.setLayout(layout)

        currency_label = QLabel("Display Currency:")

        self.currency_combo = QComboBox()
        self.currency_combo.setMinimumHeight(34)

        for currency_code in SUPPORTED_CURRENCIES:

            currency_name = CURRENCY_NAMES.get(currency_code, currency_code)
            self.currency_combo.addItem(
                f"{currency_code} - {currency_name}",
                currency_code
            )

        note = QLabel(
            "Database values remain saved in PKR. "
            "Selected currency is used only for display/report conversion."
        )
        note.setWordWrap(True)
        note.setStyleSheet("""
            color:#555555;
            font-size:12px;
            padding:4px;
        """)

        layout.addWidget(currency_label, 0, 0)
        layout.addWidget(self.currency_combo, 0, 1)
        layout.addWidget(note, 1, 0, 1, 2)

        return group

    def create_exchange_rates_group(self):

        group = QGroupBox("Exchange Rates to PKR")
        layout = QGridLayout()
        group.setLayout(layout)

        info = QLabel(
            "Enter rates as: 1 foreign currency unit = X PKR. "
            "Example: 1 USD = 280 PKR."
        )
        info.setWordWrap(True)
        info.setStyleSheet("""
            color:#555555;
            font-size:12px;
            padding:4px;
        """)

        layout.addWidget(info, 0, 0, 1, 3)

        row = 1

        pkr_label = QLabel("PKR:")
        pkr_value = QLabel("1.0000")
        pkr_note = QLabel("Base Currency")

        layout.addWidget(pkr_label, row, 0)
        layout.addWidget(pkr_value, row, 1)
        layout.addWidget(pkr_note, row, 2)

        row += 1

        for currency_code in SUPPORTED_CURRENCIES:

            if currency_code == "PKR":
                continue

            currency_name = CURRENCY_NAMES.get(currency_code, currency_code)

            label = QLabel(f"{currency_code}:")
            rate_input = QDoubleSpinBox()
            rate_input.setRange(0.0001, 1000000)
            rate_input.setDecimals(4)
            rate_input.setSingleStep(1)
            rate_input.setMinimumHeight(32)

            note = QLabel(f"1 {currency_code} = PKR | {currency_name}")

            layout.addWidget(label, row, 0)
            layout.addWidget(rate_input, row, 1)
            layout.addWidget(note, row, 2)

            self.rate_inputs[currency_code] = rate_input

            row += 1

        reset_btn = QPushButton("Reset Default Rates")
        reset_btn.setMinimumHeight(34)
        reset_btn.clicked.connect(self.reset_default_rates)

        layout.addWidget(reset_btn, row, 1)

        return group

    def load_current_values(self):

        theme = str(
            self.settings.get("theme", "light")
        ).strip().lower()

        if theme not in ["light", "dark"]:
            theme = "light"

        self.theme_combo.setCurrentText(theme)

        try:
            concentration_limit = float(
                self.settings.get("concentration_limit", 30)
            )

        except (ValueError, TypeError):
            concentration_limit = 30

        self.concentration_spin.setValue(concentration_limit)

        self.backup_input.setText(
            str(self.settings.get("backup_folder", ""))
        )

        selected_currency = str(
            self.settings.get("currency", "PKR")
        ).strip().upper()

        currency_index = self.currency_combo.findData(selected_currency)

        if currency_index >= 0:
            self.currency_combo.setCurrentIndex(currency_index)

        exchange_rates = self.settings.get("exchange_rates", {})

        if not isinstance(exchange_rates, dict):
            exchange_rates = {}

        # Legacy support.
        legacy_usd_rate = self.settings.get("usd_to_pkr_rate", None)

        for currency_code, input_widget in self.rate_inputs.items():

            rate = exchange_rates.get(
                currency_code,
                DEFAULT_EXCHANGE_RATES.get(currency_code, 1)
            )

            if currency_code == "USD" and legacy_usd_rate:
                rate = legacy_usd_rate

            try:
                rate = float(rate)

            except (ValueError, TypeError):
                rate = DEFAULT_EXCHANGE_RATES.get(currency_code, 1)

            if rate <= 0:
                rate = DEFAULT_EXCHANGE_RATES.get(currency_code, 1)

            input_widget.setValue(rate)

    def browse_backup_folder(self):

        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Backup Folder",
            self.backup_input.text().strip()
        )

        if folder:
            self.backup_input.setText(folder)

    def reset_default_rates(self):

        confirm = QMessageBox.question(
            self,
            "Reset Exchange Rates",
            "Do you want to reset all exchange rates to default values?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if confirm != QMessageBox.Yes:
            return

        for currency_code, input_widget in self.rate_inputs.items():

            input_widget.setValue(
                DEFAULT_EXCHANGE_RATES.get(currency_code, 1)
            )

    def validate_and_accept(self):

        backup_folder = self.backup_input.text().strip()

        if not backup_folder:
            QMessageBox.warning(
                self,
                "Missing Backup Folder",
                "Please select a backup folder."
            )
            return

        for currency_code, input_widget in self.rate_inputs.items():

            if input_widget.value() <= 0:

                QMessageBox.warning(
                    self,
                    "Invalid Exchange Rate",
                    f"Exchange rate for {currency_code} must be greater than zero."
                )
                return

        self.accept()

    def get_data(self):

        selected_currency = self.currency_combo.currentData()

        exchange_rates = {
            "PKR": 1.0
        }

        for currency_code, input_widget in self.rate_inputs.items():

            exchange_rates[currency_code] = float(input_widget.value())

        return {
            "currency": selected_currency,
            "theme": self.theme_combo.currentText(),
            "concentration_limit": float(self.concentration_spin.value()),
            "backup_folder": self.backup_input.text().strip(),
            "exchange_rates": exchange_rates,
            # Legacy key kept so old code remains safe.
            "usd_to_pkr_rate": exchange_rates.get("USD", 280.0),
        }
