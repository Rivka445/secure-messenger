from fastapi import Depends
from sqlalchemy.orm import Session

from server.database import get_db
from server.repositories import IUserRepository, UserRepository
from server.repositories import IMessageRepository, MessageRepository
from server.services import IAuthService, AuthService
from server.services import IMessageService, MessageService
from server.repositories import GroupRepository
from server.services.group_service import GroupService


def get_user_repo(db: Session = Depends(get_db)) -> IUserRepository:
    return UserRepository(db)


def get_message_repo(db: Session = Depends(get_db)) -> IMessageRepository:
    return MessageRepository(db)


def get_auth_service(user_repo: IUserRepository = Depends(get_user_repo)) -> IAuthService:
    return AuthService(user_repo)


def get_message_service(
    user_repo: IUserRepository = Depends(get_user_repo),
    message_repo: IMessageRepository = Depends(get_message_repo),
) -> IMessageService:
    return MessageService(user_repo, message_repo)


def get_group_repo(db: Session = Depends(get_db)) -> GroupRepository:
    return GroupRepository(db)


def get_group_service(group_repo: GroupRepository = Depends(get_group_repo)) -> GroupService:
    return GroupService(group_repo)
