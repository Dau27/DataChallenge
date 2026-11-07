"""Process actual DEV through the local API with a conservative USD spending guard.

Uses configured identified rates and actual usage. Unknown usage retains a worst-case
reservation. Stops before a new job if its four-attempt upper bound exceeds the budget.
Budget is for application evaluation calls, not unrelated account usage or GPU rental.
"""
import argparse
from collections import Counter
from decimal import Decimal
from dataclasses import replace
import json
from pathlib import Path
import sys
import time

import httpx

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.app.config import Settings
from backend.app.domain import Checklist, canonical_json
from backend.app.services.evaluator import INSTRUCTIONS, operator_focus, output_schema


def checked(response):
    if response.status_code >= 400:
        raise SystemExit(f"Local API HTTP {response.status_code}: {response.json().get('detail')}")
    return response.json()


def four_attempt_bound(settings, snapshot, checklist):
    # Byte-level tokenizers cannot produce more text tokens than UTF-8 bytes. Allow
    # another 4096 input tokens for protocol/schema/repair framing on every attempt.
    body = canonical_json({"instructions": INSTRUCTIONS, "conversation": snapshot,
                           "operator_focus_untrusted": operator_focus(snapshot),
                           "checklist": checklist.model_dump(mode="json"),
                           "schema": output_schema(checklist, [m["id"] for m in snapshot.get("transcript", [])])})
    input_upper = len(body.encode("utf-8")) + 4096
    return 4 * (Decimal(input_upper) * settings.input_rate + Decimal(settings.max_output_tokens) * settings.output_rate) / Decimal(1_000_000)


def historical_attempt_bound(settings, result, snapshot):
    """Reserve actual past attempts at their original rates/settings, not hypothetical future repairs."""
    meta = result["metadata"]
    rate = meta.get("rate", {})
    if any(rate.get(key) is None for key in ["input_usd_per_million", "output_usd_per_million"]):
        raise ValueError("Historical unknown usage lacks identified rates; budget cannot safely resume")
    historical = replace(settings, input_rate=Decimal(rate["input_usd_per_million"]),
                         output_rate=Decimal(rate["output_usd_per_million"]),
                         max_output_tokens=meta["generation"]["max_output_tokens"])
    fallback = four_attempt_bound(historical, snapshot, Checklist.model_validate(result["checklist"]["snapshot"])) / 4
    reservation = Decimal(0)
    for attempt in result["attempts"]:
        if attempt.get("input_token_upper_bound") is not None and attempt.get("max_output_tokens") is not None:
            reservation += (Decimal(attempt["input_token_upper_bound"]) * historical.input_rate +
                            Decimal(attempt["max_output_tokens"]) * historical.output_rate) / Decimal(1_000_000)
        else:
            reservation += fallback
    return reservation


