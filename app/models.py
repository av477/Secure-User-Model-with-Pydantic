"""SQLAlchemy ORM models."""

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # unique=True creates a UNIQUE constraint in PostgreSQL, so duplicates are
    # rejected by the database itself, not only by application code.
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    # Only the bcrypt hash is ever stored - never the plain-text password.
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    # Set by the database at insert time, stored with its time zone.
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} username={self.username!r}>"
