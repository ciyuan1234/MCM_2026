"""交付自检：把 analysis/delivery_check.py 的检查纳入测试套件。"""

from analysis.delivery_check import run_checks


def test_delivery_checks_all_pass() -> None:
    results = run_checks()
    failures = [item for item in results if item["status"] != "PASS"]
    assert not failures, failures
    assert len(results) >= 60


def test_delivery_checks_cover_every_problem() -> None:
    results = run_checks()
    names = " ".join(item["name"] for item in results)
    for problem in (1, 2, 3, 4):
        assert f"问题 {problem} " in names