def affordable_batch(rows, bounds, available, maximum=2):
    selected, reserved = [], Decimal(0)
    for row in rows[:maximum]:
        if reserved + bounds[row["id"]] > available:
            break
        selected.append(row)
        reserved += bounds[row["id"]]
    return selected


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--budget-usd", type=Decimal, default=Decimal("4.00"))
    parser.add_argument("--checklist", type=int, default=1)
    parser.add_argument("--only-missing", action="store_true", help="Keep existing succeeded assessments; create new jobs only for unfinished records")
    args = parser.parse_args()
    settings = Settings.from_env()
    if not settings.provider_ready or settings.input_rate is None or settings.output_rate is None or not settings.rate_source:
        raise SystemExit("A real provider and identified configured cost rates are required for the budget guard")
    if not args.budget_usd.is_finite() or args.budget_usd <= 0 or args.budget_usd > Decimal("4.00"):
        raise SystemExit("Use a positive budget of at most $4.00, preserving headroom below the user's $5 balance")
    with httpx.Client(base_url="http://127.0.0.1:8000", timeout=30) as client:
        access = checked(client.get("/api/access"))
        if not access["provider_configured"]:
            raise SystemExit(access["provider_status"])
        versions = checked(client.get("/api/checklists"))
        checklist = Checklist.model_validate(next(v["snapshot"] for v in versions if v["id"] == args.checklist))
        rows = [r for r in checked(client.get(f"/api/conversations?checklist_id={args.checklist}")) if r["group_id"] == "DEV"]
        report = {"group": "DEV", "active_model": settings.model, "checklist_id": args.checklist,
                  "budget_usd": str(args.budget_usd), "cost_rate_source": settings.rate_source,
                  "records": [], "stopped_for_budget": False, "stopped_for_provider": False}
        def result_record(row, result, existing=False):
            return {"source_id": row["source_id"], "language": row["language"], "channel": row["channel"],
                    "evaluation_id": result["id"], "state": result["state"], "completeness": result["completeness"],
                    "total": result["total"], "model": result["metadata"]["model"], "existing_assessment": existing,
                    "cached_from": result["cached_from"], "usage": result["usage"], "error": result["error"]}

        remaining = []
        for row in rows:
            if args.only_missing and row.get("evaluation") and row["evaluation"]["state"] == "succeeded":
                result = checked(client.get("/api/evaluations/" + row["evaluation"]["id"]))
                report["records"].append(result_record(row, result, True))
            else:
                remaining.append(row)
        while remaining:
            batch = remaining[:min(settings.concurrency, 2)]
            preview = checked(client.post("/api/evaluations/preview", json={"conversation_ids": [row["id"] for row in batch], "checklist_id": args.checklist}))
            status = preview["budget"]
            required = Decimal(preview["required_reservation_usd"] or "0")
            accounted = sum(Decimal(status[k]) for k in ["accounted_usd", "reserved_usd", "overhead_usd"])
            if not preview["affordable"] or (required and accounted + required > args.budget_usd):
                report["stopped_for_budget"] = True
                report["budget_reason"] = preview["blocked_reason"] or "CLI ceiling would be exceeded"
                report["records"].extend({"source_id": row["source_id"], "state": "not_started_budget_guard"} for row in remaining)
                break
            response = client.post("/api/evaluations", json={"conversation_ids": [row["id"] for row in batch], "checklist_id": args.checklist})
            if response.status_code == 409 and response.json().get("code") == "BUDGET_BLOCKED":
                report["stopped_for_budget"], report["budget_reason"] = True, response.json()["detail"]
                report["records"].extend({"source_id": row["source_id"], "state": "not_started_budget_guard"} for row in remaining)
                break
            started = checked(response)
            pending = dict(zip(started["evaluation_ids"], batch))
            remaining = remaining[len(batch):]
            deadline = time.monotonic() + 600
            provider_block = False
            while pending:
                for evaluation_id, row in list(pending.items()):
                    result = checked(client.get("/api/evaluations/" + evaluation_id))
                    if result["state"] in {"queued", "running"}:
                        continue
                    report["records"].append(result_record(row, result))
                    provider_block |= result["state"] == "failed" and any(400 <= a.get("http_status", 0) < 500 for a in result["attempts"])
                    del pending[evaluation_id]
                if time.monotonic() > deadline:
                    raise SystemExit("Jobs remain persisted but exceeded the wait guard; no next batch started")
                if pending:
                    time.sleep(1)
            print(json.dumps({"processed": len(report["records"]), "of": len(rows), "shared_budget": checked(client.get("/api/budget"))}), flush=True)
            report["shared_budget"] = checked(client.get("/api/budget"))
            (ROOT / "local_data/dev_run.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
            if provider_block:
                report["stopped_for_provider"] = True
                report["records"].extend({"source_id": row["source_id"], "state": "not_started_provider_backoff"} for row in remaining)
                break
        report["states"] = dict(Counter(r["state"] for r in report["records"]))
        report["completeness"] = dict(Counter(r.get("completeness", "not_started") for r in report["records"]))
        report["models"] = dict(Counter(r.get("model", "not_started") for r in report["records"]))
        report["shared_budget"] = checked(client.get("/api/budget"))
        (ROOT / "local_data/dev_run.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps({k: v for k, v in report.items() if k != "records"}, indent=2), flush=True)
