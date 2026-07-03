"""
Zain Wealth Manager Pro
styles.py

Corporate Excel Formatting
"""

import xlsxwriter


class ExcelTheme:

    # Corporate Colors
    PRIMARY = "#0B5CAD"
    SECONDARY = "#1F4E78"
    SUCCESS = "#2E7D32"
    DANGER = "#C62828"
    WARNING = "#F9A825"
    LIGHT = "#F5F7FA"
    WHITE = "#FFFFFF"
    DARK = "#263238"

    def __init__(self, workbook):

        self.workbook = workbook

        self.title = workbook.add_format({
            "bold": True,
            "font_size": 22,
            "font_color": self.WHITE,
            "align": "center",
            "valign": "vcenter",
            "bg_color": self.PRIMARY
        })

        self.heading = workbook.add_format({
            "bold": True,
            "font_size": 13,
            "font_color": self.WHITE,
            "bg_color": self.SECONDARY,
            "border": 1,
            "align": "center"
        })

        self.normal = workbook.add_format({
            "font_size": 11,
            "border": 1
        })

        self.currency = workbook.add_format({
            "num_format": 'Rs #,##0.00',
            "font_size": 11,
            "border": 1
        })

        self.green = workbook.add_format({
            "bold": True,
            "font_color": self.SUCCESS,
            "font_size": 12
        })

        self.red = workbook.add_format({
            "bold": True,
            "font_color": self.DANGER,
            "font_size": 12
        })

        self.card_title = workbook.add_format({
            "bold": True,
            "font_size": 12,
            "font_color": self.DARK,
            "bg_color": "#DCE6F1",
            "border": 1
        })

        self.card_value = workbook.add_format({
            "bold": True,
            "font_size": 16,
            "font_color": self.PRIMARY,
            "border": 1,
            "align": "center"
        })