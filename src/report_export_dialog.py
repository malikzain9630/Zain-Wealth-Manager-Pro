"""
Report Export Dialog
Allows user to choose Excel/PDF report export options and output folder.
"""

from pathlib import Path

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QCheckBox,
    QLineEdit,
    QPushButton,
    QFileDialog,
    QMessageBox,
    QDialogButtonBox,
    QFrame,
)


class ReportExportDialog(QDialog):
    """
    Dialog for report export options.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Report Export Options")
        self.resize(560, 260)

        self.init_ui()

    def init_ui(self):

        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        heading = QLabel("📄 Report Export Options")
        heading.setStyleSheet("""
            font-size:20px;
            font-weight:bold;
            padding:8px;
        """)

        info = QLabel(
            "Select which report format you want to generate."
        )
        info.setStyleSheet("""
            font-size:13px;
            padding:4px;
        """)

        options_frame = QFrame()
        options_frame.setFrameShape(QFrame.StyledPanel)

        options_layout = QVBoxLayout()
        options_frame.setLayout(options_layout)

        self.excel_checkbox = QCheckBox("Generate Excel Report")
        self.pdf_checkbox = QCheckBox("Generate PDF Report")

        self.excel_checkbox.setChecked(True)
        self.pdf_checkbox.setChecked(True)

        self.excel_checkbox.setMinimumHeight(32)
        self.pdf_checkbox.setMinimumHeight(32)

        options_layout.addWidget(self.excel_checkbox)
        options_layout.addWidget(self.pdf_checkbox)

        folder_label = QLabel("Save Folder:")
        folder_label.setStyleSheet("""
            font-size:13px;
            font-weight:bold;
        """)

        folder_layout = QHBoxLayout()

        self.folder_input = QLineEdit()
        self.folder_input.setMinimumHeight(34)
        self.folder_input.setText(str(self.get_default_output_folder()))

        browse_btn = QPushButton("Browse")
        browse_btn.setMinimumHeight(34)
        browse_btn.clicked.connect(self.browse_folder)

        folder_layout.addWidget(self.folder_input)
        folder_layout.addWidget(browse_btn)

        self.buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )

        self.buttons.accepted.connect(self.validate_and_accept)
        self.buttons.rejected.connect(self.reject)

        main_layout.addWidget(heading)
        main_layout.addWidget(info)
        main_layout.addWidget(options_frame)
        main_layout.addWidget(folder_label)
        main_layout.addLayout(folder_layout)
        main_layout.addStretch()
        main_layout.addWidget(self.buttons)

    def get_default_output_folder(self):

        project_root = Path(__file__).resolve().parent.parent
        output_folder = project_root / "output"

        return output_folder

    def browse_folder(self):

        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Report Save Folder",
            self.folder_input.text().strip()
        )

        if folder:
            self.folder_input.setText(folder)

    def validate_and_accept(self):

        if (
            not self.excel_checkbox.isChecked()
            and not self.pdf_checkbox.isChecked()
        ):
            QMessageBox.warning(
                self,
                "No Report Type Selected",
                "Please select at least one report type: Excel or PDF."
            )
            return

        folder_text = self.folder_input.text().strip()

        if not folder_text:
            QMessageBox.warning(
                self,
                "Missing Save Folder",
                "Please select a save folder."
            )
            return

        try:
            folder_path = Path(folder_text)
            folder_path.mkdir(parents=True, exist_ok=True)

        except Exception as e:
            QMessageBox.critical(
                self,
                "Folder Error",
                f"Could not create or access the selected folder.\n\n{str(e)}"
            )
            return

        self.accept()

    def get_data(self):

        return {
            "generate_excel": self.excel_checkbox.isChecked(),
            "generate_pdf": self.pdf_checkbox.isChecked(),
            "output_folder": self.folder_input.text().strip(),
        }
