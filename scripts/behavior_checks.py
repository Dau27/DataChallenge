"""Run synthetic behavioral diagnostics through the actual configured hosted provider.

Expectations are provisional agent labels, not human ground truth or an accuracy benchmark.
Never run these in place of the mandatory real DEV slice. This command can incur provider charges.
"""
from collections import Counter
import json
from pathlib import Path
import time

import httpx

ROOT = Path(__file__).resolve().parents[1]


def checked(response):
    if response.status_code >= 400:
        raise SystemExit(f"Local API HTTP {response.status_code}: {response.json().get('detail')}")
    return response.json()


if __name__ == "__main__":
    payload = json.loads((ROOT / "tests/fixtures/semantic_cases.json").read_text(encoding="utf-8"))
    expected = json.loads((ROOT / "tests/fixtures/semantic_expectations.json").read_text(encoding="utf-8"))
    with httpx.Client(base_url="http://127.0.0.1:8000", timeout=30) as client:
        access = checked(client.get("/api/access"))
        if not access["provider_configured"]:
            raise SystemExit(access["provider_status"] + "; no synthetic diagnostics or inference started")
        imported = checked(client.post("/api/import/json", json=payload))
        rows = checked(client.get("/api/conversations"))
        source_ids = {row["id"]: row["source_id"] for row in rows}
        versions = checked(client.get("/api/checklists"))
        # Expectations belong specifically to the original rubric; do not reinterpret a modified rubric.
        ids = checked(client.post("/api/evaluations", json={"conversation_ids": imported["conversation_ids"], "checklist_id": 1}))["evaluation_ids"]
        results, pending = {}, set(ids)
        deadline = time.monotonic() + 1800
        while pending and time.monotonic() < deadline:
            for evaluation_id in list(pending):
                result = checked(client.get("/api/evaluations/" + evaluation_id))
                if result["state"] not in {"queued", "running"}:
                    results[source_ids[result["conversation_id"]]] = result
                    pending.remove(evaluation_id)
            if pending:
                time.sleep(1)
        checks = []
        for source_id, criteria in expected["cases"].items():
            result = results.get(source_id)
            for criterion_id, fields in criteria.items():
                actual = (result.get("original") or {}).get("results", {}).get(criterion_id) if result else None
                checks.append({"source_id": source_id, "criterion_id": criterion_id,
                               "matches_provisional_expectation": bool(actual and all(actual.get(k) == v for k, v in fields.items())),
                               "execution_state": result["state"] if result else "pending", "expected": fields,
                               "actual": actual, "cached_from": result.get("cached_from") if result else None})
        report = {"label_provenance": expected["label_provenance"], "checks": checks, "pending_evaluation_ids": sorted(pending),
                  "execution_states": dict(Counter(result["state"] for result in results.values()))}
        output = ROOT / "local_data/behavior_report.json"
        output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps({"report": str(output), "checks": len(checks), "provisional_matches": sum(c["matches_provisional_expectation"] for c in checks),
                          "execution_states": report["execution_states"], "pending": len(pending), "human_reviewed": False}, indent=2))
