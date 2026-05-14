from typing import Protocol
from sqlalchemy.orm import Session
from server.models import Message


class IMessageRepository(Protocol):
    """Protocol for message repository DB operations."""

    def create(self, sender: str, recipient: str, ciphertext: str) -> Message: ...

    def get_for_user(self, username: str) -> list[Message]: ...


class MessageRepository:
    """SQLAlchemy-backed implementation for storing and querying messages."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def create(self, sender: str, recipient: str, ciphertext: str) -> Message:
        msg = Message(sender=sender, recipient=recipient, ciphertext=ciphertext)
        self._db.add(msg)
        self._db.commit()
        self._db.refresh(msg)
        return msg

    def get_for_user(self, username: str) -> list[Message]:
        return (
            self._db.query(Message)
            .filter((Message.sender == username) | (Message.recipient == username))
            .order_by(Message.created_at)
            .all()
        )
