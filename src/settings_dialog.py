"""
Settings Dialog
Handles application settings UI.
"""

from PySide6.QtWidgets import (
    QDialog,
    QFormLayout,
    QLineEdit,
    QPushButton,
    QHBoxLayout,
    QVBoxLayout,
    QMessageBox,
    QComboBox,
    QCheckBox,
    QFileDialog
)

from services.settings_service import (
    load_settings,
    reset_settings
)


class SettingsDialog(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Settings")
        self.setMinimumWidth(450)

        self.settings = load_settings()

        self.currency = QComboBox()
        self.currency.addItems(["PKR", "USD"])

        self.concentration_limit = QLineEdit()

        self.backup_folder = QLineEdit()

        self.btn_browse_backup = QPushButton("Browse")

        self.theme = QComboBox()
        self.theme.addItems(["light", "dark"])

        self.auto_refresh = QCheckBox("Enable Auto Refresh")

        self.btn_save = QPushButton("Save")
        self.btn_cancel = QPushButton("Cancel")
        self.btn_reset = QPushButton("Reset Default")

        self.setup_ui()
        self.load_values()

        self.btn_save.clicked.connect(self.validate_and_accept)
        self.btn_cancel.clicked.connect(self.reject)
        self.btn_reset.clicked.connect(self.reset_default_settings)
        self.btn_browse_backup.clicked.connect(self.browse_backup_folder)

    def setup_ui(self):

        form = QFormLayout()

        form.addRow("Currency", self.currency)
        form.addRow("Concentration Alert Limit (%)", self.concentration_limit)

        backup_layout = QHBoxLayout()
        backup_layout.addWidget(self.backup_folder)
        backup_layout.addWidget(self.btn_browse_backup)

        form.addRow("Backup Folder", backup_layout)
        form.addRow("Theme", self.theme)
        form.addRow("", self.auto_refresh)

        buttons = QHBoxLayout()
        buttons.addWidget(self.btn_save)
        buttons.addWidget(self.btn_reset)
        buttons.addWidget(self.btn_cancel)

        layout = QVBoxLayout()
        layout.addLayout(form)
        layout.addLayout(buttons)

        self.setLayout(layout)

    def load_values(self):

        currency = str(self.settings.get("currency", "PKR"))

        currency_index = self.currency.findText(currency)

        if currency_index >= 0:
            self.currency.setCurrentIndex(currency_index)

        self.concentration_limit.setText(
            str(self.settings.get("concentration_limit", 30))
        )

        self.backup_folder.setText(
            str(self.settings.get("backup_folder", "backups"))
        )

        theme = str(self.settings.get("theme", "light"))

        theme_index = self.theme.findText(theme)

        if theme_index >= 0:
            self.theme.setCurrentIndex(theme_index)

        auto_refresh = bool(
            self.settings.get("auto_refresh", False)
        )

        self.auto_refresh.setChecked(auto_refresh)

    def browse_backup_folder(self):

        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Backup Folder",
            self.backup_folder.text().strip()
        )

        if folder:
            self.backup_folder.setText(folder)

    def validate_and_accept(self):

        concentration_limit = self.concentration_limit.text().strip()

        if not concentration_limit:
            QMessageBox.warning(
                self,
                "Validation Error",
                "Please enter concentration alert limit."
            )
            return

        try:
            concentration_limit = float(concentration_limit)

        except ValueError:
            QMessageBox.warning(
                self,
                "Validation Error",
                "Concentration alert limit must be numeric."
            )
            return

        if concentration_limit <= 0 or concentration_limit > 100:
            QMessageBox.warning(
                self,
                "Validation Error",
                "Concentration alert limit must be between 1 and 100."
            )
            return

        backup_folder = self.backup_folder.text().strip()

        if not backup_folder:
            QMessageBox.warning(
                self,
                "Validation Error",
                "Please enter backup folder."
            )
            return

        self.accept()

    def reset_default_settings(self):

        confirm = QMessageBox.question(
            self,
            "Reset Settings",
            "Are you sure you want to reset settings to default values?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if confirm != QMessageBox.Yes:
            return

        self.settings = reset_settings()

        self.load_values()

        QMessageBox.information(
            self,
            "Settings Reset",
            "Settings have been reset to default values."
        )

    def get_data(self):

        return {
            "currency": self.currency.currentText(),
            "concentration_limit": float(
                self.concentration_limit.text().strip()
            ),
            "backup_folder": self.backup_folder.text().strip(),
            "theme": self.theme.currentText(),
            "auto_refresh": self.auto_refresh.isChecked()
        }