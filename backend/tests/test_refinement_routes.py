import csv
import io
import pytest
from backend.tests.test_saved_inspection import saved, db_rows


@pytest.mark.parametrize("format", ["json", "csv", "simple_csv"])
def test_selected_export_route_returns_exact_saved_selection_atomically(saved, format):
    client, db, _, _, _ = saved
    before = db_rows(db)
    response = client.get("/api/evaluations/export-batch", params=[("evaluation_id", "right"), ("evaluation_id", "left"), ("format", format)])
    assert response.status_code == 200, response.text
    assert response.headers["cache-control"] == "no-store" and response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["content-disposition"].endswith('.json"' if format == "json" else '.csv"')
    if format == "json":
        packet = response.json()
        assert [r["evaluation_id"] for r in packet["manifest"]["runs"]] == ["right", "left"]
        assert [r["evaluation"]["id"] for r in packet["reports"]] == ["right", "left"]
    else:
        rows = list(csv.DictReader(io.StringIO(response.content.decode("utf-8-sig"))))
        if format == "simple_csv":
            assert len(rows) == 32 and {r["evaluation_id"] for r in rows[:16]} == {"right"}
        else:
            assert rows[0]["record_type"] == "batch_manifest"
            assert {r["evaluation_id"] for r in rows if r["record_type"] == "criterion"} == {"right", "left"}
    assert db_rows(db) == before


def test_export_route_validation_and_single_simple_csv_keep_rows(saved):
    client, db, _, _, _ = saved
    before = db_rows(db)
    for query in [[], [("evaluation_id", "")], [("evaluation_id", "left"), ("evaluation_id", "left")],
                  [("evaluation_id", "x" * 201)], [("evaluation_id", str(i)) for i in range(101)],
                  [("evaluation_id", "left"), ("format", "pdf")]]:
        assert client.get("/api/evaluations/export-batch", params=query).status_code == 422
    assert client.get("/api/evaluations/export-batch", params=[("evaluation_id", "left"), ("evaluation_id", "missing")]).status_code == 404
    response = client.get("/api/evaluations/left/export?format=simple_csv")
    assert response.status_code == 200 and '-criteria.csv"' in response.headers["content-disposition"]
    assert len(list(csv.DictReader(io.StringIO(response.content.decode("utf-8-sig"))))) == 16
    assert db_rows(db) == before
