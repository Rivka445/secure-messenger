from typing import Protocol, Optional
from sqlalchemy.orm import Session
from server.models import User


class IUserRepository(Protocol):
    """Protocol for user repository operations against the DB."""

    def get_by_username(self, username: str) -> Optional[User]: ...

    def create(self, username: str, password_hash: str, email: str | None) -> User: ...


class UserRepository:
    """SQLAlchemy-backed implementation of IUserRepository."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def get_by_username(self, username: str) -> Optional[User]:
        return self._db.query(User).filter(User.username == username).first()

    def create(self, username: str, password_hash: str, email: str | None) -> User:
        user = User(username=username, password_hash=password_hash, email=email)
        self._db.add(user)
        self._db.commit()
        self._db.refresh(user)
        return user
