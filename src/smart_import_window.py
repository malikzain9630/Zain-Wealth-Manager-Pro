"""
Smart Import Center
Phase 10A - Unified Smart Import Engine

Purpose:
- One import button/window for all supported wealth files.
- Auto-detect and route data:
    PSX stocks -> Portfolio Manager
    Mutual Funds -> Mutual Funds Manager
    Pension / MTPF -> Wealth Assets Manager

Supported examples:
- CSV / Excel PSX portfolio
- Broker PDF account statement
- JS InvestPro JPG/PNG screenshot
- Al Meezan Mutual Fund / MTPF PDF statement
- Mixed PDF with PSX + Mutual Funds + MTPF sections

Safety:
- Direct import without preview is not allowed.
- User reviews rows before import.
"""

from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFileDialog,
    QMessageBox,
    QTextEdit,
    QFrame,
    QCheckBox,
    QGroupBox,
)

from services.settings_service import load_settings

from services.smart_import_service import (
    read_portfolio_file,
    get_import_summary,
    SUPPORTED_EXTENSIONS,
)

from services.portfolio_service import (
    get_all_holdings,
    add_new_holding,
    update_existing_holding,
)

from smart_import_preview_dialog import SmartImportPreviewDialog
from unified_smart_import_preview_dialog import UnifiedSmartImportPreviewDialog

try:
    from services.fund_statement_import_service import read_fund_statement_file
    FUND_IMPORT_AVAILABLE = True
except Exception:
    read_fund_statement_file = None
    FUND_IMPORT_AVAILABLE = False

try:
    from fund_statement_preview_dialog import FundStatementPreviewDialog
    FUND_PREVIEW_AVAILABLE = True
except Exception:
    FundStatementPreviewDialog = None
    FUND_PREVIEW_AVAILABLE = False

try:
    from services.mutual_fund_service import (
        get_all_mutual_funds,
        add_new_mutual_fund,
        update_existing_mutual_fund,
    )
except Exception:
    get_all_mutual_funds = None
    add_new_mutual_fund = None
    update_existing_mutual_fund = None

try:
    from services.wealth_asset_service import (
        get_all_wealth_assets,
        add_new_wealth_asset,
        update_existing_wealth_asset,
    )
except Exception:
    get_all_wealth_assets = None
    add_new_wealth_asset = None
    update_existing_wealth_asset = None

try:
    from services.currency_service import format_currency as format_display_currency
except Exception:
    def format_display_currency(value, *args, **kwargs):
        try:
            return f"PKR {float(value):,.2f}"
        except Exception:
            return "PKR 0.00"


