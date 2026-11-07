"""Validated contracts. Rubric IDs and answer ranges are configuration, never code."""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime
from decimal import Decimal
from typing import Annotated, Any, Literal
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field, StrictBool, StrictInt, field_validator, model_validator


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


Text = Annotated[str, Field(min_length=1)]


def nonblank(value: str) -> str:
    if not value.strip():
        raise ValueError("Text must contain non-whitespace characters")
    return value


def numeric(value: Any) -> Any:
    if isinstance(value, bool) or not isinstance(value, (int, float, Decimal, str)):
        raise ValueError("Expected a finite number, not a boolean")
    return value


class Anchor(Contract):
    value: Decimal = Field(ge=0)
    description: Text
    _numeric = field_validator("value", mode="before")(numeric)
    _text = field_validator("description")(nonblank)


class Section(Contract):
    id: Text
    title: Text
    _text = field_validator("id", "title")(nonblank)


class Criterion(Contract):
    id: str = Field(pattern=r"^[A-Za-z0-9_-]{1,80}$")
    name: Text
    description: Text
    section_id: Text
    answer_type: Literal["binary", "scale", "flag"]
    weight: Decimal | None
    na_allowed: StrictBool
    na_condition: str | None
    scale: list[Anchor] = Field(max_length=50)
    _numeric = field_validator("weight", mode="before")(lambda v: None if v is None else numeric(v))
    _text = field_validator("name", "description", "section_id")(nonblank)

    @model_validator(mode="after")
    def valid_configuration(self):
        if self.answer_type == "flag":
            if self.weight is not None or self.na_allowed:
                raise ValueError("Flags must be unscored and cannot be N/A")
        elif self.weight is None or not self.weight.is_finite() or self.weight < 0:
            raise ValueError("Scored criteria require a finite nonnegative weight")
        if self.na_allowed != bool(self.na_condition and self.na_condition.strip()):
            raise ValueError("N/A requires an exact condition; disabled N/A requires an empty condition")
        if self.answer_type == "scale":
            values = [a.value for a in self.scale]
            if not values or len(set(values)) != len(values) or max(values) <= 0:
                raise ValueError("Scale needs distinct nonnegative anchors with a positive maximum")
        elif self.scale:
            raise ValueError("Only numerical scale criteria may have anchors")
        return self


class ScoringPolicy(Contract):
    binary_yes_fraction: Literal[1] = 1
    binary_no_fraction: Literal[0] = 0
    scale_normalization: Literal["value_divided_by_maximum_scale_value"] = "value_divided_by_maximum_scale_value"
    na_handling: Literal["exclude_and_renormalize_applicable_scored_weights_to_100"] = "exclude_and_renormalize_applicable_scored_weights_to_100"
    flag_handling: Literal["separate_from_numeric_score"] = "separate_from_numeric_score"
    final_decimal_places: Literal[2] = 2
    empty_applicable_weight: Literal["not_calculated"] = "not_calculated"


class Checklist(Contract):
    schema_version: Literal[1] = 1
    name: Text
    initial_version_label: str | None = None
    source: dict[str, Any] | None = None
    sections: list[Section] = Field(min_length=1, max_length=30)
    criteria: list[Criterion] = Field(min_length=1, max_length=64)
    scoring_policy: ScoringPolicy = Field(default_factory=ScoringPolicy)
    source_notes: list[str] = Field(default_factory=list)
    _text = field_validator("name")(nonblank)

    @model_validator(mode="after")
    def unique_ids(self):
        for label, values in [("criterion", self.criteria), ("section", self.sections)]:
            if len({v.id for v in values}) != len(values):
                raise ValueError(f"Duplicate {label} IDs")
        if any(c.section_id not in {s.id for s in self.sections} for c in self.criteria):
            raise ValueError("Every criterion must reference a configured section")
        return self


class Message(Contract):
    timestamp: Text
    speaker: Literal["client", "operator", "bot", "system"]
    text: str


