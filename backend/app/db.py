from contextlib import contextmanager
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import JSON, Boolean, ForeignKey, Index, Integer, String, UniqueConstraint, create_engine, event, inspect, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker


def now():
    return datetime.now(timezone.utc).isoformat()


def uid():
    return uuid4().hex


class Base(DeclarativeBase):
    pass


class AccessCheck(Base):
    __tablename__ = "provider_access_checks"
    identity_hash: Mapped[str] = mapped_column(String, primary_key=True)
    report: Mapped[dict] = mapped_column(JSON)


class BudgetState(Base):
    __tablename__ = "budget_state"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    opening_usd: Mapped[str] = mapped_column(String)
    coverage: Mapped[dict] = mapped_column(JSON)
    provenance: Mapped[str] = mapped_column(String)
    created_at: Mapped[str] = mapped_column(String, default=now)


class BudgetReservation(Base):
    __tablename__ = "budget_reservations"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    kind: Mapped[str] = mapped_column(String)
    source_id: Mapped[str] = mapped_column(String, index=True)
    state: Mapped[str] = mapped_column(String, default="reserved")
    reserved_usd: Mapped[str] = mapped_column(String)
    accounted_usd: Mapped[str] = mapped_column(String, default="0")
    rate: Mapped[dict] = mapped_column(JSON)
    max_attempts: Mapped[int] = mapped_column(Integer)
    attempt_offset: Mapped[int] = mapped_column(Integer, default=0)
    attempts: Mapped[list] = mapped_column(JSON, default=list)
    report_hash: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[str] = mapped_column(String, default=now)
    updated_at: Mapped[str] = mapped_column(String, default=now)


class Conversation(Base):
    __tablename__ = "conversation_revisions"
    __table_args__ = (UniqueConstraint("group_id", "source_id", "content_hash"), UniqueConstraint("group_id", "source_id", "revision"))
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    group_id: Mapped[str] = mapped_column(String, index=True)
    source_id: Mapped[str] = mapped_column(String, index=True)
    revision: Mapped[int] = mapped_column(Integer)
    content_hash: Mapped[str] = mapped_column(String)
    snapshot: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[str] = mapped_column(String, default=now)


class ChecklistVersion(Base):
    __tablename__ = "checklist_versions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    content_hash: Mapped[str] = mapped_column(String, index=True)
    snapshot: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[str] = mapped_column(String, default=now)


class Evaluation(Base):
    __tablename__ = "evaluations"
    __table_args__ = (Index("ix_evaluation_source_history", "conversation_id", "created_at", "id"),
                     Index("ix_evaluation_global_history", "created_at", "id"))
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    conversation_id: Mapped[str] = mapped_column(ForeignKey("conversation_revisions.id"), index=True)
    checklist_id: Mapped[int] = mapped_column(ForeignKey("checklist_versions.id"))
    state: Mapped[str] = mapped_column(String, default="queued", index=True)
    completeness: Mapped[str] = mapped_column(String, default="incomplete")
    cache_key: Mapped[str] = mapped_column(String, index=True)
    cached_from: Mapped[str | None] = mapped_column(String, nullable=True)
    original: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    original_score: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    effective: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    effective_score: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    meta: Mapped[dict] = mapped_column(JSON, default=dict)
    attempts: Mapped[list] = mapped_column(JSON, default=list)
    error: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[str] = mapped_column(String, default=now)
    updated_at: Mapped[str] = mapped_column(String, default=now)


class Appeal(Base):
    __tablename__ = "appeals"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    evaluation_id: Mapped[str] = mapped_column(ForeignKey("evaluations.id"), index=True)
    criterion_id: Mapped[str] = mapped_column(String)
    comment: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, default="open")
    created_at: Mapped[str] = mapped_column(String, default=now)


class Review(Base):
    __tablename__ = "review_decisions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    appeal_id: Mapped[str] = mapped_column(ForeignKey("appeals.id"))
    evaluation_id: Mapped[str] = mapped_column(ForeignKey("evaluations.id"), index=True)
    criterion_id: Mapped[str] = mapped_column(String)
    action: Mapped[str] = mapped_column(String)
    rationale: Mapped[str] = mapped_column(String)
    judgment: Mapped[dict] = mapped_column(JSON)
    resulting_score: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[str] = mapped_column(String, default=now)


class TranscriptMessage(Base):
    __tablename__ = "transcript_messages"
    __table_args__ = (UniqueConstraint("conversation_id", "message_id"),
                     Index("ix_transcript_source_order", "conversation_id", "ordinal"))
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    conversation_id: Mapped[str] = mapped_column(ForeignKey("conversation_revisions.id", ondelete="CASCADE"), index=True)
    message_id: Mapped[str] = mapped_column(String)
    ordinal: Mapped[int] = mapped_column(Integer)
    speaker: Mapped[str] = mapped_column(String, index=True)
    folded_text: Mapped[str] = mapped_column(String)
    fts_safe: Mapped[bool] = mapped_column(Boolean)


class TranscriptIndexState(Base):
    __tablename__ = "transcript_index_state"
    conversation_id: Mapped[str] = mapped_column(ForeignKey("conversation_revisions.id", ondelete="CASCADE"), primary_key=True)
    content_hash: Mapped[str] = mapped_column(String)
    version: Mapped[str] = mapped_column(String)


@event.listens_for(Conversation, "after_insert")
@event.listens_for(Conversation, "after_update")
def maintain_transcript_index(mapper, connection, target):
    from backend.app.services.transcript_index import write_index
    state = inspect(target)
    if state.pending or state.attrs.snapshot.history.has_changes() or state.attrs.content_hash.history.has_changes():
        write_index(connection, target.id, target.content_hash, target.snapshot)


@event.listens_for(Conversation, 'before_delete')
def remove_transcript_index(mapper, connection, target):
    from backend.app.services.transcript_index import delete_index
    delete_index(connection, target.id)


class Database:
    def __init__(self, path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.engine = create_engine("sqlite:///" + path.as_posix(), connect_args={"check_same_thread": False, "timeout": 30})

        @event.listens_for(self.engine, "connect")
        def pragmas(connection, _):
            cursor = connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA busy_timeout=30000")
            cursor.close()

        Base.metadata.create_all(self.engine)
        for index in Evaluation.__table__.indexes:
            if index.name in {'ix_evaluation_source_history', 'ix_evaluation_global_history'}:
                index.create(self.engine, checkfirst=True)
        self.sessions = sessionmaker(self.engine, expire_on_commit=False)
        from backend.app.services.transcript_index import ensure_index
        ensure_index(self.engine)

    @contextmanager
    def read_snapshot(self):
        """One consistent SQLite read transaction, including review history."""
        with self.sessions() as session:
            session.execute(text("BEGIN"))
            yield session

    @contextmanager
    def transaction(self):
        # Serialize revision increments, job claims and review recalculation in SQLite.
        with self.sessions() as session:
            session.execute(text("BEGIN IMMEDIATE"))
            try:
                yield session
                session.commit()
            except BaseException:
                session.rollback()
                raise
