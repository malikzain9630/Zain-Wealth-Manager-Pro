"""
Unified Smart Import Preview Dialog
Phase 10A - Unified Smart Import Center

Purpose:
- Show PSX stock rows and Mutual Fund / MTPF rows in one preview window.
- Use tabs for clean separation.
- Return selected PSX rows and selected Fund/MTPF rows.
"""

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QMessageBox,
    QFrame,
    QCheckBox,
    QAbstractItemView,
    QTabWidget,
    QWidget,
)
from PySide6.QtCore import Qt

try:
    from services.currency_service import format_currency as format_display_currency
except Exception:
    def format_display_currency(value, *args, **kwargs):
        try:
            return f"PKR {float(value):,.2f}"
        except Exception:
            return "PKR 0.00"

try:
    from services.settings_service import load_settings
except Exception:
    def load_settings():
        return {"theme": "Light"}


class UnifiedSmartImportPreviewDialog(QDialog):
    """
    Unified preview dialog for PSX + Mutual Fund / MTPF rows.
    """

    def __init__(
        self,
        psx_rows=None,
        fund_rows=None,
        parent=None,
        auto_uncheck_low_confidence=True,
        skip_zero_funds=True,
    ):
        super().__init__(parent)

        self.psx_rows = psx_rows or []
        self.fund_rows = fund_rows or []
        self.auto_uncheck_low_confidence = auto_uncheck_low_confidence
        self.skip_zero_funds = skip_zero_funds

        self.settings = load_settings()
        self.theme = self.settings.get("theme", "Light")

        self.psx_table = None
        self.fund_table = None
        self.tab_widget = None

        self.setWindowTitle("Unified Smart Import Preview")
        self.resize(1450, 780)

        self.setup_ui()
        self.apply_theme()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)

        title = QLabel("📥 Unified Smart Import Preview")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 21px; font-weight: bold; padding: 10px;")
        main_layout.addWidget(title)

        note = QLabel(
            "Review all detected rows in one window. "
            "PSX rows will go to Portfolio Manager. "
            "Mutual Fund rows will go to Mutual Funds Manager. "
            "Pension/MTPF rows will go to Wealth Assets Manager."
        )
        note.setAlignment(Qt.AlignCenter)
        note.setWordWrap(True)
        main_layout.addWidget(note)

        self.create_summary_cards(main_layout)

        self.tab_widget = QTabWidget()
        self.create_psx_tab()
        self.create_fund_tab()
        main_layout.addWidget(self.tab_widget)

        buttons_layout = QHBoxLayout()

        select_all_btn = QPushButton("✅ Select All")
        unselect_all_btn = QPushButton("⬜ Unselect All")
        import_btn = QPushButton("🚀 Import Selected")
        cancel_btn = QPushButton("❌ Cancel")

        select_all_btn.clicked.connect(self.select_all_rows)
        unselect_all_btn.clicked.connect(self.unselect_all_rows)
        import_btn.clicked.connect(self.accept_import)
        cancel_btn.clicked.connect(self.reject)

        buttons_layout.addWidget(select_all_btn)
        buttons_layout.addWidget(unselect_all_btn)
        buttons_layout.addStretch()
        buttons_layout.addWidget(import_btn)
        buttons_layout.addWidget(cancel_btn)

        main_layout.addLayout(buttons_layout)

    def create_summary_cards(self, parent_layout):
        layout = QHBoxLayout()

        psx_value = sum(safe_float(row.get("current_value", 0)) for row in self.psx_rows)

        mutual_rows = [row for row in self.fund_rows if row.get("category") == "Mutual Fund"]
        pension_rows = [row for row in self.fund_rows if row.get("category") == "Pension / MTPF"]

        mutual_value = sum(safe_float(row.get("investment_value", 0)) for row in mutual_rows)
        pension_value = sum(safe_float(row.get("investment_value", 0)) for row in pension_rows)

        cards = [
            ("PSX Rows", len(self.psx_rows)),
            ("PSX Value", format_display_currency(psx_value)),
            ("Mutual Fund Rows", len(mutual_rows)),
            ("Mutual Fund Value", format_display_currency(mutual_value)),
            ("Pension/MTPF Rows", len(pension_rows)),
            ("Pension/MTPF Value", format_display_currency(pension_value)),
        ]

        for title, value in cards:
            layout.addWidget(self.make_card(title, value))

        parent_layout.addLayout(layout)

    def make_card(self, title, value):
        frame = QFrame()
        frame.setObjectName("summary_card")
        frame.setFrameShape(QFrame.StyledPanel)
        frame.setMinimumHeight(82)

        layout = QVBoxLayout(frame)

        title_label = QLabel(str(title))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-weight: bold;")

        value_label = QLabel(str(value))
        value_label.setAlignment(Qt.AlignCenter)
        value_label.setStyleSheet("font-size: 15px; font-weight: bold;")

        layout.addWidget(title_label)
        layout.addWidget(value_label)

        return frame

    def create_psx_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        self.psx_table = QTableWidget()
        self.psx_table.setColumnCount(11)
        self.psx_table.setHorizontalHeaderLabels([
            "Import?",
            "Symbol",
            "Share Name",
            "Shares",
            "Avg Price",
            "Current Price",
            "Investment Value",
            "Current Value",
            "Confidence",
            "Source",
            "Remarks",
        ])

        self.psx_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.psx_table.horizontalHeader().setStretchLastSection(True)
        self.psx_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.psx_table.setAlternatingRowColors(True)

        self.load_psx_rows()

        layout.addWidget(self.psx_table)
        self.tab_widget.addTab(tab, f"📈 PSX Stocks ({len(self.psx_rows)})")

    def create_fund_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        self.fund_table = QTableWidget()
        self.fund_table.setColumnCount(13)
        self.fund_table.setHorizontalHeaderLabels([
            "Import?",
            "Category",
            "Fund Code",
            "Fund Name",
            "Unit Type",
            "Units",
            "NAV",
            "Investment Value",
            "FYTD Gain/Loss",
            "Total Gain/Loss",
            "Confidence",
            "Source",
            "Remarks",
        ])

        self.fund_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.fund_table.horizontalHeader().setStretchLastSection(True)
        self.fund_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.fund_table.setAlternatingRowColors(True)

        self.load_fund_rows()

        layout.addWidget(self.fund_table)
        self.tab_widget.addTab(tab, f"🧾 Funds / MTPF ({len(self.fund_rows)})")

    def load_psx_rows(self):
        self.psx_table.setRowCount(len(self.psx_rows))

        for row_index, row in enumerate(self.psx_rows):
            checkbox = QCheckBox()
            confidence = safe_float(row.get("confidence", 0))
            checked = not (self.auto_uncheck_low_confidence and confidence < 60)
            checkbox.setChecked(checked)
            self.psx_table.setCellWidget(row_index, 0, self.center_checkbox(checkbox))

            values = [
                row.get("symbol", ""),
                row.get("share_name", ""),
                row.get("shares", 0),
                row.get("avg_price", 0),
                row.get("current_price", 0),
                row.get("investment_value", 0),
                row.get("current_value", 0),
                row.get("confidence", 0),
                row.get("source", ""),
                row.get("remarks", ""),
            ]

            for col_offset, value in enumerate(values, start=1):
                item = QTableWidgetItem(str(value))

                # Symbol, confidence, source read-only.
                if col_offset in [1, 8, 9]:
                    item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
                else:
                    item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable)

                if col_offset == 8:
                    self.apply_confidence_color(item, value)

                self.psx_table.setItem(row_index, col_offset, item)

        self.psx_table.resizeColumnsToContents()

    def load_fund_rows(self):
        self.fund_table.setRowCount(len(self.fund_rows))

        for row_index, row in enumerate(self.fund_rows):
            checkbox = QCheckBox()
            checked = bool(row.get("import_suggested", True))

            if self.skip_zero_funds and safe_float(row.get("investment_value", 0)) <= 0:
                checked = False

            checkbox.setChecked(checked)
            self.fund_table.setCellWidget(row_index, 0, self.center_checkbox(checkbox))

            values = [
                row.get("category", ""),
                row.get("fund_code", ""),
                row.get("fund_name", ""),
                row.get("unit_type", ""),
                row.get("units", 0),
                row.get("nav", 0),
                row.get("investment_value", 0),
                row.get("fytd_gain_loss", 0),
                row.get("total_gain_loss", 0),
                row.get("confidence", 0),
                row.get("source", ""),
                row.get("remarks", ""),
            ]

            for col_offset, value in enumerate(values, start=1):
                item = QTableWidgetItem(str(value))

                # Category, Fund Code, Confidence, Source read-only.
                if col_offset in [1, 2, 10, 11]:
                    item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
                else:
                    item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable)

                if col_offset == 10:
                    self.apply_confidence_color(item, value)

                self.fund_table.setItem(row_index, col_offset, item)

        self.fund_table.resizeColumnsToContents()

    def center_checkbox(self, checkbox):
        frame = QFrame()
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignCenter)
        layout.addWidget(checkbox)
        return frame

    def apply_confidence_color(self, item, confidence):
        confidence = safe_float(confidence)

        if confidence >= 85:
            item.setBackground(Qt.green)
            item.setForeground(Qt.black)
        elif confidence >= 60:
            item.setBackground(Qt.yellow)
            item.setForeground(Qt.black)
        else:
            item.setBackground(Qt.red)
            item.setForeground(Qt.white)

    def get_row_checkbox(self, table, row):
        widget = table.cellWidget(row, 0)
        if not widget:
            return None
        return widget.findChild(QCheckBox)

    def select_all_rows(self):
        self.set_all_rows_checked(True)

    def unselect_all_rows(self):
        self.set_all_rows_checked(False)

    def set_all_rows_checked(self, checked):
        for table in [self.psx_table, self.fund_table]:
            if table is None:
                continue

            for row in range(table.rowCount()):
                checkbox = self.get_row_checkbox(table, row)
                if checkbox:
                    checkbox.setChecked(checked)

    def get_cell_text(self, table, row, column):
        item = table.item(row, column)
        if not item:
            return ""
        return item.text().strip()

    def get_selected_psx_rows(self):
        selected = []

        for row in range(self.psx_table.rowCount()):
            checkbox = self.get_row_checkbox(self.psx_table, row)

            if not checkbox or not checkbox.isChecked():
                continue

            symbol = self.get_cell_text(self.psx_table, row, 1).upper()
            share_name = self.get_cell_text(self.psx_table, row, 2)
            shares = safe_float(self.get_cell_text(self.psx_table, row, 3))
            avg_price = safe_float(self.get_cell_text(self.psx_table, row, 4))
            current_price = safe_float(self.get_cell_text(self.psx_table, row, 5))
            investment_value = safe_float(self.get_cell_text(self.psx_table, row, 6))
            current_value = safe_float(self.get_cell_text(self.psx_table, row, 7))
            confidence = int(safe_float(self.get_cell_text(self.psx_table, row, 8)))
            source = self.get_cell_text(self.psx_table, row, 9)
            remarks = self.get_cell_text(self.psx_table, row, 10)

            selected.append({
                "symbol": symbol,
                "share_name": share_name,
                "shares": round(shares, 4),
                "avg_price": round(avg_price, 4),
                "current_price": round(current_price, 4),
                "investment_value": round(investment_value, 2),
                "current_value": round(current_value, 2),
                "confidence": confidence,
                "source": source,
                "remarks": remarks,
            })

        return selected

    def get_selected_fund_rows(self):
        selected = []

        for row in range(self.fund_table.rowCount()):
            checkbox = self.get_row_checkbox(self.fund_table, row)

            if not checkbox or not checkbox.isChecked():
                continue

            category = self.get_cell_text(self.fund_table, row, 1)
            fund_code = self.get_cell_text(self.fund_table, row, 2).upper()
            fund_name = self.get_cell_text(self.fund_table, row, 3)
            unit_type = self.get_cell_text(self.fund_table, row, 4)
            units = safe_float(self.get_cell_text(self.fund_table, row, 5))
            nav = safe_float(self.get_cell_text(self.fund_table, row, 6))
            investment_value = safe_float(self.get_cell_text(self.fund_table, row, 7))
            fytd_gain_loss = safe_float(self.get_cell_text(self.fund_table, row, 8))
            total_gain_loss = safe_float(self.get_cell_text(self.fund_table, row, 9))
            confidence = int(safe_float(self.get_cell_text(self.fund_table, row, 10)))
            source = self.get_cell_text(self.fund_table, row, 11)
            remarks = self.get_cell_text(self.fund_table, row, 12)

            selected.append({
                "category": category,
                "fund_code": fund_code,
                "fund_name": fund_name,
                "unit_type": unit_type,
                "units": round(units, 4),
                "nav": round(nav, 4),
                "investment_value": round(investment_value, 2),
                "fytd_gain_loss": round(fytd_gain_loss, 2),
                "total_gain_loss": round(total_gain_loss, 2),
                "confidence": confidence,
                "source": source,
                "remarks": remarks,
            })

        return selected

    def accept_import(self):
        psx_rows = self.get_selected_psx_rows()
        fund_rows = self.get_selected_fund_rows()

        if not psx_rows and not fund_rows:
            QMessageBox.warning(
                self,
                "No Rows Selected",
                "Please select at least one row to import."
            )
            return

        invalid = []

        for row in psx_rows:
            if not row["symbol"]:
                invalid.append("PSX: Symbol missing.")
            if row["shares"] <= 0:
                invalid.append(f"PSX {row['symbol']}: Shares must be greater than zero.")
            if row["avg_price"] < 0:
                invalid.append(f"PSX {row['symbol']}: Avg Price cannot be negative.")
            if row["current_price"] < 0:
                invalid.append(f"PSX {row['symbol']}: Current Price cannot be negative.")

        for row in fund_rows:
            if not row["fund_code"]:
                invalid.append("Fund: Fund Code missing.")
            if row["units"] < 0:
                invalid.append(f"Fund {row['fund_code']}: Units cannot be negative.")
            if row["nav"] < 0:
                invalid.append(f"Fund {row['fund_code']}: NAV cannot be negative.")
            if row["investment_value"] < 0:
                invalid.append(f"Fund {row['fund_code']}: Investment Value cannot be negative.")

        if invalid:
            QMessageBox.warning(
                self,
                "Invalid Rows",
                "\n".join(invalid[:12])
            )
            return

        self.accept()

    def apply_theme(self):
        dark = str(self.theme).lower() == "dark"

        if dark:
            self.setStyleSheet("""
                QDialog {
                    background-color: #121212;
                    color: #ffffff;
                }
                QLabel {
                    color: #ffffff;
                }
                QFrame#summary_card {
                    background-color: #1f1f1f;
                    border: 1px solid #444444;
                    border-radius: 8px;
                }
                QTableWidget {
                    background-color: #1e1e1e;
                    color: #ffffff;
                    gridline-color: #444444;
                    alternate-background-color: #252525;
                }
                QHeaderView::section {
                    background-color: #2c2c2c;
                    color: #ffffff;
                    padding: 5px;
                    border: 1px solid #444444;
                }
                QPushButton {
                    background-color: #2c2c2c;
                    color: #ffffff;
                    border: 1px solid #555555;
                    padding: 8px;
                    border-radius: 5px;
                }
                QPushButton:hover {
                    background-color: #3a3a3a;
                }
                QCheckBox {
                    color: #ffffff;
                }
                QTabWidget::pane {
                    border: 1px solid #444444;
                }
                QTabBar::tab {
                    background: #2c2c2c;
                    color: #ffffff;
                    padding: 8px;
                    border: 1px solid #444444;
                }
                QTabBar::tab:selected {
                    background: #3a3a3a;
                }
            """)
        else:
            self.setStyleSheet("""
                QDialog {
                    background-color: #f5f5f5;
                    color: #000000;
                }
                QFrame#summary_card {
                    background-color: #ffffff;
                    border: 1px solid #d0d0d0;
                    border-radius: 8px;
                }
                QTableWidget {
                    background-color: #ffffff;
                    color: #000000;
                    alternate-background-color: #f2f2f2;
                }
                QHeaderView::section {
                    background-color: #eeeeee;
                    color: #000000;
                    padding: 5px;
                    border: 1px solid #cccccc;
                }
                QPushButton {
                    padding: 8px;
                    border-radius: 5px;
                }
                QTabBar::tab {
                    padding: 8px;
                }
            """)


def safe_float(value):
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
