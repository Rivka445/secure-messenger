from typing import Protocol
from fastapi import HTTPException
from server.repositories import IUserRepository
from server.core.auth import hash_password, verify_password, create_access_token
from server.schemas import TokenResponse
from sqlalchemy.exc import IntegrityError


class IAuthService(Protocol):
    """Interface (Protocol) for authentication service.

    Methods:
    - register: create a new user account
    - login: authenticate a user and return an access token
    """

    def register(self, username: str, password: str, email: str | None) -> dict: ...

    def login(self, username: str, password: str) -> TokenResponse: ...


class AuthService:
    """Concrete implementation of authentication logic using a user repository.

    The service is responsible for registering users (with password hashing)
    and authenticating credentials to issue JWT access tokens.
    """

    def __init__(self, user_repo: IUserRepository) -> None:
        """Initialize the service with a user repository dependency.

        Parameters:
        - user_repo: an object implementing `IUserRepository` for DB operations
        """
        self._repo = user_repo

    def register(self, username: str, password: str, email: str | None) -> dict:
        """Register a new user.

        - Returns a small dict message on success.
        - Raises HTTPException(400) if username already exists.
        """
        if self._repo.get_by_username(username):
            raise HTTPException(status_code=400, detail="username already taken")
        try:
            self._repo.create(username, hash_password(password), email)
        except IntegrityError:
            # In case of race-condition or DB unique constraint violation,
            # surface a 400 response instead of crashing the server.
            raise HTTPException(status_code=400, detail="username already taken")
        return {"message": "user created successfully"}

    def login(self, username: str, password: str) -> TokenResponse:
        """Authenticate a user and return a TokenResponse.

        - Raises HTTPException(401) for invalid credentials.
        - On success returns a `TokenResponse` Pydantic model containing an access token.
        """
        user = self._repo.get_by_username(username)
        if not user or not verify_password(password, user.password_hash):
            raise HTTPException(status_code=401, detail="invalid credentials")
        return TokenResponse(access_token=create_access_token(username))
