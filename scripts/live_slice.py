"""Run one actual imported conversation against the configured provider via the local API.

No synthetic fallback. Full result is written only to ignored local_data/live_runs/.
"""
import argparse
import json
from pathlib import Path
import sys
import time

import httpx

ROOT = Path(__file__).resolve().parents[1]


def checked(response):
    if response.status_code >= 400:
        detail = response.json().get("detail", "Local API request failed")
        raise SystemExit(json.dumps({"http_status": response.status_code, "detail": detail}, ensure_ascii=False))
    return response.json()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-id", required=True)
    parser.add_argument("--group", default="DEV")
    parser.add_argument("--checklist", type=int, default=1)
    parser.add_argument("--fresh", action="store_true", help="Bypass assessment cache (makes a paid provider call)")
    args = parser.parse_args()
    with httpx.Client(base_url="http://127.0.0.1:8000", timeout=30) as client:
        access = checked(client.get("/api/access"))
        if not access["provider_configured"]:
            raise SystemExit(access["provider_status"] + "; no provider request sent")
        rows = checked(client.get("/api/conversations"))
        candidates = [row for row in rows if row["source_id"] == args.source_id and row["group_id"] == args.group]
        if len(candidates) != 1:
            raise SystemExit("Expected exactly one imported source revision; no evaluation started")
        result = checked(client.post("/api/evaluations", json={"conversation_ids": [candidates[0]["id"]], "checklist_id": args.checklist, "reuse_cache": not args.fresh}))
        evaluation_id = result["evaluation_ids"][0]
        print(json.dumps({"evaluation_id": evaluation_id, "state": "submitted"}), flush=True)
        deadline = time.monotonic() + 900
        while time.monotonic() < deadline:
            result = checked(client.get("/api/evaluations/" + evaluation_id))
            if result["state"] not in {"queued", "running"}:
                directory = ROOT / "local_data/live_runs"
                directory.mkdir(exist_ok=True, parents=True)
                (directory / (evaluation_id + ".json")).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
                print(json.dumps({key: result[key] for key in ["id", "state", "completeness", "total", "cached_from", "error", "usage"]}, ensure_ascii=False, indent=2))
                raise SystemExit(0 if result["state"] == "succeeded" else 1)
            time.sleep(1)
        raise SystemExit("Wait limit reached; job remains persisted. Inspect the local UI; no fallback assessment created.")
