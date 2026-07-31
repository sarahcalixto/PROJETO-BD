"""Base declarativa compartilhada pelos modelos SQLAlchemy."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base dos mapeamentos do sistema hospitalar."""
