from datetime import datetime, timezone
from sqlalchemy import Integer, String, ForeignKey, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from server.database import Base


class GroupMessage(Base):
    """ORM model for a message sent to a group."""
    __tablename__ = "group_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"), nullable=False)
    sender: Mapped[str] = mapped_column(String, nullable=False)
    ciphertext: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
