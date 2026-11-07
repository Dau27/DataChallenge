"""Read-only draft validation and complete saved-versus-draft configuration differences."""
from pydantic import ValidationError
from backend.app.domain import Checklist


def field_issues(error, draft):
    issues = []
    for item in error.errors(include_input=False, include_context=False, include_url=False):
        path, message = list(item["loc"]), item["msg"]
        if len(path) == 2 and path[0] == "criteria":
            field = ("weight" if "weight" in message.lower() or "unscored" in message.lower() else
                     "na_condition" if "N/A" in message else "scale" if "Scale" in message or "anchors" in message else None)
            if field:
                path.append(field)
        if not path and ("unknown section" in message.lower() or "configured section" in message.lower()):
            sections = {s.get("id") for s in draft.get("sections", []) if isinstance(s, dict)}
            issues.extend({"location": ["criteria", i, "section_id"], "message": message}
                          for i, c in enumerate(draft.get("criteria", [])) if isinstance(c, dict) and c.get("section_id") not in sections)
            continue
        issues.append({"location": path, "message": message})
    labels = {"name": "Name", "description": "Definition", "weight": "Weight", "answer_type": "Answer type",
              "section_id": "Section", "na_allowed": "N/A allowed", "na_condition": "N/A condition", "scale": "Scale anchors",
              "value": "Value", "title": "Title", "criteria": "Criteria", "sections": "Sections"}
    for issue in issues:
        path = issue["location"]
        if len(path) >= 2 and path[0] in {"criteria", "sections"} and isinstance(path[1], int):
            collection = draft.get(path[0], [])
            item = collection[path[1]] if path[1] < len(collection) and isinstance(collection[path[1]], dict) else {}
            prefix = item.get("name") or item.get("title") or f"{path[0].title()} {path[1] + 1}"
            issue["label"] = str(prefix) + " / " + " / ".join(labels.get(p, p) if isinstance(p, str) else str(p + 1) for p in path[2:])
        else:
            issue["label"] = " / ".join(labels.get(str(p), str(p)) for p in path) or "Checklist"
    return issues


def configuration_diff(before, after):
    changes = []
    labels = {"name": "Name", "description": "Definition", "section_id": "Section", "answer_type": "Answer type",
              "weight": "Weight", "na_allowed": "N/A allowed", "na_condition": "N/A condition", "scale": "Scale anchors",
              "value": "Value", "title": "Title", "source_notes": "Source notes", "scoring_policy": "Scoring policy"}
    def walk(old, new, path, label):
        if old == new:
            return
        if isinstance(old, dict) and isinstance(new, dict):
            for key in sorted(old.keys() | new.keys()):
                walk(old.get(key), new.get(key), path + [key], label + " / " + labels.get(key, key))
        elif isinstance(old, list) and isinstance(new, list):
            for i in range(max(len(old), len(new))):
                walk(old[i] if i < len(old) else None, new[i] if i < len(new) else None, path + [i], label + f" / {i + 1}")
        else:
            changes.append({"location": path, "label": label, "before": old, "after": new})
    for field in sorted(before.keys() | after.keys()):
        old, new = before.get(field), after.get(field)
        if field in {"criteria", "sections"} and isinstance(old, list) and isinstance(new, list) and all(isinstance(v, dict) and isinstance(v.get("id"), str) for v in old + new):
            old_map, new_map = {v["id"]: v for v in old}, {v["id"]: v for v in new}
            if len(old_map) != len(old) or len(new_map) != len(new):
                walk(old, new, [field], field.title())
                continue
            old_ids, new_ids = [v["id"] for v in old], [v["id"] for v in new]
            if old_ids != new_ids:
                changes.append({"location": [field, "order"], "label": field.title() + " order / membership",
                                "before": [v.get("name", v.get("title", v["id"])) for v in old],
                                "after": [v.get("name", v.get("title", v["id"])) for v in new]})
            for key in dict.fromkeys(old_ids + new_ids):
                item = new_map.get(key) or old_map[key]
                walk(old_map.get(key), new_map.get(key), [field, key], str(item.get("name") or item.get("title") or key))
        else:
            walk(old, new, [field], labels.get(field, field.replace("_", " ").title()))
    return changes


def preview_checklist(saved, draft):
    try:
        Checklist.model_validate(draft)
        errors = []
    except ValidationError as error:
        errors = field_issues(error, draft)
    return {"valid": not errors, "errors": errors, "changes": configuration_diff(saved, draft)}
