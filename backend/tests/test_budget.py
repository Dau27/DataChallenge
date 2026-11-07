from decimal import Decimal

from backend.app.config import Settings
from scripts.run_dev import four_attempt_bound
from scripts.run_dev import historical_attempt_bound
from scripts.run_dev import affordable_batch


def test_budget_reservation_covers_all_four_attempts(checklist, tmp_path):
    settings = Settings(database_path=tmp_path / "test.sqlite3", input_rate=Decimal("0.75"), output_rate=Decimal("4.50"), max_output_tokens=6000)
    snapshot = {"transcript": [{"id": "m0001", "speaker": "client", "timestamp": "00:00", "text": "SYNTHETIC budget test"}]}
    bound = four_attempt_bound(settings, snapshot, checklist)
    # Even ignoring all input, reserve four full output limits, including possible repairs/retries.
    assert bound > 4 * Decimal(6000) * Decimal("4.50") / Decimal(1_000_000)
    larger = {"transcript": [{"id": "m0001", "speaker": "client", "timestamp": "00:00", "text": "SYNTHETIC " * 1000}]}
    assert four_attempt_bound(settings, larger, checklist) > bound


def test_historical_failures_reserve_sent_attempts_at_original_model_rates(checklist, tmp_path):
    current = Settings(database_path=tmp_path / "test.sqlite3", input_rate=Decimal("0.25"), output_rate=Decimal("2.00"), max_output_tokens=6000)
    result = {"metadata": {"rate": {"input_usd_per_million": "0.75", "output_usd_per_million": "4.50"}, "generation": {"max_output_tokens": 6000}},
              "checklist": {"snapshot": checklist.model_dump(mode="json")}, "attempts": [
                  {"input_token_upper_bound": 10000, "max_output_tokens": 6000},
                  {"input_token_upper_bound": 10000, "max_output_tokens": 6000}]}
    assert historical_attempt_bound(current, result, {}) == Decimal("0.069")


def test_concurrent_batch_reserves_every_inflight_job_before_start():
    rows = [{"id": "a"}, {"id": "b"}, {"id": "c"}]
    bounds = {"a": Decimal("0.20"), "b": Decimal("0.30"), "c": Decimal("0.10")}
    assert affordable_batch(rows, bounds, Decimal("0.50")) == rows[:2]
    assert affordable_batch(rows, bounds, Decimal("0.49")) == rows[:1]
    assert affordable_batch(rows, bounds, Decimal("0.19")) == []