class SmartImportWindow(QWidget):
    """
    Unified Smart Import Center.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.parent_window = parent
        self.settings = load_settings()
        self.selected_file = ""

        self.psx_result = None
        self.fund_result = None
        self.import_result = None

        self.psx_rows = []
        self.fund_rows = []

        self.setWindowTitle("Smart Import Center")
        self.resize(1050, 720)

        self.init_ui()
        self.apply_theme()

    def init_ui(self):
        """
        Build UI.
        """

        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        self.heading = QLabel("📥 Smart Import Center")
        self.heading.setAlignment(Qt.AlignCenter)

        description = QLabel(
            "Upload one file and the app will auto-detect whether it contains "
            "PSX stocks, mutual funds, pension/MTPF data, or a mixed statement. "
            "Detected rows will be routed to the correct manager after preview."
        )
        description.setWordWrap(True)
        description.setAlignment(Qt.AlignCenter)
        description.setStyleSheet("""
            font-size:13px;
            padding:6px;
        """)

        file_group = self.create_file_group()
        options_group = self.create_options_group()
        route_group = self.create_route_summary_group()
        button_layout = self.create_buttons()

        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)
        self.log_box.setMinimumHeight(250)

        note = QLabel(
            "Safety rule: Import always opens preview first. "
            "Financial data is never applied directly without your confirmation."
        )
        note.setWordWrap(True)
        note.setStyleSheet("""
            font-size:12px;
            color:#555555;
            padding:5px;
        """)

        main_layout.addWidget(self.heading)
        main_layout.addWidget(description)
        main_layout.addWidget(file_group)
        main_layout.addWidget(options_group)
        main_layout.addWidget(route_group)
        main_layout.addLayout(button_layout)
        main_layout.addWidget(QLabel("Import Log:"))
        main_layout.addWidget(self.log_box)
        main_layout.addWidget(note)

        self.write_log("Smart Import Center ready.")
        self.write_log("PSX supported files: " + ", ".join(SUPPORTED_EXTENSIONS))
        self.write_log("Fund/MTPF statement support: " + ("Available" if FUND_IMPORT_AVAILABLE else "Not available"))

    def create_file_group(self):
        """
        Create file selector group.
        """

        group = QGroupBox("Select File")
        layout = QHBoxLayout()
        group.setLayout(layout)

        self.file_label = QLabel("No file selected")
        self.file_label.setWordWrap(True)
        self.file_label.setMinimumHeight(42)
        self.file_label.setFrameShape(QFrame.StyledPanel)
        self.file_label.setStyleSheet("""
            padding:8px;
            border:1px solid #cccccc;
            border-radius:5px;
        """)

        browse_btn = QPushButton("📂 Browse File")
        browse_btn.setMinimumHeight(40)
        browse_btn.clicked.connect(self.browse_file)

        layout.addWidget(self.file_label)
        layout.addWidget(browse_btn)

        return group

    def create_options_group(self):
        """
        Create import options group.
        """

        group = QGroupBox("Import Options")
        layout = QVBoxLayout()
        group.setLayout(layout)

        self.update_existing_checkbox = QCheckBox(
            "Update existing records if matching record already exists"
        )
        self.update_existing_checkbox.setChecked(True)

        self.skip_low_confidence_checkbox = QCheckBox(
            "Auto-uncheck low confidence PSX rows in preview"
        )
        self.skip_low_confidence_checkbox.setChecked(True)

        self.skip_zero_funds_checkbox = QCheckBox(
            "Skip zero-balance Mutual Fund / MTPF rows"
        )
        self.skip_zero_funds_checkbox.setChecked(True)

        self.auto_route_note = QLabel(
            "Auto route: PSX stocks → Portfolio, Mutual Funds → Mutual Funds Manager, "
            "Pension/MTPF → Wealth Assets Manager."
        )
        self.auto_route_note.setWordWrap(True)
        self.auto_route_note.setStyleSheet("""
            font-size:12px;
            color:#555555;
        """)

        layout.addWidget(self.update_existing_checkbox)
        layout.addWidget(self.skip_low_confidence_checkbox)
        layout.addWidget(self.skip_zero_funds_checkbox)
        layout.addWidget(self.auto_route_note)

        return group

    def create_route_summary_group(self):
        """
        Create detected route summary cards.
        """

        group = QGroupBox("Detected Data Routes")
        layout = QHBoxLayout()
        group.setLayout(layout)

        cards = [
            ("psx", "PSX Stocks", "0 rows"),
            ("mutual", "Mutual Funds", "0 rows"),
            ("pension", "Pension / MTPF", "0 rows"),
            ("total", "Total Detected", "0 rows"),
        ]

        self.route_labels = {}

        for key, title, value in cards:
            card = self.create_route_card(title, value)
            self.route_labels[key] = card.findChild(QLabel, "value_label")
            layout.addWidget(card)

        return group

    def create_route_card(self, title, value):
        """
        Create route summary card.
        """

        frame = QFrame()
        frame.setObjectName("route_card")
        frame.setFrameShape(QFrame.StyledPanel)
        frame.setMinimumHeight(80)

        layout = QVBoxLayout(frame)

        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-weight:bold;")

        value_label = QLabel(value)
        value_label.setObjectName("value_label")
        value_label.setAlignment(Qt.AlignCenter)
        value_label.setStyleSheet("""
            font-size:16px;
            font-weight:bold;
            color:green;
        """)

        layout.addWidget(title_label)
        layout.addWidget(value_label)

        return frame

    def create_buttons(self):
        """
        Create buttons.
        """

        layout = QHBoxLayout()

        self.read_btn = QPushButton("🔍 Analyze File")
        self.preview_btn = QPushButton("👁 Preview & Import")
        self.raw_text_btn = QPushButton("🧾 Show Raw Text")
        self.clear_btn = QPushButton("🧹 Clear")
        self.close_btn = QPushButton("❌ Close")

        buttons = [
            self.read_btn,
            self.preview_btn,
            self.raw_text_btn,
            self.clear_btn,
            self.close_btn,
        ]

        for button in buttons:
            button.setMinimumHeight(40)
            layout.addWidget(button)

        self.preview_btn.setEnabled(False)
        self.raw_text_btn.setEnabled(False)

        self.read_btn.clicked.connect(self.analyze_selected_file)
        self.preview_btn.clicked.connect(self.open_preview_and_import)
        self.raw_text_btn.clicked.connect(self.show_raw_text_from_last_import)
        self.clear_btn.clicked.connect(self.clear_import)
        self.close_btn.clicked.connect(self.close_or_return_dashboard)

        return layout

    def browse_file(self):
        """
        Browse supported file.
        """

        file_filter = (
            "Smart Import Files (*.csv *.xlsx *.xlsm *.pdf *.png *.jpg *.jpeg *.txt);;"
            "CSV Files (*.csv);;"
            "Excel Files (*.xlsx *.xlsm);;"
            "PDF Files (*.pdf);;"
            "Images (*.png *.jpg *.jpeg);;"
            "Text Files (*.txt);;"
            "All Files (*.*)"
        )

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select File for Smart Import",
            "",
            file_filter
        )

        if not file_path:
            return

        self.selected_file = file_path
        self.file_label.setText(file_path)
        self.reset_detected_data(keep_file=True)

        self.write_log(f"Selected file: {file_path}")

    def analyze_selected_file(self):
        """
        Analyze selected file using all available import engines.
        """

        if not self.selected_file:
            QMessageBox.warning(
                self,
                "No File Selected",
                "Please select a file first."
            )
            return

        self.reset_detected_data(keep_file=True)

        self.write_log("Analyzing selected file...")

        path = Path(self.selected_file)
        extension = path.suffix.lower()

        # 1. PSX / portfolio engine.
        self.run_psx_engine()

        # 2. Fund/MTPF engine. Only useful for PDF/TXT.
        if extension in [".pdf", ".txt"]:
            self.run_fund_engine()
        else:
            self.write_log("Fund/MTPF engine skipped for this file type.")

        self.apply_zero_balance_filter()
        self.update_route_cards()

        raw_text_available = bool(self.get_combined_raw_text().strip())
        self.raw_text_btn.setEnabled(raw_text_available)

        total_rows = len(self.psx_rows) + len(self.fund_rows)

        if total_rows <= 0:
            self.preview_btn.setEnabled(False)
            self.log_raw_text_preview(self.get_combined_raw_text())

            QMessageBox.warning(
                self,
                "No Rows Detected",
                "No valid import rows were detected.\n\n"
                "Raw text preview has been added to the log."
            )
            return

        self.preview_btn.setEnabled(True)

        message = (
            f"Smart analysis completed.\n\n"
            f"PSX Stock Rows: {len(self.psx_rows)}\n"
            f"Mutual Fund Rows: {self.count_fund_category('Mutual Fund')}\n"
            f"Pension / MTPF Rows: {self.count_fund_category('Pension / MTPF')}\n\n"
            "Click Preview & Import to review and route data."
        )

        QMessageBox.information(
            self,
            "Analysis Completed",
            message
        )

    def run_psx_engine(self):
        """
        Run PSX portfolio import engine.
        """

        try:
            self.psx_result = read_portfolio_file(self.selected_file)
            self.import_result = self.psx_result

            errors = self.psx_result.get("errors", [])
            warnings = self.psx_result.get("warnings", [])

            for warning in warnings:
                self.write_log(f"PSX WARNING: {warning}")

            for error in errors:
                self.write_log(f"PSX ERROR: {error}")

            self.psx_rows = self.psx_result.get("rows", []) or []

            if self.psx_rows:
                summary = get_import_summary(self.psx_rows)

                self.write_log(f"PSX rows detected: {summary['total_rows']}")
                self.write_log(
                    f"PSX investment value: PKR {summary['total_investment']:,.2f}"
                )
                self.write_log(
                    f"PSX current value: PKR {summary['total_current']:,.2f}"
                )
            else:
                self.write_log("PSX rows detected: 0")

        except Exception as e:
            self.psx_rows = []
            self.write_log(f"PSX ENGINE ERROR: {str(e)}")

    def run_fund_engine(self):
        """
        Run Mutual Fund / MTPF statement engine.
        """

        if not FUND_IMPORT_AVAILABLE or read_fund_statement_file is None:
            self.write_log("Fund/MTPF engine not available.")
            return

        try:
            self.fund_result = read_fund_statement_file(self.selected_file)

            errors = self.fund_result.get("errors", [])
            warnings = self.fund_result.get("warnings", [])

            for warning in warnings:
                self.write_log(f"FUND WARNING: {warning}")

            for error in errors:
                self.write_log(f"FUND ERROR: {error}")

            self.fund_rows = self.fund_result.get("rows", []) or []

            if self.fund_rows:
                summary = self.recalculate_fund_summary(self.fund_rows)

                self.write_log(f"Fund/MTPF rows detected: {summary['total_rows']}")
                self.write_log(
                    f"Mutual Fund value: {format_display_currency(summary['mutual_fund_value'])}"
                )
                self.write_log(
                    f"Pension / MTPF value: {format_display_currency(summary['pension_value'])}"
                )
            else:
                self.write_log("Fund/MTPF rows detected: 0")

        except Exception as e:
            self.fund_rows = []
            self.write_log(f"FUND ENGINE ERROR: {str(e)}")

    def apply_zero_balance_filter(self):
        """
        Filter zero-balance fund rows if selected.
        """

        if not self.skip_zero_funds_checkbox.isChecked():
            return

        original_count = len(self.fund_rows)

        self.fund_rows = [
            row for row in self.fund_rows
            if safe_float(row.get("investment_value", 0)) > 0
        ]

        removed = original_count - len(self.fund_rows)

        if removed > 0:
            self.write_log(f"Zero-balance fund rows skipped: {removed}")

    def open_preview_and_import(self):
        """
        Open one unified preview dialog and import selected rows to correct managers.
        """

        if not self.psx_rows and not self.fund_rows:
            QMessageBox.warning(
                self,
                "No Rows",
                "Please analyze a valid file first."
            )
            return

        dialog = UnifiedSmartImportPreviewDialog(
            psx_rows=self.psx_rows,
            fund_rows=self.fund_rows,
            parent=self,
            auto_uncheck_low_confidence=self.skip_low_confidence_checkbox.isChecked(),
            skip_zero_funds=self.skip_zero_funds_checkbox.isChecked(),
        )

        if not dialog.exec():
            self.write_log("Unified Smart Import cancelled by user.")
            return

        selected_psx_rows = dialog.get_selected_psx_rows()
        selected_fund_rows = dialog.get_selected_fund_rows()

        if self.skip_zero_funds_checkbox.isChecked():
            selected_fund_rows = [
                row for row in selected_fund_rows
                if safe_float(row.get("investment_value", 0)) > 0
            ]

        if not selected_psx_rows and not selected_fund_rows:
            QMessageBox.warning(
                self,
                "No Rows Selected",
                "No rows were selected for import."
            )
            return

        total_result = {
            "psx_added": 0,
            "psx_updated": 0,
            "psx_skipped": 0,
            "psx_errors": 0,
            "mf_added": 0,
            "mf_updated": 0,
            "pension_added": 0,
            "pension_updated": 0,
            "fund_skipped": 0,
            "fund_errors": [],
        }

        if selected_psx_rows:
            psx_result = self.import_rows_to_portfolio(selected_psx_rows)
            total_result["psx_added"] += psx_result["added"]
            total_result["psx_updated"] += psx_result["updated"]
            total_result["psx_skipped"] += psx_result["skipped"]
            total_result["psx_errors"] += psx_result["errors"]

        if selected_fund_rows:
            fund_result = self.import_selected_fund_rows(selected_fund_rows)
            total_result["mf_added"] += fund_result["mutual_funds_added"]
            total_result["mf_updated"] += fund_result["mutual_funds_updated"]
            total_result["pension_added"] += fund_result["pension_added"]
            total_result["pension_updated"] += fund_result["pension_updated"]
            total_result["fund_skipped"] += fund_result["skipped"]
            total_result["fund_errors"].extend(fund_result["errors"])

        self.show_final_import_message(total_result)
        self.refresh_parent_dashboard()
        self.preview_btn.setEnabled(False)


    def preview_and_import_psx(self, total_result):
        """
        Preview and import PSX rows.
        """

        dialog = SmartImportPreviewDialog(
            parent=self,
            rows=self.psx_rows,
            file_path=self.selected_file,
        )

        if self.skip_low_confidence_checkbox.isChecked():
            dialog.uncheck_invalid_rows()

        if not dialog.exec():
            return False

        selected_rows = dialog.get_data()

        if not selected_rows:
            self.write_log("No PSX rows selected.")
            return True

        result = self.import_rows_to_portfolio(selected_rows)

        total_result["psx_added"] += result["added"]
        total_result["psx_updated"] += result["updated"]
        total_result["psx_skipped"] += result["skipped"]
        total_result["psx_errors"] += result["errors"]

        return True

    def preview_and_import_funds(self, total_result):
        """
        Preview and import fund/MTPF rows.
        """

        if not FUND_PREVIEW_AVAILABLE or FundStatementPreviewDialog is None:
            QMessageBox.critical(
                self,
                "Fund Preview Missing",
                "fund_statement_preview_dialog.py is missing."
            )
            return False

        summary = self.recalculate_fund_summary(self.fund_rows)

        dialog = FundStatementPreviewDialog(
            rows=self.fund_rows,
            summary=summary,
            parent=self,
        )

        if not dialog.exec():
            return False

        selected_rows = dialog.get_selected_rows()

        if self.skip_zero_funds_checkbox.isChecked():
            selected_rows = [
                row for row in selected_rows
                if safe_float(row.get("investment_value", 0)) > 0
            ]

        if not selected_rows:
            self.write_log("No Fund/MTPF rows selected.")
            return True

        result = self.import_selected_fund_rows(selected_rows)

        total_result["mf_added"] += result["mutual_funds_added"]
        total_result["mf_updated"] += result["mutual_funds_updated"]
        total_result["pension_added"] += result["pension_added"]
        total_result["pension_updated"] += result["pension_updated"]
        total_result["fund_skipped"] += result["skipped"]
        total_result["fund_errors"].extend(result["errors"])

        return True

    def import_rows_to_portfolio(self, rows):
        """
        Import selected PSX rows to portfolio.
        """

        existing_holdings = get_all_holdings()
        existing_by_symbol = {}

        for holding in existing_holdings:
            symbol = str(holding.get("symbol", "")).strip().upper()

            if symbol:
                existing_by_symbol[symbol] = holding

        result = {
            "added": 0,
            "updated": 0,
            "skipped": 0,
            "errors": 0,
        }

        update_existing = self.update_existing_checkbox.isChecked()

        for row in rows:
            try:
                symbol = str(row["symbol"]).strip().upper()
                shares = float(row["shares"])
                avg_price = float(row["avg_price"])
                current_price = float(row["current_price"])

                if not symbol or shares <= 0:
                    result["skipped"] += 1
                    continue

                if symbol in existing_by_symbol:
                    if update_existing:
                        update_existing_holding(
                            symbol,
                            shares,
                            avg_price,
                            current_price
                        )
                        result["updated"] += 1
                        self.write_log(f"Updated PSX holding: {symbol}")
                    else:
                        result["skipped"] += 1
                        self.write_log(f"Skipped existing PSX holding: {symbol}")
                else:
                    add_new_holding(
                        symbol,
                        shares,
                        avg_price,
                        current_price
                    )
                    result["added"] += 1
                    self.write_log(f"Added PSX holding: {symbol}")

            except Exception as e:
                result["errors"] += 1
                self.write_log(
                    f"PSX row import error for {row.get('symbol', '')}: {str(e)}"
                )

        return result

    def import_selected_fund_rows(self, rows):
        """
        Import selected Mutual Fund / MTPF rows.
        """

        result = {
            "mutual_funds_added": 0,
            "mutual_funds_updated": 0,
            "pension_added": 0,
            "pension_updated": 0,
            "skipped": 0,
            "errors": [],
        }

        update_existing = self.update_existing_checkbox.isChecked()

        for row in rows:
            try:
                category = str(row.get("category", "")).strip()

                if category == "Mutual Fund":
                    imported = self.import_mutual_fund_row(row, update_existing)

                    if imported == "updated":
                        result["mutual_funds_updated"] += 1
                    elif imported == "added":
                        result["mutual_funds_added"] += 1
                    else:
                        result["skipped"] += 1

                elif category == "Pension / MTPF":
                    imported = self.import_pension_row(row, update_existing)

                    if imported == "updated":
                        result["pension_updated"] += 1
                    elif imported == "added":
                        result["pension_added"] += 1
                    else:
                        result["skipped"] += 1

                else:
                    result["skipped"] += 1

            except Exception as e:
                result["errors"].append(
                    f"{row.get('fund_code', 'Unknown')}: {str(e)}"
                )

        return result

    def import_mutual_fund_row(self, row, update_existing=True):
        """
        Import one Mutual Fund row.
        """

        if add_new_mutual_fund is None or update_existing_mutual_fund is None:
            raise RuntimeError("Mutual Fund service is not available.")

        units = safe_float(row.get("units", 0))
        nav = safe_float(row.get("nav", 0))
        investment_value = safe_float(row.get("investment_value", 0))

        if units <= 0 or investment_value <= 0:
            return "skipped"

        fund_name = self.build_mutual_fund_import_name(row)
        avg_nav = investment_value / units if units > 0 else nav
        current_nav = nav

        existing = self.find_existing_mutual_fund(fund_name)

        if existing and update_existing:
            update_existing_mutual_fund(
                fund_name,
                units,
                avg_nav,
                current_nav
            )
            self.write_log(f"Updated Mutual Fund: {fund_name}")
            return "updated"

        if existing and not update_existing:
            self.write_log(f"Skipped existing Mutual Fund: {fund_name}")
            return "skipped"

        add_new_mutual_fund(
            fund_name,
            units,
            avg_nav,
            current_nav
        )
        self.write_log(f"Added Mutual Fund: {fund_name}")
        return "added"

    def import_pension_row(self, row, update_existing=True):
        """
        Import one Pension / MTPF row into Wealth Assets.
        """

        if add_new_wealth_asset is None or update_existing_wealth_asset is None:
            raise RuntimeError("Wealth Asset service is not available.")

        investment_value = safe_float(row.get("investment_value", 0))

        if investment_value <= 0:
            return "skipped"

        account_name = self.build_pension_account_name(row)
        today = datetime.now().strftime("%Y-%m-%d")

        asset_data = {
            "asset_type": "Pension / MTPF",
            "account_name": account_name,
            "institution": "Al Meezan Investments",
            "current_balance": investment_value,
            "monthly_contribution": 0,
            "employer_contribution": 0,
            "start_date": "",
            "last_updated": today,
            "remarks": (
                f"Imported from Smart Import Center. "
                f"Fund Code: {row.get('fund_code', '')}, "
                f"Unit Type: {row.get('unit_type', '')}, "
                f"Units: {row.get('units', 0)}, "
                f"NAV: {row.get('nav', 0)}. "
                f"{row.get('remarks', '')}"
            ),
            "is_active": 1,
        }

        existing = self.find_existing_pension_asset(account_name)

        if existing and update_existing:
            update_existing_wealth_asset(
                existing["id"],
                asset_data
            )
            self.write_log(f"Updated Pension/MTPF Asset: {account_name}")
            return "updated"

        if existing and not update_existing:
            self.write_log(f"Skipped existing Pension/MTPF Asset: {account_name}")
            return "skipped"

        add_new_wealth_asset(asset_data)
        self.write_log(f"Added Pension/MTPF Asset: {account_name}")
        return "added"

    def build_mutual_fund_import_name(self, row):
        """
        Build mutual fund name for database.
        """

        fund_code = str(row.get("fund_code", "")).upper().strip()
        unit_type = str(row.get("unit_type", "")).strip()

        if unit_type:
            return f"{fund_code} {unit_type}".strip()

        return fund_code

    def build_pension_account_name(self, row):
        """
        Build pension/MTPF asset account name.
        """

        fund_code = str(row.get("fund_code", "")).upper().strip()
        unit_type = str(row.get("unit_type", "")).strip()

        if unit_type:
            return f"{fund_code} {unit_type}".strip()

        return fund_code

    def find_existing_mutual_fund(self, fund_name):
        """
        Find existing mutual fund by name.
        """

        if get_all_mutual_funds is None:
            return None

        target = str(fund_name or "").upper().strip()

        for item in get_all_mutual_funds():
            existing_name = str(item.get("fund", "")).upper().strip()

            if existing_name == target:
                return item

        return None

    def find_existing_pension_asset(self, account_name):
        """
        Find existing Pension/MTPF asset by account name.
        """

        if get_all_wealth_assets is None:
            return None

        target = str(account_name or "").upper().strip()

        try:
            assets = get_all_wealth_assets(include_inactive=True)
        except TypeError:
            assets = get_all_wealth_assets()

        for item in assets:
            item_type = str(item.get("asset_type", "")).strip()
            item_name = str(item.get("account_name", "")).upper().strip()

            if item_type == "Pension / MTPF" and item_name == target:
                return item

        return None

    def count_fund_category(self, category):
        """
        Count fund rows by category.
        """

        return len([
            row for row in self.fund_rows
            if row.get("category") == category
        ])

    def recalculate_fund_summary(self, rows):
        """
        Recalculate fund summary.
        """

        rows = rows or []

        mutual_rows = [
            row for row in rows
            if row.get("category") == "Mutual Fund"
        ]

        pension_rows = [
            row for row in rows
            if row.get("category") == "Pension / MTPF"
        ]

        mutual_value = sum(
            safe_float(row.get("investment_value", 0))
            for row in mutual_rows
        )

        pension_value = sum(
            safe_float(row.get("investment_value", 0))
            for row in pension_rows
        )

        total_value = mutual_value + pension_value

        return {
            "total_rows": len(rows),
            "mutual_fund_rows": len(mutual_rows),
            "pension_rows": len(pension_rows),
            "mutual_fund_value": round(mutual_value, 2),
            "pension_value": round(pension_value, 2),
            "total_value": round(total_value, 2),
            "suggested_rows": len([
                row for row in rows
                if safe_float(row.get("investment_value", 0)) > 0
            ]),
            "total_gain_loss": sum(
                safe_float(row.get("total_gain_loss", 0))
                for row in rows
            ),
        }

    def update_route_cards(self):
        """
        Update detected route cards.
        """

        psx_count = len(self.psx_rows)
        mutual_count = self.count_fund_category("Mutual Fund")
        pension_count = self.count_fund_category("Pension / MTPF")
        total_count = psx_count + mutual_count + pension_count

        values = {
            "psx": f"{psx_count} rows",
            "mutual": f"{mutual_count} rows",
            "pension": f"{pension_count} rows",
            "total": f"{total_count} rows",
        }

        for key, value in values.items():
            label = self.route_labels.get(key)

            if label:
                label.setText(value)

    def get_combined_raw_text(self):
        """
        Return combined raw text from engines.
        """

        texts = []

        if self.psx_result:
            texts.append(str(self.psx_result.get("raw_text", "") or ""))

        if self.fund_result:
            texts.append(str(self.fund_result.get("raw_text", "") or ""))

        return "\n\n".join([text for text in texts if text.strip()])

    def show_raw_text_from_last_import(self):
        """
        Show raw extracted text in log.
        """

        raw_text = self.get_combined_raw_text()

        if not raw_text.strip():
            QMessageBox.information(
                self,
                "No Raw Text",
                "No raw OCR/PDF text is available for this file."
            )
            return

        self.log_raw_text_preview(raw_text, max_lines=100)

    def log_raw_text_preview(self, raw_text, max_lines=60):
        """
        Log raw OCR/PDF text preview.
        """

        raw_text = str(raw_text or "").strip()

        if not raw_text:
            self.write_log("RAW TEXT PREVIEW: No text extracted.")
            return

        self.write_log("----- RAW OCR/PDF TEXT PREVIEW START -----")

        lines = [
            line.strip()
            for line in raw_text.splitlines()
            if line.strip()
        ]

        for line in lines[:max_lines]:
            self.write_log(line)

        if len(lines) > max_lines:
            self.write_log(
                f"... {len(lines) - max_lines} more lines hidden ..."
            )

        self.write_log("----- RAW OCR/PDF TEXT PREVIEW END -----")

    def show_final_import_message(self, result):
        """
        Show final import summary.
        """

        message = (
            "Smart Import completed.\n\n"
            f"PSX Added: {result['psx_added']}\n"
            f"PSX Updated: {result['psx_updated']}\n"
            f"PSX Skipped: {result['psx_skipped']}\n"
            f"PSX Errors: {result['psx_errors']}\n\n"
            f"Mutual Funds Added: {result['mf_added']}\n"
            f"Mutual Funds Updated: {result['mf_updated']}\n"
            f"Pension/MTPF Added: {result['pension_added']}\n"
            f"Pension/MTPF Updated: {result['pension_updated']}\n"
            f"Fund/MTPF Skipped: {result['fund_skipped']}\n"
            f"Fund/MTPF Errors: {len(result['fund_errors'])}"
        )

        self.write_log(message.replace("\n", " | "))

        if result["fund_errors"]:
            for error in result["fund_errors"]:
                self.write_log(f"FUND IMPORT ERROR: {error}")

        QMessageBox.information(
            self,
            "Import Completed",
            message
        )

    def reset_detected_data(self, keep_file=False):
        """
        Reset detected data.
        """

        self.psx_result = None
        self.fund_result = None
        self.import_result = None
        self.psx_rows = []
        self.fund_rows = []
        self.preview_btn.setEnabled(False)
        self.raw_text_btn.setEnabled(False)

        if not keep_file:
            self.selected_file = ""
            self.file_label.setText("No file selected")

        self.update_route_cards()

    def clear_import(self):
        """
        Clear import screen.
        """

        self.reset_detected_data(keep_file=False)
        self.log_box.clear()
        self.write_log("Smart Import cleared.")

    def write_log(self, message):
        """
        Write log line.
        """

        self.log_box.append(str(message))

    def refresh_parent_dashboard(self):
        """
        Refresh parent dashboard if possible.
        """

        try:
            if self.parent_window and hasattr(self.parent_window, "load_portfolio"):
                self.parent_window.load_portfolio()
        except Exception:
            pass

    def close_or_return_dashboard(self):
        """
        Close or return dashboard in single-window navigation.
        """

        try:
            if self.parent_window and hasattr(self.parent_window, "show_dashboard"):
                self.parent_window.show_dashboard()
                return
        except Exception:
            pass

        self.close()

    def apply_theme(self):
        """
        Apply theme.
        """

        theme = str(
            self.settings.get("theme", "light")
        ).strip().lower()

        if theme == "dark":
            self.setStyleSheet("""
                QWidget {
                    background-color:#1e1e1e;
                    color:#ffffff;
                }

                QLabel {
                    color:#ffffff;
                }

                QGroupBox {
                    border:1px solid #555555;
                    border-radius:6px;
                    margin-top:10px;
                    padding:10px;
                    font-weight:bold;
                    color:#ffffff;
                }

                QGroupBox::title {
                    subcontrol-origin: margin;
                    left:10px;
                    padding:0 5px 0 5px;
                }

                QFrame#route_card {
                    background-color:#252526;
                    border:1px solid #555555;
                    border-radius:8px;
                }

                QPushButton {
                    background-color:#2d2d30;
                    color:#ffffff;
                    border:1px solid #555555;
                    border-radius:5px;
                    padding:6px;
                }

                QPushButton:hover {
                    background-color:#3e3e42;
                }

                QTextEdit {
                    background-color:#252526;
                    color:#ffffff;
                    border:1px solid #555555;
                    border-radius:5px;
                }

                QCheckBox {
                    color:#ffffff;
                    font-size:13px;
                }
            """)

            self.heading.setStyleSheet("""
                font-size:24px;
                font-weight:bold;
                padding:10px;
                color:#ffffff;
            """)

        else:
            self.setStyleSheet("""
                QWidget {
                    background-color:#ffffff;
                    color:#000000;
                }

                QLabel {
                    color:#000000;
                }

                QGroupBox {
                    border:1px solid #cccccc;
                    border-radius:6px;
                    margin-top:10px;
                    padding:10px;
                    font-weight:bold;
                    color:#000000;
                }

                QGroupBox::title {
                    subcontrol-origin: margin;
                    left:10px;
                    padding:0 5px 0 5px;
                }

                QFrame#route_card {
                    background-color:#f8f9fa;
                    border:1px solid #cccccc;
                    border-radius:8px;
                }

                QPushButton {
                    background-color:#f5f5f5;
                    color:#000000;
                    border:1px solid #cccccc;
                    border-radius:5px;
                    padding:6px;
                }

                QPushButton:hover {
                    background-color:#e8e8e8;
                }

                QTextEdit {
                    background-color:#ffffff;
                    color:#000000;
                    border:1px solid #cccccc;
                    border-radius:5px;
                }

                QCheckBox {
                    color:#000000;
                    font-size:13px;
                }
            """)

            self.heading.setStyleSheet("""
                font-size:24px;
                font-weight:bold;
                padding:10px;
                color:#000000;
            """)


def safe_float(value):
    """
    Convert value to float safely.
    """

    try:
        if value is None:
            return 0.0

        if isinstance(value, (int, float)):
            return float(value)

        text = str(value).strip()
        text = text.replace(",", "")
        text = text.replace("PKR", "")
        text = text.replace("Rs.", "")
        text = text.replace("Rs", "")
        text = text.replace("%", "")

        if not text:
            return 0.0

        return float(text)

    except Exception:
        return 0.0
