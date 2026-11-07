"""Literal source-text search, with source-based snippets and message identifiers."""
import unicodedata


def folded(text):
    return unicodedata.normalize("NFC", text).casefold()


def _mapped_fold(text):
    """Fold clusters while retaining offsets into verbatim source code points."""
    clusters = []
    for index, char in enumerate(text):
        if clusters and (unicodedata.combining(char) or
                         unicodedata.normalize("NFC", clusters[-1][1] + char) !=
                         unicodedata.normalize("NFC", clusters[-1][1]) + unicodedata.normalize("NFC", char)):
            clusters[-1][1] += char
        else:
            clusters.append([index, char])
    parts, positions = [], []
    for start, cluster in clusters:
        part = folded(cluster)
        parts.append(part)
        positions.extend([(start, start + len(cluster))] * len(part))
    return "".join(parts), positions


def search_messages(messages, query, speaker="all", limit=5, offset=0):
    query = query.strip()
    if not query and speaker == "all":
        return [], 0
    needle, matches, total = folded(query), [], 0
    for message in messages:
        if speaker != "all" and message["speaker"] != speaker:
            continue
        text = message["text"]
        if needle and needle not in folded(text):
            continue
        ordinal = total
        total += 1
        # Count every matching message but build snippets/maps only for the requested page.
        if ordinal < offset or len(matches) >= limit:
            continue
        haystack, positions = _mapped_fold(text) if needle else ("", [])
        hit = haystack.find(needle) if needle else 0
        if hit < 0:
            raise ValueError("The search match could not be mapped to source text")
        start = positions[hit][0] if positions and needle else 0
        end = positions[hit + len(needle) - 1][1] if needle else 0
        lo, hi = max(0, start - 70), min(len(text), max(end + 70, start + 160))
        prefix = "…" if lo else ""
        spans = []
        while needle and hit >= 0:
            a, b = positions[hit][0], positions[hit + len(needle) - 1][1]
            if a >= hi:
                break
            if b > lo:
                span = {"start": len(prefix) + max(a, lo) - lo, "end": len(prefix) + min(b, hi) - lo}
                if spans and span["start"] <= spans[-1]["end"]:
                    spans[-1]["end"] = max(spans[-1]["end"], span["end"])
                else:
                    spans.append(span)
            hit = haystack.find(needle, hit + len(needle))
        matches.append({"id": message["id"], "speaker": message["speaker"], "timestamp": message["timestamp"],
                        "snippet": prefix + text[lo:hi] + ("…" if hi < len(text) else ""), "highlights": spans})
    return matches, total
