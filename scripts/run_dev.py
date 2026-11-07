"""Process actual DEV through the local API with a conservative USD spending guard.

Uses configured identified rates and actual usage. Unknown usage retains a worst-case
reservation. Stops before a new job if its four-attempt upper bound exceeds the budget.
Budget is for application evaluation calls, not unrelated account usage or GPU rental.
"""
import argparse
from collections import Counter
from decimal import Decimal
import json
from pathlib import Path
import sys
import time

import httpx

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.app.config import Settings
from backend.app.domain import Checklist, canonical_json
from backend.app.services.evaluator import INSTRUCTIONS, output_schema


def checked(response):
    if response.status_code >= 400:
        raise SystemExit(f"Local API HTTP {response.status_code}: {response.json().get('detail')}")
    return response.json()


def four_attempt_bound(settings, snapshot, checklist):
    # Byte-level tokenizers cannot produce more text tokens than UTF-8 bytes. Allow
    # another 4096 input tokens for protocol/schema/repair framing on every attempt.
    body = canonical_json({"instructions": INSTRUCTIONS, "conversation": snapshot,
                           "checklist": checklist.model_dump(mode="json"), "schema": output_schema(checklist)})
    input_upper = len(body.encode("utf-8")) + 4096
    return 4 * (Decimal(input_upper) * settings.input_rate + Decimal(settings.max_output_tokens) * settings.output_rate) / Decimal(1_000_000)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--budget-usd", type=Decimal, default=Decimal("4.00"))
    parser.add_argument("--checklist", type=int, default=1)
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
        rows = [r for r in checked(client.get("/api/conversations")) if r["group_id"] == "DEV"]
        snapshots = {r["id"]: checked(client.get("/api/conversations/" + r["id"]))["snapshot"] for r in rows}
        known_spend = Decimal(0)
        unknown_reserved = Decimal(0)
        # Include previous diagnostics/configuration demonstrations in the application-wide guard.
        for previous in checked(client.get("/api/evaluations")):
            result = checked(client.get("/api/evaluations/" + previous["id"]))
            usage = result["usage"]
            if usage["estimated_cost_usd"] is not None:
                known_spend += Decimal(usage["estimated_cost_usd"])
            elif usage["request_attempts"]:
                snapshot = checked(client.get("/api/conversations/" + previous["conversation_id"]))["snapshot"]
                unknown_reserved += four_attempt_bound(settings, snapshot, Checklist.model_validate(result["checklist"]["snapshot"]))
        # Keep $0.10 for access checks and framing uncertainty outside evaluation job records.
        overhead_reserve = Decimal("0.10")
        report = {"group": "DEV", "model": settings.model, "checklist_id": args.checklist,
                  "budget_usd": str(args.budget_usd), "cost_rate_source": settings.rate_source,
                  "records": [], "stopped_for_budget": False}
        for index, row in enumerate(rows, 1):
            bound = four_attempt_bound(settings, snapshots[row["id"]], checklist)
            if known_spend + unknown_reserved + overhead_reserve + bound > args.budget_usd:
                report["stopped_for_budget"] = True
                report["records"].extend({"source_id": remaining["source_id"], "state": "not_started_budget_guard"} for remaining in rows[index - 1:])
                break
            started = checked(client.post("/api/evaluations", json={"conversation_ids": [row["id"]], "checklist_id": args.checklist}))
            evaluation_id = started["evaluation_ids"][0]
            deadline = time.monotonic() + 600
            while True:
                result = checked(client.get("/api/evaluations/" + evaluation_id))
                if result["state"] not in {"queued", "running"}:
                    break
                if time.monotonic() > deadline:
                    raise SystemExit("Job remains persisted but exceeded the wait guard; no next job started")
                time.sleep(1)
            usage = result["usage"]
            if usage["estimated_cost_usd"] is not None:
                known_spend += Decimal(usage["estimated_cost_usd"])
            elif usage["request_attempts"]:
                unknown_reserved += bound
            report["records"].append({"source_id": row["source_id"], "language": row["language"], "channel": row["channel"],
                                      "evaluation_id": evaluation_id, "state": result["state"], "completeness": result["completeness"],
                                      "total": result["total"], "cached_from": result["cached_from"], "usage": usage, "error": result["error"]})
            if index % 5 == 0 or index == len(rows):
                print(json.dumps({"processed": index, "of": len(rows), "known_application_estimate_usd": str(known_spend), "unknown_cost_reserved_usd": str(unknown_reserved)}), flush=True)
            report.update(known_application_estimate_usd=str(known_spend), unknown_cost_reserved_usd=str(unknown_reserved))
            (ROOT / "local_data/dev_run.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        report["states"] = dict(Counter(r["state"] for r in report["records"]))
        report["completeness"] = dict(Counter(r.get("completeness", "not_started") for r in report["records"]))
        report.update(known_application_estimate_usd=str(known_spend), unknown_cost_reserved_usd=str(unknown_reserved))
        (ROOT / "local_data/dev_run.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps({k: v for k, v in report.items() if k != "records"}, indent=2), flush=True)
