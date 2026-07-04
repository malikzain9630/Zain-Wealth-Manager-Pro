"""
Charts Window
Visual analytics for PSX, Mutual Funds and Overall Wealth.
Supports light/dark theme from Settings.
"""

from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QColor, QFont, QPainter, QPen, QBrush
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

from services.settings_service import load_settings
from services.chart_service import (
    get_psx_allocation_data,
    get_mutual_fund_allocation_data,
    get_overall_wealth_data,
    get_profit_loss_data,
    get_chart_summary,
)


class ChartWidget(QFrame):
    """
    Custom chart widget using Qt painting.
    Supports:
        - pie chart
        - bar chart
        - light/dark theme
    """

    def __init__(self, title, chart_type="pie", parent=None):
        super().__init__(parent)

        self.title = title
        self.chart_type = chart_type
        self.labels = []
        self.values = []

        self.theme = "light"

        self.background_color = QColor("#ffffff")
        self.text_color = QColor("#000000")
        self.muted_text_color = QColor("#777777")
        self.border_color = QColor("#cccccc")
        self.axis_color = QColor("#666666")
        self.positive_color = QColor("#70AD47")
        self.negative_color = QColor("#C00000")

        self.setMinimumHeight(330)
        self.setFrameShape(QFrame.StyledPanel)

        self.colors = [
            QColor("#4472C4"),
            QColor("#ED7D31"),
            QColor("#A5A5A5"),
            QColor("#FFC000"),
            QColor("#5B9BD5"),
            QColor("#70AD47"),
            QColor("#264478"),
            QColor("#9E480E"),
            QColor("#636363"),
            QColor("#997300"),
        ]

        self.set_theme("light")

    def set_theme(self, theme):
        """
        Apply light/dark theme to chart widget.
        """

        self.theme = str(theme).strip().lower()

        if self.theme == "dark":

            self.background_color = QColor("#2d2d30")
            self.text_color = QColor("#ffffff")
            self.muted_text_color = QColor("#b0b0b0")
            self.border_color = QColor("#555555")
            self.axis_color = QColor("#bbbbbb")
            self.positive_color = QColor("#70AD47")
            self.negative_color = QColor("#FF6B6B")

            self.setStyleSheet("""
                QFrame {
                    background-color: #2d2d30;
                    border: 1px solid #555555;
                    border-radius: 8px;
                }
            """)

        else:

            self.background_color = QColor("#ffffff")
            self.text_color = QColor("#000000")
            self.muted_text_color = QColor("#777777")
            self.border_color = QColor("#cccccc")
            self.axis_color = QColor("#666666")
            self.positive_color = QColor("#70AD47")
            self.negative_color = QColor("#C00000")

            self.setStyleSheet("""
                QFrame {
                    background-color: #ffffff;
                    border: 1px solid #cccccc;
                    border-radius: 8px;
                }
            """)

        self.update()

    def set_data(self, labels, values):
        """
        Set chart data and repaint.
        """

        self.labels = labels
        self.values = values
        self.update()

    def paintEvent(self, event):

        super().paintEvent(event)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        self.draw_title(painter)

        if not self.labels or not self.values:
            self.draw_no_data(painter)
            return

        if self.chart_type == "bar":
            self.draw_bar_chart(painter)
        else:
            self.draw_pie_chart(painter)

    def draw_title(self, painter):

        painter.setPen(QPen(self.text_color))
        painter.setFont(QFont("Arial", 12, QFont.Bold))

        painter.drawText(
            QRectF(10, 8, self.width() - 20, 30),
            Qt.AlignCenter,
            self.title
        )

    def draw_no_data(self, painter):

        painter.setPen(QPen(self.muted_text_color))
        painter.setFont(QFont("Arial", 11))

        painter.drawText(
            QRectF(10, 60, self.width() - 20, self.height() - 80),
            Qt.AlignCenter,
            "No data available"
        )

    def draw_pie_chart(self, painter):

        chart_labels = []
        chart_values = []

        for label, value in zip(self.labels, self.values):

            value = float(value)

            if value > 0:
                chart_labels.append(str(label))
                chart_values.append(value)

        if not chart_values:
            self.draw_no_data(painter)
            return

        total = sum(chart_values)

        if total <= 0:
            self.draw_no_data(painter)
            return

        left = 30
        top = 55
        size = min(self.height() - 100, self.width() // 2 - 40)

        if size < 120:
            size = 120

        pie_rect = QRectF(left, top, size, size)

        start_angle = 0

        for index, value in enumerate(chart_values):

            span_angle = int((value / total) * 360 * 16)

            color = self.colors[index % len(self.colors)]

            painter.setBrush(QBrush(color))
            painter.setPen(QPen(self.background_color, 1))

            painter.drawPie(
                pie_rect,
                start_angle,
                span_angle
            )

            start_angle += span_angle

        self.draw_legend(
            painter,
            chart_labels,
            chart_values,
            total,
            left + size + 35,
            top
        )

    def draw_legend(self, painter, labels, values, total, x, y):

        painter.setFont(QFont("Arial", 9))
        painter.setPen(QPen(self.text_color))

        max_items = min(len(labels), 10)

        for index in range(max_items):

            color = self.colors[index % len(self.colors)]

            painter.setBrush(QBrush(color))
            painter.setPen(QPen(self.border_color))

            box_y = y + index * 24

            painter.drawRect(x, box_y, 14, 14)

            percent = 0

            if total > 0:
                percent = (values[index] / total) * 100

            text = f"{labels[index]} - {percent:.1f}%"

            painter.setPen(QPen(self.text_color))
            painter.drawText(x + 22, box_y + 12, text)

        if len(labels) > max_items:
            painter.setPen(QPen(self.muted_text_color))
            painter.drawText(
                x,
                y + max_items * 24 + 14,
                f"...and {len(labels) - max_items} more"
            )

    def draw_bar_chart(self, painter):

        labels = [str(label) for label in self.labels]
        values = [float(value) for value in self.values]

        if not values:
            self.draw_no_data(painter)
            return

        max_abs = max(abs(value) for value in values)

        if max_abs <= 0:
            self.draw_no_data(painter)
            return

        left = 60
        right = 30
        top = 60
        bottom = 70

        chart_width = self.width() - left - right
        chart_height = self.height() - top - bottom

        if chart_width <= 0 or chart_height <= 0:
            return

        zero_y = top + chart_height / 2

        painter.setPen(QPen(self.axis_color, 1))
        painter.drawLine(left, int(zero_y), left + chart_width, int(zero_y))

        painter.setFont(QFont("Arial", 9))
        painter.setPen(QPen(self.text_color))
        painter.drawText(10, int(zero_y) + 4, "0")

        bar_count = len(values)
        gap = 20
        bar_width = max(
            35,
            int((chart_width - gap * (bar_count + 1)) / max(bar_count, 1))
        )

        for index, value in enumerate(values):

            x = left + gap + index * (bar_width + gap)

            bar_height = abs(value) / max_abs * (chart_height / 2 - 25)

            if value >= 0:
                y = zero_y - bar_height
                color = self.positive_color
            else:
                y = zero_y
                color = self.negative_color

            painter.setBrush(QBrush(color))
            painter.setPen(QPen(color))

            painter.drawRect(
                int(x),
                int(y),
                int(bar_width),
                int(bar_height)
            )

            painter.setPen(QPen(self.text_color))
            painter.setFont(QFont("Arial", 9, QFont.Bold))

            value_text = f"{value:,.0f}"

            painter.drawText(
                QRectF(
                    x - 20,
                    y - 22 if value >= 0 else y + bar_height + 5,
                    bar_width + 40,
                    20
                ),
                Qt.AlignCenter,
                value_text
            )

            painter.setFont(QFont("Arial", 8))
            painter.setPen(QPen(self.text_color))

            painter.drawText(
                QRectF(x - 20, self.height() - 55, bar_width + 40, 35),
                Qt.AlignCenter | Qt.TextWordWrap,
                labels[index]
            )


class ChartsWindow(QWidget):
    """
    Charts and visual analytics window.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.settings = load_settings()
        self.summary_labels = {}

        self.setWindowTitle("Charts & Visual Analytics")
        self.resize(1250, 800)

        self.init_ui()
        self.apply_theme()
        self.load_charts()

    def init_ui(self):

        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        self.heading = QLabel("📈 Charts & Visual Analytics")
        self.heading.setAlignment(Qt.AlignCenter)

        summary_layout = self.create_summary_cards()
        button_layout = self.create_buttons()

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)

        container = QWidget()
        grid = QGridLayout()
        container.setLayout(grid)

        self.psx_allocation_chart = ChartWidget(
            "PSX Allocation",
            "pie"
        )

        self.mutual_fund_allocation_chart = ChartWidget(
            "Mutual Funds Allocation",
            "pie"
        )

        self.overall_wealth_chart = ChartWidget(
            "Overall Wealth Allocation",
            "pie"
        )

        self.profit_loss_chart = ChartWidget(
            "Profit / Loss Comparison",
            "bar"
        )

        grid.addWidget(self.psx_allocation_chart, 0, 0)
        grid.addWidget(self.mutual_fund_allocation_chart, 0, 1)
        grid.addWidget(self.overall_wealth_chart, 1, 0)
        grid.addWidget(self.profit_loss_chart, 1, 1)

        self.scroll.setWidget(container)

        main_layout.addWidget(self.heading)
        main_layout.addLayout(summary_layout)
        main_layout.addLayout(button_layout)
        main_layout.addWidget(self.scroll)

    def create_summary_cards(self):

        layout = QHBoxLayout()

        cards = [
            ("PSX Current Value", "psx_current"),
            ("MF Current Value", "mutual_fund_current"),
            ("Total Current Value", "total_current"),
            ("Total Profit / Loss", "total_profit"),
            ("Total Profit %", "total_profit_percent"),
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

            psx_data = get_psx_allocation_data()
            mutual_fund_data = get_mutual_fund_allocation_data()
            overall_data = get_overall_wealth_data()
            profit_loss_data = get_profit_loss_data()

            self.psx_allocation_chart.set_data(
                psx_data["labels"],
                psx_data["values"]
            )

            self.mutual_fund_allocation_chart.set_data(
                mutual_fund_data["labels"],
                mutual_fund_data["values"]
            )

            self.overall_wealth_chart.set_data(
                overall_data["labels"],
                overall_data["values"]
            )

            self.profit_loss_chart.set_data(
                profit_loss_data["labels"],
                profit_loss_data["values"]
            )

            self.update_summary_cards()

        except Exception as e:

            QMessageBox.critical(
                self,
                "Charts Error",
                f"Failed to load charts.\n\n{str(e)}"
            )

    def update_summary_cards(self):

        summary = get_chart_summary()

        self.summary_labels["psx_current"].setText(
            self.format_currency(summary["psx_current"])
        )

        self.summary_labels["mutual_fund_current"].setText(
            self.format_currency(summary["mutual_fund_current"])
        )

        self.summary_labels["total_current"].setText(
            self.format_currency(summary["total_current"])
        )

        self.summary_labels["total_profit"].setText(
            self.format_currency(summary["total_profit"])
        )

        self.summary_labels["total_profit_percent"].setText(
            f"{summary['total_profit_percent']:.2f}%"
        )

        if summary["total_profit"] >= 0:
            color = "green"
        else:
            color = "red"

        self.summary_labels["total_profit"].setStyleSheet(f"""
            font-size:17px;
            font-weight:bold;
            color:{color};
        """)

        self.summary_labels["total_profit_percent"].setStyleSheet(f"""
            font-size:17px;
            font-weight:bold;
            color:{color};
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
            self.psx_allocation_chart,
            self.mutual_fund_allocation_chart,
            self.overall_wealth_chart,
            self.profit_loss_chart,
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
