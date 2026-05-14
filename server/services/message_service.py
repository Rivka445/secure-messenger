from typing import Protocol
import logging
import asyncio

from server.repositories import IUserRepository, IMessageRepository, GroupRepository
from server.core.crypto import encrypt, decrypt
from server.core.broadcaster import broadcaster
from server.schemas import MessageResponse
from server import exceptions as app_exceptions

log = logging.getLogger(__name__)


class IMessageService(Protocol):
    """Protocol for message-related business logic."""

    async def send(self, sender: str, recipient: str, content: str) -> MessageResponse: ...

    def get_messages(self, username: str) -> list[MessageResponse]: ...


class MessageService:
    """Concrete message service that handles sending and retrieving messages.

    Responsibilities:
    - Verify recipient exists.
    - Store an encrypted message in the message repository.
    - Publish a plaintext notification to the broadcaster for real-time subscribers.
    - Decrypt messages when retrieving for a user.
    """

    def __init__(self, user_repo: IUserRepository, message_repo: IMessageRepository) -> None:
        self._users = user_repo
        self._messages = message_repo

    async def send_to_group(self, sender: str, group_id: int, content: str, group_repo: GroupRepository) -> MessageResponse:
        """Send a message to a group (single publish).

        Persists an encrypted group message and publishes a single 'group' payload
        to the broadcaster. The broadcaster consumers (SSE) will filter by
        membership.
        """
        # verify sender is member (run sync DB call in thread)
        is_mem = await asyncio.to_thread(group_repo.is_member, group_id, sender)
        if not is_mem:
            raise app_exceptions.ForbiddenError("sender not a group member")

        ciphertext = encrypt(content)
        msg = group_repo.create_group_message(group_id, sender, ciphertext)

        # Build payload for single publish (consumers will check membership)
        payload = {
            "type": "group",
            "group_id": group_id,
            "sender": sender,
            "content": content,
            "created_at": msg.created_at,
        }

        asyncio.create_task(broadcaster.publish(payload))
        log.info("Published group message %s to group %s by %s", msg.id, group_id, sender)

        # reuse MessageResponse for shape (may create GroupMessageResponse later)
        return MessageResponse(
            id=msg.id,
            sender=msg.sender,
            recipient=str(group_id),
            content=content,
            created_at=msg.created_at,
        )

    async def send(self, sender: str, recipient: str, content: str) -> MessageResponse:
        """Send a message from `sender` to `recipient`.

        Steps:
        1. Ensure recipient exists, otherwise raise 404.
        2. Encrypt the plaintext content and persist via the message repository.
        3. Create a `MessageResponse` object with plaintext content for clients.
        4. Publish the message to the broadcaster asynchronously (non-blocking).

        Returns:
        - MessageResponse: the created message in a client-facing shape.
        """
        if not self._users.get_by_username(recipient):
            raise app_exceptions.NotFoundError("recipient not found")

        msg = self._messages.create(sender, recipient, encrypt(content))

        response = MessageResponse(
            id=msg.id,
            sender=msg.sender,
            recipient=msg.recipient,
            content=content,
            created_at=msg.created_at,
        )

        import asyncio
        asyncio.create_task(broadcaster.publish(response.model_dump()))
        return response

    def get_messages(self, username: str) -> list[MessageResponse]:
        """Retrieve and decrypt all messages for `username`.

        Returns a list of `MessageResponse` objects with the message content decrypted.
        """
        return [
            MessageResponse(
                id=msg.id,
                sender=msg.sender,
                recipient=msg.recipient,
                content=decrypt(msg.ciphertext),
                created_at=msg.created_at,
            )
            for msg in self._messages.get_for_user(username)
        ]
