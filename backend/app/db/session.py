from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

from app.config import get_settings


class SessionPlaceholder:
    """Minimal DB session contract until persistent SQLAlchemy wiring is added."""

    def __init__(self) -> None:
        self.database_url = get_settings().database_url

    def close(self) -> None:
        return None


@contextmanager
def get_session() -> Iterator[SessionPlaceholder]:
    session = SessionPlaceholder()
    try:
        yield session
    finally:
        session.close()
