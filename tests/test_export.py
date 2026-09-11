import numpy as np
from openpyxl import Workbook

from src.export_xlsx import verify_result1_workbook


def test_verify_result1_workbook_accepts_matching_values(tmp_path) -> None:
    path = tmp_path / "result1_test.xlsx"
    workbook = Workbook()
    temperature = workbook.active
    temperature.title = "温度"
    moisture = workbook.create_sheet("水分浓度")

    time_s = np.array([0.0, 1.0])
    radius_m = np.array([0.0, 0.001])
    temperature_values = np.array([[28.0, 28.0], [28.1, 28.2]])
    moisture_values = np.array([[2.55, 2.55], [2.5, 2.4]])
    for sheet, values in [
        (temperature, temperature_values),
        (moisture, moisture_values),
    ]:
        sheet.append(["时间\\到药材中心的距离", 0, 0.1])
        for index, time_value in enumerate(time_s):
            sheet.append([time_value, values[index, 0], values[index, 1]])

    workbook.save(path)
    verify_result1_workbook(
        path,
        time_s,
        radius_m,
        temperature_values,
        moisture_values,
        tolerance=1e-9,
    )
