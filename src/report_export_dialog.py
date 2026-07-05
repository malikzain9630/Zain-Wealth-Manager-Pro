"""
Report Export Dialog
Allows user to choose:
- Excel/PDF formats
- Combined overall report
- Section-wise separate reports
- Output folder
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
    QGroupBox,
    QGridLayout,
)


class ReportExportDialog(QDialog):
    """
    Dialog for report export options.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Report Export Options")
        self.resize(720, 610)

        self.section_checkboxes = {}

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
            "Select report format, report mode and optional section-wise reports."
        )
        info.setStyleSheet("""
            font-size:13px;
            padding:4px;
        """)

        format_group = QGroupBox("Report Format")
        format_layout = QVBoxLayout()
        format_group.setLayout(format_layout)

        self.excel_checkbox = QCheckBox("Generate Excel Report")
        self.pdf_checkbox = QCheckBox("Generate PDF Report")

        self.excel_checkbox.setChecked(True)
        self.pdf_checkbox.setChecked(True)

        self.excel_checkbox.setMinimumHeight(30)
        self.pdf_checkbox.setMinimumHeight(30)

        format_layout.addWidget(self.excel_checkbox)
        format_layout.addWidget(self.pdf_checkbox)

        mode_group = QGroupBox("Report Mode")
        mode_layout = QVBoxLayout()
        mode_group.setLayout(mode_layout)

        self.combined_checkbox = QCheckBox("Generate Combined Overall Report")
        self.sectionwise_checkbox = QCheckBox("Generate Section-wise Separate Reports")

        self.combined_checkbox.setChecked(True)
        self.sectionwise_checkbox.setChecked(False)

        self.combined_checkbox.setMinimumHeight(30)
        self.sectionwise_checkbox.setMinimumHeight(30)

        mode_layout.addWidget(self.combined_checkbox)
        mode_layout.addWidget(self.sectionwise_checkbox)

        section_group = QGroupBox("Section-wise Report Selection")
        section_layout = QGridLayout()
        section_group.setLayout(section_layout)

        sections = [
            ("overall", "Overall Summary"),
            ("psx", "PSX Portfolio"),
            ("mutual_funds", "Mutual Funds"),
            ("dividends", "Dividends"),
            ("wealth_assets", "Wealth Assets"),
            ("wealth_projection", "Wealth Projection"),
            ("charts", "Charts"),
        ]

        for index, (key, title) in enumerate(sections):

            checkbox = QCheckBox(title)
            checkbox.setChecked(True)
            checkbox.setMinimumHeight(28)

            row = index // 2
            col = index % 2

            section_layout.addWidget(checkbox, row, col)
            self.section_checkboxes[key] = checkbox

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

        note = QLabel(
            "Note: Section-wise option creates separate files for selected sections. "
            "Combined option creates one full overall report."
        )
        note.setWordWrap(True)
        note.setStyleSheet("""
            font-size:12px;
            color:#555555;
            padding:4px;
        """)

        self.buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )

        self.buttons.accepted.connect(self.validate_and_accept)
        self.buttons.rejected.connect(self.reject)

        main_layout.addWidget(heading)
        main_layout.addWidget(info)
        main_layout.addWidget(format_group)
        main_layout.addWidget(mode_group)
        main_layout.addWidget(section_group)
        main_layout.addWidget(folder_label)
        main_layout.addLayout(folder_layout)
        main_layout.addWidget(note)
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

        if (
            not self.combined_checkbox.isChecked()
            and not self.sectionwise_checkbox.isChecked()
        ):
            QMessageBox.warning(
                self,
                "No Report Mode Selected",
                "Please select Combined Report or Section-wise Reports."
            )
            return

        if self.sectionwise_checkbox.isChecked():

            selected_sections = self.get_selected_sections()

            if not selected_sections:
                QMessageBox.warning(
                    self,
                    "No Section Selected",
                    "Please select at least one section for section-wise reports."
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

    def get_selected_sections(self):

        selected = []

        for key, checkbox in self.section_checkboxes.items():

            if checkbox.isChecked():
                selected.append(key)

        return selected

    def get_data(self):

        return {
            "generate_excel": self.excel_checkbox.isChecked(),
            "generate_pdf": self.pdf_checkbox.isChecked(),
            "generate_combined": self.combined_checkbox.isChecked(),
            "generate_section_wise": self.sectionwise_checkbox.isChecked(),
            "selected_sections": self.get_selected_sections(),
            "output_folder": self.folder_input.text().strip(),
        }
