from decimal import Decimal

from backend.app.config import Settings
from scripts.run_dev import four_attempt_bound


def test_budget_reservation_covers_all_four_attempts(checklist, tmp_path):
    settings = Settings(database_path=tmp_path / "test.sqlite3", input_rate=Decimal("0.75"), output_rate=Decimal("4.50"), max_output_tokens=6000)
    snapshot = {"transcript": [{"id": "m0001", "speaker": "client", "timestamp": "00:00", "text": "SYNTHETIC budget test"}]}
    bound = four_attempt_bound(settings, snapshot, checklist)
    # Even ignoring all input, reserve four full output limits, including possible repairs/retries.
    assert bound > 4 * Decimal(6000) * Decimal("4.50") / Decimal(1_000_000)
    larger = {"transcript": [{"id": "m0001", "speaker": "client", "timestamp": "00:00", "text": "SYNTHETIC " * 1000}]}
    assert four_attempt_bound(settings, larger, checklist) > bound
