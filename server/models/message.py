from datetime import datetime, timezone
from sqlalchemy import String, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from server.database import Base


class Message(Base):
    """SQLAlchemy ORM model representing an encrypted message record."""
    __tablename__ = "messages"

    id:         Mapped[int] = mapped_column(primary_key=True)
    sender:     Mapped[str] = mapped_column(String, index=True, nullable=False)
    recipient:  Mapped[str] = mapped_column(String, index=True, nullable=False)
    ciphertext: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
