from datetime import datetime
import sqlalchemy as sa
from sqlalchemy import Table, Column, Integer, String, DateTime, JSON, MetaData, create_engine
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:example@localhost:5432/aura")
engine = create_engine(DATABASE_URL)
metadata = MetaData()

audit_events = Table(
    "audit_events",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("event_type", String, nullable=False),
    Column("actor", String, nullable=False),
    Column("session_id", String, nullable=True),
    Column("timestamp", DateTime, nullable=False, default=datetime.utcnow),
    Column("outcome", String, nullable=False),
    Column("metadata", JSON, nullable=True),
)

def create_tables():
    metadata.create_all(engine)

def write_audit_event(event_type: str, actor: str, session_id: str, outcome: str, metadata_obj: dict = None):
    with engine.begin() as conn:
        ins = audit_events.insert().values(
            event_type=event_type,
            actor=actor,
            session_id=session_id,
            timestamp=datetime.utcnow(),
            outcome=outcome,
            metadata=metadata_obj
        )
        conn.execute(ins)