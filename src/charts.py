"""
Charts Module
Version 2.0
"""

from data.networth import NET_WORTH_HISTORY


def create_asset_chart(workbook, worksheet, allocation):

    chart = workbook.add_chart({"type": "pie"})

    labels = list(allocation.keys())
    values = list(allocation.values())

    start_row = 30

    for i, label in enumerate(labels):
        worksheet.write(start_row + i, 10, label)
        worksheet.write(start_row + i, 11, values[i])

    chart.add_series({
        "name": "Asset Allocation",
        "categories": ["Dashboard", start_row, 10,
                       start_row + len(labels) - 1, 10],
        "values": ["Dashboard", start_row, 11,
                   start_row + len(labels) - 1, 11],
        "data_labels": {
            "percentage": True,
            "category": True
        }
    })

    chart.set_title({"name": "Asset Allocation"})
    chart.set_style(10)

    worksheet.insert_chart("F15", chart, {
        "x_scale": 1.25,
        "y_scale": 1.25
    })


def create_networth_chart(workbook, worksheet):

    chart = workbook.add_chart({"type": "line"})

    start_row = 45

    for i, item in enumerate(NET_WORTH_HISTORY):

        worksheet.write(start_row + i, 10, item[0])
        worksheet.write(start_row + i, 11, item[1])

    chart.add_series({

        "name": "Net Worth",

        "categories": [
            "Dashboard",
            start_row,
            10,
            start_row + len(NET_WORTH_HISTORY) - 1,
            10
        ],

        "values": [
            "Dashboard",
            start_row,
            11,
            start_row + len(NET_WORTH_HISTORY) - 1,
            11
        ],

        "marker": {
            "type": "circle",
            "size": 6
        }

    })

    chart.set_title({
        "name": "Net Worth Trend"
    })

    chart.set_x_axis({
        "name": "Month"
    })

    chart.set_y_axis({
        "name": "PKR"
    })

    chart.set_style(11)

    worksheet.insert_chart("F32", chart, {
        "x_scale": 1.4,
        "y_scale": 1.3
    })