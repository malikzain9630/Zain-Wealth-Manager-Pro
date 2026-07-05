"""
Wealth Projection Window
Phase 10 projection/forecast window for:
- Provident Fund
- Pension / MTPF
- Bank Cash
- Other manual wealth assets

All base values are stored in PKR.
Display currency conversion is handled by currency_service.
"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QBrush
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QComboBox,
    QDoubleSpinBox,
    QSpinBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QAbstractItemView,
    QHeaderView,
    QFrame,
    QGroupBox,
    QMessageBox,
)

from services.settings_service import load_settings
from services.currency_service import format_currency as format_display_currency
from services.currency_service import get_conversion_note
from services.wealth_asset_service import (
    get_all_wealth_assets,
    calculate_projected_balance,
)


class SortableTableWidgetItem(QTableWidgetItem):

    def __init__(self, text, sort_value=None):
        super().__init__(text)

        if sort_value is None:
            self.sort_value = text
        else:
            self.sort_value = sort_value

    def __lt__(self, other):

        if isinstance(other, SortableTableWidgetItem):

            try:
                return float(self.sort_value) < float(other.sort_value)

            except (ValueError, TypeError):
                return str(self.sort_value) < str(other.sort_value)

        return super().__lt__(other)


class WealthProjectionWindow(QWidget):
    """
    Future projection window for PF, Pension/MTPF and Bank Cash.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.settings = load_settings()
        self.assets = []
        self.summary_labels = {}

        self.setWindowTitle("Wealth Projection / Forecast")
        self.resize(1250, 760)

        self.init_ui()
        self.apply_theme()
        self.load_assets()

    def init_ui(self):

        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        self.heading = QLabel("📈 Wealth Projection / Forecast")
        self.heading.setAlignment(Qt.AlignCenter)

        self.conversion_note = QLabel("")
        self.conversion_note.setAlignment(Qt.AlignCenter)
        self.conversion_note.setMinimumHeight(28)

        input_group = self.create_input_group()
        summary_layout = self.create_summary_cards()
        button_layout = self.create_buttons()

        self.result_table = self.create_result_table()

        main_layout.addWidget(self.heading)
        main_layout.addWidget(self.conversion_note)
        main_layout.addWidget(input_group)
        main_layout.addLayout(summary_layout)
        main_layout.addLayout(button_layout)
        main_layout.addWidget(self.result_table)

    def create_input_group(self):

        group = QGroupBox("Projection Inputs")
        layout = QGridLayout()
        group.setLayout(layout)

        self.asset_combo = QComboBox()
        self.asset_combo.setMinimumHeight(34)
        self.asset_combo.currentIndexChanged.connect(self.asset_changed)

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

        self.annual_return_spin = QDoubleSpinBox()
        self.annual_return_spin.setRange(0, 100)
        self.annual_return_spin.setDecimals(2)
        self.annual_return_spin.setSingleStep(0.50)
        self.annual_return_spin.setValue(8.00)
        self.annual_return_spin.setSuffix(" %")
        self.annual_return_spin.setMinimumHeight(34)

        self.years_spin = QSpinBox()
        self.years_spin.setRange(1, 50)
        self.years_spin.setValue(5)
        self.years_spin.setMinimumHeight(34)

        layout.addWidget(QLabel("Select Asset:"), 0, 0)
        layout.addWidget(self.asset_combo, 0, 1)

        layout.addWidget(QLabel("Current Balance (PKR):"), 1, 0)
        layout.addWidget(self.current_balance_spin, 1, 1)

        layout.addWidget(QLabel("Monthly Contribution (PKR):"), 2, 0)
        layout.addWidget(self.monthly_contribution_spin, 2, 1)

        layout.addWidget(QLabel("Employer Contribution (PKR):"), 3, 0)
        layout.addWidget(self.employer_contribution_spin, 3, 1)

        layout.addWidget(QLabel("Expected Annual Return:"), 4, 0)
        layout.addWidget(self.annual_return_spin, 4, 1)

        layout.addWidget(QLabel("Years:"), 5, 0)
        layout.addWidget(self.years_spin, 5, 1)

        note = QLabel(
            "Note: Projection uses monthly compounding. "
            "Actual return may vary; this is an estimate only."
        )
        note.setWordWrap(True)

        layout.addWidget(note, 6, 0, 1, 2)

        return group

    def create_summary_cards(self):

        layout = QHBoxLayout()

        cards = [
            ("Current Balance", "current_balance"),
            ("Total Contribution", "total_contribution"),
            ("Estimated Profit", "estimated_profit"),
            ("Projected Balance", "projected_balance"),
            ("Monthly Addition", "monthly_addition"),
        ]

        for title, key in cards:
            layout.addWidget(self.create_card(title, key))

        return layout

    def create_card(self, title, key):

        card = QFrame()
        card.setObjectName("SummaryCard")
        card.setFrameShape(QFrame.StyledPanel)
        card.setMinimumHeight(88)

        layout = QVBoxLayout()
        card.setLayout(layout)

        title_label = QLabel(title)
        title_label.setObjectName("CardTitle")
        title_label.setAlignment(Qt.AlignCenter)

        value_label = QLabel(self.format_currency(0))
        value_label.setObjectName("CardValue")
        value_label.setAlignment(Qt.AlignCenter)

        layout.addWidget(title_label)
        layout.addWidget(value_label)

        self.summary_labels[key] = value_label

        return card

    def create_buttons(self):

        layout = QHBoxLayout()

        self.calculate_btn = QPushButton("📈 Calculate Projection")
        self.refresh_btn = QPushButton("🔄 Refresh Assets")
        self.close_btn = QPushButton("❌ Close")

        buttons = [
            self.calculate_btn,
            self.refresh_btn,
            self.close_btn,
        ]

        for button in buttons:
            button.setMinimumHeight(38)
            layout.addWidget(button)

        self.calculate_btn.clicked.connect(self.calculate_projection)
        self.refresh_btn.clicked.connect(self.load_assets)
        self.close_btn.clicked.connect(self.close)

        return layout

    def create_result_table(self):

        table = QTableWidget()
        table.setColumnCount(6)

        table.setHorizontalHeaderLabels([
            "Year",
            "Opening Balance",
            "User Contribution",
            "Employer Contribution",
            "Estimated Profit",
            "Closing Balance",
        ])

        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setSelectionMode(QAbstractItemView.SingleSelection)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.setAlternatingRowColors(True)
        table.setSortingEnabled(True)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.verticalHeader().setVisible(False)

        return table

    def load_assets(self):

        try:
            self.settings = load_settings()
            self.assets = get_all_wealth_assets()

            self.asset_combo.blockSignals(True)
            self.asset_combo.clear()

            if not self.assets:
                self.asset_combo.addItem("No active wealth assets found", None)
            else:
                for asset in self.assets:

                    institution = str(asset.get("institution", "") or "").strip()

                    if institution:
                        label = (
                            f"{asset['asset_type']} - "
                            f"{asset['account_name']} ({institution})"
                        )
                    else:
                        label = f"{asset['asset_type']} - {asset['account_name']}"

                    self.asset_combo.addItem(label, asset["id"])

            self.asset_combo.blockSignals(False)

            self.update_conversion_note()
            self.asset_changed()
            self.apply_theme()

        except Exception as e:

            QMessageBox.critical(
                self,
                "Load Assets Error",
                str(e)
            )

    def asset_changed(self):

        asset = self.get_selected_asset()

        if not asset:
            self.current_balance_spin.setValue(0)
            self.monthly_contribution_spin.setValue(0)
            self.employer_contribution_spin.setValue(0)
            self.clear_results()
            return

        self.current_balance_spin.setValue(
            self.safe_float(asset.get("current_balance", 0))
        )

        self.monthly_contribution_spin.setValue(
            self.safe_float(asset.get("monthly_contribution", 0))
        )

        self.employer_contribution_spin.setValue(
            self.safe_float(asset.get("employer_contribution", 0))
        )

        self.calculate_projection()

    def calculate_projection(self):

        try:
            current_balance = self.current_balance_spin.value()
            monthly_contribution = self.monthly_contribution_spin.value()
            employer_contribution = self.employer_contribution_spin.value()
            annual_return = self.annual_return_spin.value()
            years = self.years_spin.value()

            projection = calculate_projected_balance(
                current_balance=current_balance,
                monthly_contribution=monthly_contribution,
                employer_contribution=employer_contribution,
                annual_return_percent=annual_return,
                years=years,
            )

            self.summary_labels["current_balance"].setText(
                self.format_currency(projection["current_balance"])
            )

            self.summary_labels["total_contribution"].setText(
                self.format_currency(projection["total_contribution"])
            )

            self.summary_labels["estimated_profit"].setText(
                self.format_currency(projection["estimated_profit"])
            )

            self.summary_labels["projected_balance"].setText(
                self.format_currency(projection["projected_balance"])
            )

            self.summary_labels["monthly_addition"].setText(
                self.format_currency(projection["monthly_addition"])
            )

            self.populate_yearly_table(
                current_balance=current_balance,
                monthly_contribution=monthly_contribution,
                employer_contribution=employer_contribution,
                annual_return=annual_return,
                years=years,
            )

            self.color_summary_cards()

        except Exception as e:

            QMessageBox.critical(
                self,
                "Projection Error",
                str(e)
            )

    def populate_yearly_table(
        self,
        current_balance,
        monthly_contribution,
        employer_contribution,
        annual_return,
        years,
    ):

        self.result_table.setSortingEnabled(False)
        self.result_table.setRowCount(0)
        self.result_table.setRowCount(years)

        balance = self.safe_float(current_balance)
        monthly_contribution = self.safe_float(monthly_contribution)
        employer_contribution = self.safe_float(employer_contribution)
        annual_return = self.safe_float(annual_return)

        monthly_return = annual_return / 100 / 12

        for row in range(years):

            opening_balance = balance
            user_contribution_year = 0
            employer_contribution_year = 0

            for _ in range(12):

                balance += monthly_contribution
                user_contribution_year += monthly_contribution

                balance += employer_contribution
                employer_contribution_year += employer_contribution

                if monthly_return > 0:
                    balance = balance * (1 + monthly_return)

            closing_balance = balance
            estimated_profit = (
                closing_balance
                - opening_balance
                - user_contribution_year
                - employer_contribution_year
            )

            if estimated_profit < 0:
                estimated_profit = 0

            row_items = [
                self.create_table_item(str(row + 1), row + 1),
                self.create_table_item(
                    self.format_currency(opening_balance),
                    opening_balance
                ),
                self.create_table_item(
                    self.format_currency(user_contribution_year),
                    user_contribution_year
                ),
                self.create_table_item(
                    self.format_currency(employer_contribution_year),
                    employer_contribution_year
                ),
                self.create_table_item(
                    self.format_currency(estimated_profit),
                    estimated_profit
                ),
                self.create_table_item(
                    self.format_currency(closing_balance),
                    closing_balance
                ),
            ]

            self.set_row_items(row, row_items)

        self.result_table.setSortingEnabled(True)

    def set_row_items(self, row, row_items):

        for column, item in enumerate(row_items):

            item.setTextAlignment(Qt.AlignCenter)

            if column > 0:

                try:
                    numeric_value = float(item.data(Qt.UserRole))
                except (ValueError, TypeError):
                    numeric_value = 0

                if numeric_value > 0:
                    item.setForeground(QBrush(QColor("green")))

            self.result_table.setItem(row, column, item)

    def create_table_item(self, text, value):

        item = SortableTableWidgetItem(text, value)
        item.setData(Qt.UserRole, value)

        return item

    def clear_results(self):

        self.result_table.setRowCount(0)

        for label in self.summary_labels.values():
            label.setText(self.format_currency(0))

    def color_summary_cards(self):

        for label in self.summary_labels.values():

            label.setStyleSheet("""
                font-size:17px;
                font-weight:bold;
                color:green;
            """)

    def get_selected_asset(self):

        selected_id = self.asset_combo.currentData()

        if selected_id is None:
            return None

        for asset in self.assets:

            if int(asset["id"]) == int(selected_id):
                return asset

        return None

    def update_conversion_note(self):

        try:
            self.conversion_note.setText(get_conversion_note())

        except Exception:
            self.conversion_note.setText("Base currency: PKR")

    def format_currency(self, value):

        try:
            return format_display_currency(value)

        except Exception:
            return f"PKR {float(value):,.2f}"

    def safe_float(self, value):

        try:
            if value is None:
                return 0.0

            return float(value)

        except (ValueError, TypeError):
            return 0.0

    def apply_theme(self):

        theme = str(
            self.settings.get("theme", "light")
        ).strip().lower()

        if theme == "dark":

            self.setStyleSheet("""
                QWidget {
                    background-color: #1e1e1e;
                    color: #ffffff;
                }

                QLabel {
                    color: #ffffff;
                }

                QLabel#CardTitle {
                    font-size:13px;
                    font-weight:bold;
                    color:#dddddd;
                }

                QLabel#CardValue {
                    font-size:17px;
                    font-weight:bold;
                    color:#ffffff;
                }

                QGroupBox {
                    border: 1px solid #555555;
                    border-radius: 6px;
                    margin-top: 10px;
                    padding: 10px;
                    font-weight: bold;
                    color: #ffffff;
                }

                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 5px 0 5px;
                }

                QPushButton {
                    background-color: #2d2d30;
                    color: #ffffff;
                    border: 1px solid #555555;
                    border-radius: 5px;
                    padding: 6px;
                }

                QPushButton:hover {
                    background-color: #3e3e42;
                }

                QComboBox, QDoubleSpinBox, QSpinBox {
                    background-color: #2d2d30;
                    color: #ffffff;
                    border: 1px solid #555555;
                    border-radius: 5px;
                    padding: 5px;
                }

                QTableWidget {
                    background-color: #252526;
                    color: #ffffff;
                    gridline-color: #555555;
                    alternate-background-color: #2d2d30;
                }

                QHeaderView::section {
                    background-color: #333333;
                    color: #ffffff;
                    padding: 5px;
                    border: 1px solid #555555;
                }

                QFrame#SummaryCard {
                    border: 1px solid #555555;
                    border-radius: 8px;
                    background-color: #2d2d30;
                }
            """)

            self.heading.setStyleSheet("""
                font-size:24px;
                font-weight:bold;
                padding:10px;
                color:#ffffff;
            """)

            self.conversion_note.setStyleSheet("""
                font-size:12px;
                color:#dddddd;
                padding:4px;
            """)

        else:

            self.setStyleSheet("""
                QWidget {
                    background-color: #ffffff;
                    color: #000000;
                }

                QLabel {
                    color: #000000;
                }

                QLabel#CardTitle {
                    font-size:13px;
                    font-weight:bold;
                    color:#444444;
                }

                QLabel#CardValue {
                    font-size:17px;
                    font-weight:bold;
                    color:#000000;
                }

                QGroupBox {
                    border: 1px solid #cccccc;
                    border-radius: 6px;
                    margin-top: 10px;
                    padding: 10px;
                    font-weight: bold;
                    color: #000000;
                }

                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 5px 0 5px;
                }

                QPushButton {
                    background-color: #f5f5f5;
                    color: #000000;
                    border: 1px solid #cccccc;
                    border-radius: 5px;
                    padding: 6px;
                }

                QPushButton:hover {
                    background-color: #e8e8e8;
                }

                QComboBox, QDoubleSpinBox, QSpinBox {
                    background-color: #ffffff;
                    color: #000000;
                    border: 1px solid #cccccc;
                    border-radius: 5px;
                    padding: 5px;
                }

                QTableWidget {
                    background-color: #ffffff;
                    color: #000000;
                    gridline-color: #dddddd;
                    alternate-background-color: #f8f9fa;
                }

                QHeaderView::section {
                    background-color: #f1f1f1;
                    color: #000000;
                    padding: 5px;
                    border: 1px solid #cccccc;
                }

                QFrame#SummaryCard {
                    border: 1px solid #cccccc;
                    border-radius: 8px;
                    background-color: #f8f9fa;
                }
            """)

            self.heading.setStyleSheet("""
                font-size:24px;
                font-weight:bold;
                padding:10px;
                color:#000000;
            """)

            self.conversion_note.setStyleSheet("""
                font-size:12px;
                color:#555555;
                padding:4px;
            """)
