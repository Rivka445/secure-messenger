from datetime import datetime, timezone
from sqlalchemy import Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from server.database import Base


class GroupJoinRequest(Base):
    """ORM model for a user's request to join a group."""
    __tablename__ = "group_join_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"), nullable=False)
    username: Mapped[str] = mapped_column(String, nullable=False, index=True)
    message: Mapped[str | None] = mapped_column(String, nullable=True)
    provided_password_ok: Mapped[bool] = mapped_column(default=False)
    status: Mapped[str] = mapped_column(String, default="pending")
    requested_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    processed_by: Mapped[str | None] = mapped_column(String, nullable=True)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
