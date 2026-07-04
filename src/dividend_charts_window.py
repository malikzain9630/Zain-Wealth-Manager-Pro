"""
Dividend Charts Window
Visual analytics for dividend income.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QPushButton,
    QMessageBox,
    QLabel,
    QFrame,
    QScrollArea,
)

from charts_window import ChartWidget
from services.settings_service import load_settings
from services.dividend_chart_service import (
    get_stock_wise_dividend_data,
    get_monthly_dividend_data,
    get_yearly_dividend_data,
    get_tax_vs_net_data,
    get_dividend_chart_summary,
)


class DividendChartsWindow(QWidget):
    """
    Dividend income charts window.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.settings = load_settings()
        self.summary_labels = {}

        self.setWindowTitle("Dividend Charts")
        self.resize(1250, 800)

        self.init_ui()
        self.apply_theme()
        self.load_charts()

    def init_ui(self):

        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        self.heading = QLabel("📊 Dividend Income Charts")
        self.heading.setAlignment(Qt.AlignCenter)

        summary_layout = self.create_summary_cards()
        button_layout = self.create_buttons()

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)

        container = QWidget()
        grid = QGridLayout()
        container.setLayout(grid)

        self.stock_wise_chart = ChartWidget(
            "Stock-wise Dividend Income",
            "pie"
        )

        self.monthly_income_chart = ChartWidget(
            "Monthly Dividend Income",
            "bar"
        )

        self.yearly_income_chart = ChartWidget(
            "Yearly Dividend Income",
            "bar"
        )

        self.tax_vs_net_chart = ChartWidget(
            "Tax vs Net Received",
            "pie"
        )

        grid.addWidget(self.stock_wise_chart, 0, 0)
        grid.addWidget(self.monthly_income_chart, 0, 1)
        grid.addWidget(self.yearly_income_chart, 1, 0)
        grid.addWidget(self.tax_vs_net_chart, 1, 1)

        self.scroll.setWidget(container)

        main_layout.addWidget(self.heading)
        main_layout.addLayout(summary_layout)
        main_layout.addLayout(button_layout)
        main_layout.addWidget(self.scroll)

    def create_summary_cards(self):

        layout = QHBoxLayout()

        cards = [
            ("Gross Dividend", "gross_amount"),
            ("Tax Deducted", "tax_amount"),
            ("Net Received", "net_amount"),
            ("Tax %", "tax_percent"),
            ("Total Records", "total_records"),
        ]

        for title, key in cards:

            card = self.create_card(title, key)
            layout.addWidget(card)

        return layout

    def create_card(self, title, key):

        card = QFrame()
        card.setObjectName("SummaryCard")
        card.setFrameShape(QFrame.StyledPanel)
        card.setMinimumHeight(90)

        layout = QVBoxLayout()
        card.setLayout(layout)

        title_label = QLabel(title)
        title_label.setObjectName("CardTitle")
        title_label.setAlignment(Qt.AlignCenter)

        value_label = QLabel("0")
        value_label.setObjectName("CardValue")
        value_label.setAlignment(Qt.AlignCenter)

        layout.addWidget(title_label)
        layout.addWidget(value_label)

        self.summary_labels[key] = value_label

        return card

    def create_buttons(self):

        layout = QHBoxLayout()

        btn_refresh = QPushButton("🔄 Refresh Charts")
        btn_close = QPushButton("❌ Close")

        btn_refresh.setMinimumHeight(38)
        btn_close.setMinimumHeight(38)

        btn_refresh.clicked.connect(self.load_charts)
        btn_close.clicked.connect(self.close)

        layout.addWidget(btn_refresh)
        layout.addWidget(btn_close)

        return layout

    def load_charts(self):

        try:
            self.settings = load_settings()
            self.apply_theme()

            stock_data = get_stock_wise_dividend_data()
            monthly_data = get_monthly_dividend_data()
            yearly_data = get_yearly_dividend_data()
            tax_net_data = get_tax_vs_net_data()

            self.stock_wise_chart.set_data(
                stock_data["labels"],
                stock_data["values"]
            )

            self.monthly_income_chart.set_data(
                monthly_data["labels"],
                monthly_data["values"]
            )

            self.yearly_income_chart.set_data(
                yearly_data["labels"],
                yearly_data["values"]
            )

            self.tax_vs_net_chart.set_data(
                tax_net_data["labels"],
                tax_net_data["values"]
            )

            self.update_summary_cards()

        except Exception as e:

            QMessageBox.critical(
                self,
                "Dividend Charts Error",
                f"Failed to load dividend charts.\n\n{str(e)}"
            )

    def update_summary_cards(self):

        summary = get_dividend_chart_summary()

        self.summary_labels["gross_amount"].setText(
            self.format_currency(summary["gross_amount"])
        )

        self.summary_labels["tax_amount"].setText(
            self.format_currency(summary["tax_amount"])
        )

        self.summary_labels["net_amount"].setText(
            self.format_currency(summary["net_amount"])
        )

        self.summary_labels["tax_percent"].setText(
            f"{summary['tax_percent']:.2f}%"
        )

        self.summary_labels["total_records"].setText(
            str(summary["total_records"])
        )

        self.summary_labels["tax_amount"].setStyleSheet("""
            font-size:17px;
            font-weight:bold;
            color:red;
        """)

        self.summary_labels["net_amount"].setStyleSheet("""
            font-size:17px;
            font-weight:bold;
            color:green;
        """)

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

                QFrame#SummaryCard {
                    border: 1px solid #555555;
                    border-radius: 8px;
                    background-color: #2d2d30;
                }

                QScrollArea {
                    border: none;
                    background-color: #1e1e1e;
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

                QFrame#SummaryCard {
                    border: 1px solid #cccccc;
                    border-radius: 8px;
                    background-color: #f8f9fa;
                }

                QScrollArea {
                    border: none;
                    background-color: #ffffff;
                }
            """)

            self.heading.setStyleSheet("""
                font-size:24px;
                font-weight:bold;
                padding:10px;
                color:#000000;
            """)

        charts = [
            self.stock_wise_chart,
            self.monthly_income_chart,
            self.yearly_income_chart,
            self.tax_vs_net_chart,
        ]

        for chart in charts:
            chart.set_theme(theme)

    def get_currency(self):

        currency = str(
            self.settings.get("currency", "PKR")
        ).strip().upper()

        if not currency:
            currency = "PKR"

        return currency

    def format_currency(self, value):

        return f"{self.get_currency()} {float(value):,.2f}"
