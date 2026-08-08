from pathlib import Path

from sqlmodel import Session, SQLModel, create_engine

import os

# Resolve database path: prefer DATABASE_URL env var, otherwise use ./data/ relative to this file
_db_url = os.getenv("DATABASE_URL", "")
if not _db_url:
    _data_dir = Path(__file__).parent / "data"
    _data_dir.mkdir(parents=True, exist_ok=True)
    _db_url = f"sqlite:///{_data_dir / 'tickerecho.db'}"
else:
    # Ensure directory exists for any sqlite:/// path
    if _db_url.startswith("sqlite:///"):
        _db_path = Path(_db_url.replace("sqlite:///", "", 1))
        _db_path.parent.mkdir(parents=True, exist_ok=True)

engine = create_engine(_db_url, connect_args={"check_same_thread": False})


def init_db() -> None:
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
