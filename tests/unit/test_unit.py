"""Unit tests — no DB, no HTTP. All external dependencies are mocked."""
import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException

from server.core.crypto import encrypt, decrypt
from server.core.auth import hash_password, verify_password, create_access_token, decode_access_token
from server.core.broadcaster import Broadcaster
from server.services.auth_service import AuthService
from server.services.message_service import MessageService


# ===========================================================================
# Crypto
# ===========================================================================

class TestCrypto:

    def test_encrypt_differs_from_plaintext(self):
        assert encrypt("hello") != "hello"

    def test_decrypt_round_trip(self):
        assert decrypt(encrypt("secret")) == "secret"

    def test_same_message_encrypts_differently(self):
        assert encrypt("hello") != encrypt("hello")

    def test_tampered_ciphertext_raises(self):
        with pytest.raises(Exception):
            decrypt(encrypt("original")[:-4] + "XXXX")


# ===========================================================================
# Auth helpers
# ===========================================================================

class TestAuthHelpers:

    def test_hash_and_verify_password(self):
        h = hash_password("mypassword")
        assert verify_password("mypassword", h)
        assert not verify_password("wrong", h)

    def test_create_and_decode_token(self):
        token = create_access_token("alice")
        assert decode_access_token(token) == "alice"

    def test_decode_invalid_token_raises_401(self):
        with pytest.raises(HTTPException) as exc:
            decode_access_token("not.a.token")
        assert exc.value.status_code == 401


# ===========================================================================
# Broadcaster
# ===========================================================================

class TestBroadcaster:

    def test_subscribe_and_receive(self):
        b = Broadcaster()
        q = b.subscribe()
        b.publish({"msg": "hi"})
        assert q.get(timeout=1) == {"msg": "hi"}

    def test_unsubscribe_stops_delivery(self):
        b = Broadcaster()
        q = b.subscribe()
        b.unsubscribe(q)
        b.publish({"msg": "hi"})
        assert q.empty()

    def test_multiple_subscribers_all_receive(self):
        b = Broadcaster()
        q1, q2 = b.subscribe(), b.subscribe()
        b.publish({"x": 1})
        assert q1.get(timeout=1) == {"x": 1}
        assert q2.get(timeout=1) == {"x": 1}


# ===========================================================================
# AuthService (unit — mocked repo)
# ===========================================================================

class TestAuthService:

    def _make_service(self, existing_user=None):
        repo = MagicMock()
        repo.get_by_username.return_value = existing_user
        return AuthService(repo), repo

    def test_register_new_user_succeeds(self):
        svc, repo = self._make_service(existing_user=None)
        result = svc.register("alice", "secret123", "a@test.com")
        assert result["message"] == "user created successfully"
        repo.create.assert_called_once()

    def test_register_duplicate_raises_400(self):
        fake_user = MagicMock()
        svc, _ = self._make_service(existing_user=fake_user)
        with pytest.raises(HTTPException) as exc:
            svc.register("alice", "secret123", "a@test.com")
        assert exc.value.status_code == 400

    def test_login_valid_credentials_returns_token(self):
        fake_user = MagicMock()
        fake_user.password_hash = hash_password("secret123")
        svc, _ = self._make_service(existing_user=fake_user)
        result = svc.login("alice", "secret123")
        assert result.access_token

    def test_login_wrong_password_raises_401(self):
        fake_user = MagicMock()
        fake_user.password_hash = hash_password("secret123")
        svc, _ = self._make_service(existing_user=fake_user)
        with pytest.raises(HTTPException) as exc:
            svc.login("alice", "wrongpass")
        assert exc.value.status_code == 401

    def test_login_unknown_user_raises_401(self):
        svc, _ = self._make_service(existing_user=None)
        with pytest.raises(HTTPException) as exc:
            svc.login("ghost", "secret123")
        assert exc.value.status_code == 401


# ===========================================================================
# MessageService (unit — mocked repos)
# ===========================================================================

class TestMessageService:

    def _make_service(self, recipient_exists=True):
        user_repo = MagicMock()
        user_repo.get_by_username.return_value = MagicMock() if recipient_exists else None
        msg_repo = MagicMock()
        fake_msg = MagicMock()
        fake_msg.id = 1
        fake_msg.sender = "alice"
        fake_msg.recipient = "bob"
        fake_msg.ciphertext = encrypt("hello")
        fake_msg.created_at = "2024-01-01T00:00:00"
        msg_repo.create.return_value = fake_msg
        msg_repo.get_for_user.return_value = [fake_msg]
        return MessageService(user_repo, msg_repo), msg_repo

    @pytest.mark.asyncio
    async def test_send_stores_encrypted_content(self):
        svc, msg_repo = self._make_service()
        with patch("server.services.message_service.asyncio.create_task"):
            result = await svc.send("alice", "bob", "hello")
        stored_ciphertext = msg_repo.create.call_args[0][2]
        assert stored_ciphertext != "hello"
        assert decrypt(stored_ciphertext) == "hello"

    @pytest.mark.asyncio
    async def test_send_unknown_recipient_raises(self):
        svc, _ = self._make_service(recipient_exists=False)
        from server.exceptions import NotFoundError
        with pytest.raises(NotFoundError):
            await svc.send("alice", "nobody", "hi")

    def test_get_messages_decrypts_content(self):
        svc, _ = self._make_service()
        msgs = svc.get_messages("alice")
        assert msgs[0].content == "hello"
