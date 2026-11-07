"""Literal source-text search, with source-based snippets and message identifiers."""
import unicodedata


def folded(text):
    return unicodedata.normalize("NFC", text).casefold()


def search_messages(messages, query, speaker="all", limit=5):
    query = query.strip()
    if not query and speaker == "all":
        return [], 0
    needle, matches = folded(query), []
    for message in messages:
        if speaker != "all" and message["speaker"] != speaker:
            continue
        text = message["text"]
        if needle and needle not in folded(text):
            continue
        # Map normalized/casefolded clusters back to source offsets (e.g. Й/И+breve, ß/ss, İ).
        clusters = []
        for index, char in enumerate(text):
            if clusters and unicodedata.combining(char):
                clusters[-1][1] += char
            else:
                clusters.append([index, char])
        parts, positions = [], []
        for start, cluster in clusters:
            part = folded(cluster)
            parts.append(part)
            positions.extend([(start, start + len(cluster))] * len(part))
        hit = "".join(parts).find(needle) if needle else 0
        if hit < 0:
            continue
        start = positions[hit][0] if positions and needle else 0
        end = positions[hit + len(needle) - 1][1] if needle else 0
        lo, hi = max(0, start - 70), min(len(text), max(end + 70, start + 160))
        matches.append({"id": message["id"], "speaker": message["speaker"], "timestamp": message["timestamp"],
                        "snippet": ("…" if lo else "") + text[lo:hi] + ("…" if hi < len(text) else "")})
    return matches[:limit], len(matches)
