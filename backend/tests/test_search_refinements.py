from backend.tests.test_saved_inspection import saved, db_rows
from backend.tests.test_workflow import synthetic_payload
from backend.app.services.search import search_messages
import pytest


def test_match_pagination_preserves_source_order_full_count_and_rows(saved):
    client, db, _, _, _ = saved
    payload = synthetic_payload(source_id="PAGED_SEARCH_TEST")
    payload["data"]["records"][0]["transcript"] = [
        {"speaker": "operator" if i % 2 == 0 else "client", "timestamp": "00:00", "text": f"TEST literal [.*] message {i}"}
        for i in range(16)]
    cid = client.post("/api/import/json", json=payload).json()["conversation_ids"][0]
    before = db_rows(db)
    params = {"q": "[.*]", "speaker": "operator", "limit": 5}
    first = client.get(f"/api/conversations/{cid}/matches", params=params).json()
    second = client.get(f"/api/conversations/{cid}/matches", params={**params, "offset": 5}).json()
    assert first["total_matches"] == second["total_matches"] == 8
    assert first["source"]["id"] == second["source"]["id"] == cid
    assert [m["id"] for m in first["matches"] + second["matches"]] == [f"m{i:04d}" for i in range(1, 17, 2)]
    assert first["source"]["content_hash"] == second["source"]["content_hash"]
    assert client.get(f"/api/conversations/{cid}/matches", params={**params, "offset": 100}).json()["matches"] == []
    # Speaker-only navigation counts all matching messages without normalizing empty search text.
    roles = client.get(f"/api/conversations/{cid}/matches?speaker=client&offset=5").json()
    assert roles["total_matches"] == 8 and len(roles["matches"]) == 3
    assert all(m["highlights"] == [] for m in roles["matches"])
    for query in ("offset=-1", "limit=0", "limit=26", "offset=1000001", "speaker=admin", "q=" + "x" * 201):
        assert client.get(f"/api/conversations/{cid}/matches?{query}").status_code == 422
    assert client.get("/api/conversations/absent/matches?q=test").status_code == 404
    assert db_rows(db) == before


@pytest.mark.parametrize("text,query,expected", [
    ("👋 И\u0306 Й", "й", ["И\u0306", "Й"]),
    ("👋 Straße STRASSE", "strasse", ["Straße", "STRASSE"]),
    ("👋 İ i", "i", ["İ", "i"]),
    ("👋 ҚАЗАҚША қазақша", "қазақша", ["ҚАЗАҚША", "қазақша"]),
    ("👋 가 가", "가", ["가", "가"]),
])
def test_highlight_offsets_map_verbatim_unicode_source(text, query, expected):
    matches, count = search_messages([{"id": "m0001", "speaker": "operator", "timestamp": "00:00", "text": text}], query)
    assert count == 1 and matches[0]["snippet"] == text
    assert [text[s["start"]:s["end"]] for s in matches[0]["highlights"]] == expected


def test_snippets_are_bounded_with_source_offsets_and_all_messages_counted():
    text = "x" * 250 + " ҚАЗАҚША " + "y" * 250
    messages = [{"id": f"m{i:04d}", "speaker": "operator", "timestamp": "00:00", "text": text} for i in range(1, 20)]
    matches, total = search_messages(messages, "қазақша", limit=5, offset=10)
    assert total == 19 and [m["id"] for m in matches] == [f"m{i:04d}" for i in range(11, 16)]
    assert all(m["snippet"].startswith("…") and m["snippet"].endswith("…") and len(m["snippet"]) < 250 for m in matches)
    for match in matches:
        assert [match["snippet"][s["start"]:s["end"]] for s in match["highlights"]] == ["ҚАЗАҚША"]
