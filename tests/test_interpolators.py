import numpy as np
from openpyxl import Workbook

from src.config import ATTACHMENT_1_PATH, ATTACHMENT_2_PATH
from src.interpolators import PiecewiseLinear, read_attachment_1, read_attachment_2


def test_attachment_1_structure_and_time_step() -> None:
    data = read_attachment_1(ATTACHMENT_1_PATH)
    assert data.time_s.size == 241
    assert np.allclose(np.diff(data.time_s), 60.0)
    assert np.all(data.air_moisture_dry_basis >= 0.0)


def test_attachment_2_structure_and_time_step() -> None:
    data = read_attachment_2(ATTACHMENT_2_PATH)
    assert data.time_s.size == 145
    assert np.allclose(np.diff(data.time_s), 1800.0)
    assert np.all(data.radius_cm > 0.0)
    assert np.all(np.diff(data.radius_cm) <= 1e-15)


def test_piecewise_linear_exact_nodes_and_endpoint_hold() -> None:
    interpolator = PiecewiseLinear(
        np.array([0.0, 1.0, 2.0]),
        np.array([10.0, 20.0, 30.0]),
    )
    assert np.isclose(interpolator(0.0), 10.0)
    assert np.isclose(interpolator(1.0), 20.0)
    assert np.isclose(interpolator(2.0), 30.0)
    assert np.isclose(interpolator(-1.0), 10.0)
    assert np.isclose(interpolator(3.0), 30.0)


def test_no_local_robust_outliers_in_first_differences() -> None:
    attachment_1 = read_attachment_1(ATTACHMENT_1_PATH)
    attachment_2 = read_attachment_2(ATTACHMENT_2_PATH)
    for values in [
        attachment_1.air_temperature_c,
        attachment_1.air_moisture_dry_basis,
        attachment_2.radius_cm,
    ]:
        differences = np.diff(values)
        median = np.median(differences)
        mad = np.median(np.abs(differences - median))
        if mad == 0.0:
            continue
        robust_z = 0.6745 * (differences - median) / mad
        assert np.max(np.abs(robust_z)) <= 3.5


def _write_attachment(path, rows) -> None:
    workbook = Workbook()
    sheet = workbook.active
    sheet.append(["时间", "温度", "水分浓度"] if len(rows[0]) == 3 else ["时间", "半径"])
    for row in rows:
        sheet.append(row)
    workbook.save(path)


def _raises_value_error(function, *args) -> None:
    try:
        function(*args)
    except ValueError:
        return
    raise AssertionError("expected ValueError")


def test_attachment_1_rejects_missing_value(tmp_path) -> None:
    path = tmp_path / "missing.xlsx"
    _write_attachment(path, [[0.0, 28.0, 0.02], [60.0, None, 0.021]])
    _raises_value_error(read_attachment_1, path)


def test_attachment_1_rejects_non_monotonic_time(tmp_path) -> None:
    path = tmp_path / "non_monotonic.xlsx"
    _write_attachment(path, [[0.0, 28.0, 0.02], [0.0, 28.5, 0.021]])
    _raises_value_error(read_attachment_1, path)


def test_attachment_1_rejects_negative_moisture(tmp_path) -> None:
    path = tmp_path / "negative_moisture.xlsx"
    _write_attachment(path, [[0.0, 28.0, -0.02], [60.0, 28.5, 0.021]])
    _raises_value_error(read_attachment_1, path)


def test_attachment_2_rejects_non_positive_radius(tmp_path) -> None:
    path = tmp_path / "bad_radius.xlsx"
    _write_attachment(path, [[0.0, 2.0], [1800.0, 0.0]])
    _raises_value_error(read_attachment_2, path)
