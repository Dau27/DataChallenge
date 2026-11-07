from contextlib import contextmanager
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import JSON, ForeignKey, Integer, String, UniqueConstraint, create_engine, event, text
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
        self.sessions = sessionmaker(self.engine, expire_on_commit=False)

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