class SourceConversation(Contract):
    conversation_id: Text
    channel: Literal["agent chat", "voice call"]
    language: Literal["RU", "KZ", "EN"]
    transcript: list[Message] = Field(min_length=1)
    audio_url: str | None = None
    _text = field_validator("conversation_id")(nonblank)

    @field_validator("audio_url")
    @classmethod
    def safe_audio(cls, value):
        if value is not None:
            parts = urlsplit(value)
            if parts.scheme not in {"http", "https"} or not parts.hostname or parts.username or parts.password:
                raise ValueError("Recording links must be HTTP(S) URLs without userinfo")
        return value

    @model_validator(mode="after")
    def timestamps(self):
        for message in self.transcript:
            if self.channel == "agent chat":
                if not re.fullmatch(r"\d{2,}:[0-5]\d", message.timestamp):
                    raise ValueError("Chat timestamps must be MM:SS")
            else:
                try:
                    stamp = datetime.fromisoformat(message.timestamp.replace("Z", "+00:00"))
                except ValueError:
                    raise ValueError("Call timestamps must be ISO 8601 with timezone") from None
                if "T" not in message.timestamp or stamp.tzinfo is None:
                    raise ValueError("Call timestamps require an ISO 8601 timezone")
        return self


class ImportData(Contract):
    dataset_group_id: Text
    total_records: StrictInt = Field(ge=0)
    records: list[SourceConversation]
    _text = field_validator("dataset_group_id")(nonblank)

    @model_validator(mode="after")
    def consistent(self):
        if len(self.records) != self.total_records:
            raise ValueError("total_records does not match records length; no records imported")
        ids = [r.conversation_id for r in self.records]
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate conversation_id in payload; no records imported")
        return self


class ImportEnvelope(Contract):
    error: str
    isSuccess: StrictBool
    data: ImportData

    @model_validator(mode="after")
    def success(self):
        if not self.isSuccess or self.error.strip():
            raise ValueError("Organizer returned an unsuccessful response; no records imported")
        return self


class Evidence(Contract):
    kind: Literal["support", "absence", "context"]
    start_message_id: Text
    end_message_id: Text


class Judgment(Contract):
    disposition: Literal["assessed", "not_applicable", "needs_review"]
    # Keep input type intact. Semantic validation below rejects bool as scale and int as boolean.
    value: Any
    explanation: Text
    na_reason: str | None
    review_reason: str | None
    evidence: list[Evidence]
    _text = field_validator("explanation")(nonblank)


class Assessment(Contract):
    results: dict[str, Judgment]


def validate_judgment(criterion: Criterion, judgment: Judgment, message_ids: list[str] | None = None):
    if judgment.disposition == "assessed":
        if judgment.na_reason is not None or judgment.review_reason is not None:
            raise ValueError("An assessed answer cannot have N/A or review reasons")
        if criterion.answer_type == "scale":
            if isinstance(judgment.value, bool) or not isinstance(judgment.value, (int, float, Decimal)):
                raise ValueError(f"{criterion.id}: expected an allowed numeric scale value")
            value = Decimal(str(judgment.value))
            if not value.is_finite() or value not in {a.value for a in criterion.scale}:
                raise ValueError(f"{criterion.id}: value is not a configured scale anchor")
        elif type(judgment.value) is not bool:
            raise ValueError(f"{criterion.id}: binary and flag values must be strict booleans")
    elif judgment.disposition == "not_applicable":
        if not criterion.na_allowed or judgment.value is not None or not (judgment.na_reason or "").strip() or judgment.review_reason is not None:
            raise ValueError(f"{criterion.id}: N/A is forbidden or lacks an explicit condition justification")
    else:
        if judgment.value is not None or not (judgment.review_reason or "").strip() or judgment.na_reason is not None:
            raise ValueError(f"{criterion.id}: unresolved answers require a missing-basis reason and null value")
    if judgment.disposition != "needs_review" and not judgment.evidence:
        raise ValueError(f"{criterion.id}: resolved decisions need evidence, including for absence and N/A")
    if message_ids is not None:
        positions = {mid: i for i, mid in enumerate(message_ids)}
        for evidence in judgment.evidence:
            start, end = positions.get(evidence.start_message_id), positions.get(evidence.end_message_id)
            if start is None or end is None or start > end:
                raise ValueError(f"{criterion.id}: evidence range is missing or reversed")


def validate_assessment(checklist: Checklist, assessment: Assessment, message_ids: list[str] | None = None):
    if set(assessment.results) != {c.id for c in checklist.criteria}:
        raise ValueError("Assessment must cover exactly the configured criterion IDs")
    for criterion in checklist.criteria:
        validate_judgment(criterion, assessment.results[criterion.id], message_ids)


def canonical_json(value: Any) -> str:
    if isinstance(value, BaseModel):
        value = value.model_dump(mode="json")
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def content_hash(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()
