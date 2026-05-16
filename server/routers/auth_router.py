from fastapi import APIRouter, Depends, status, HTTPException
from server.schemas import RegisterRequest, LoginRequest, TokenResponse
from server.services import IAuthService
from server.dependencies import get_auth_service, get_user_repo
from server.repositories import UserRepository
from server.core.auth import require_auth
from typing import Any

router = APIRouter(tags=["auth"])


@router.get("/users/verify")
def verify_user(
    username: str,
    email: str,
    current_user: str = Depends(require_auth),
    user_repo: UserRepository = Depends(get_user_repo),
):
    """Verify a user exists with the given username and email."""
    user = user_repo.get_by_username(username)
    if not user or user.email != email:
        raise HTTPException(status_code=404, detail="User not found")
    return {"username": user.username, "email": user.email}


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(
    body: RegisterRequest,
    service: IAuthService = Depends(get_auth_service),
) -> dict[str, Any]:
    """Register a new user account.

    Accepts a `RegisterRequest` body and uses the injected auth service to
    create a new user. Returns a simple dict message on success.
    """
    return service.register(body.username, body.password, body.email)


@router.post("/login", response_model=TokenResponse)
def login(
    body: LoginRequest,
    service: IAuthService = Depends(get_auth_service),
) -> TokenResponse:
    """Authenticate a user and return an access token in `TokenResponse`.

    Delegates to the auth service which raises HTTP exceptions on failure.
    """
    return service.login(body.username, body.password)
