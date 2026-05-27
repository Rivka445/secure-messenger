"""Integration tests — real HTTP requests against an in-memory test DB."""
import pytest

from server.core.broadcaster import broadcaster
from server.crypto import decrypt
from tests.conftest import register_and_login, auth, TestingSession


# ===========================================================================
# 1. Authentication
# ===========================================================================

class TestAuthentication:

    def test_register_success(self, client):
        r = client.post("/register", json={"username": "alice", "password": "secret123", "email": "alice@test.com"})
        assert r.status_code == 201

    def test_register_duplicate_username(self, client):
        client.post("/register", json={"username": "alice", "password": "secret123", "email": "alice@test.com"})
        r = client.post("/register", json={"username": "alice", "password": "secret456", "email": "alice@test.com"})
        assert r.status_code == 400

    def test_register_password_too_short(self, client):
        r = client.post("/register", json={"username": "alice", "password": "abc", "email": "a@test.com"})
        assert r.status_code == 422

    def test_register_missing_email(self, client):
        r = client.post("/register", json={"username": "alice", "password": "secret123"})
        assert r.status_code == 422

    def test_login_success(self, client):
        client.post("/register", json={"username": "alice", "password": "secret123", "email": "a@test.com"})
        r = client.post("/login", json={"username": "alice", "password": "secret123"})
        assert r.status_code == 200
        assert "access_token" in r.json()

    def test_login_wrong_password(self, client):
        client.post("/register", json={"username": "alice", "password": "secret123", "email": "a@test.com"})
        r = client.post("/login", json={"username": "alice", "password": "wrong"})
        assert r.status_code == 401

    def test_login_unknown_user(self, client):
        assert client.post("/login", json={"username": "ghost", "password": "secret123"}).status_code == 401

    def test_messages_require_token(self, client):
        assert client.get("/messages").status_code in (401, 403)

    def test_messages_reject_bad_token(self, client):
        assert client.get("/messages", headers={"Authorization": "Bearer fake"}).status_code == 401

    def test_messages_accept_valid_token(self, client):
        _, token = register_and_login(client)
        assert client.get("/messages", headers=auth(token)).status_code == 200


# ===========================================================================
# 2. Messaging
# ===========================================================================

class TestMessaging:

    def test_send_message_success(self, client):
        alice, alice_token = register_and_login(client, "alice")
        bob, _ = register_and_login(client, "bob")
        r = client.post("/messages", json={"content": "hello", "recipient": bob}, headers=auth(alice_token))
        assert r.status_code == 201
        assert r.json()["content"] == "hello"

    def test_messages_stored_encrypted(self, client):
        from server.models import Message
        _, token = register_and_login(client)
        bob, _ = register_and_login(client, "bob")
        client.post("/messages", json={"content": "secret", "recipient": bob}, headers=auth(token))
        db = TestingSession()
        row = db.query(Message).first()
        db.close()
        assert row.ciphertext != "secret"
        assert decrypt(row.ciphertext) == "secret"

    def test_get_messages_decrypted(self, client):
        alice, alice_token = register_and_login(client, "alice")
        bob, _ = register_and_login(client, "bob")
        client.post("/messages", json={"content": "hi bob", "recipient": bob}, headers=auth(alice_token))
        msgs = client.get("/messages", headers=auth(alice_token)).json()
        assert msgs[0]["content"] == "hi bob"

    def test_user_sees_only_their_messages(self, client):
        alice, alice_token = register_and_login(client, "alice")
        bob, bob_token = register_and_login(client, "bob")
        charlie, charlie_token = register_and_login(client, "charlie")

        client.post("/messages", json={"content": "a→b", "recipient": bob}, headers=auth(alice_token))
        client.post("/messages", json={"content": "c→b", "recipient": bob}, headers=auth(charlie_token))
        client.post("/messages", json={"content": "b→a", "recipient": alice}, headers=auth(bob_token))

        contents = {m["content"] for m in client.get("/messages", headers=auth(alice_token)).json()}
        assert "a→b" in contents
        assert "b→a" in contents
        assert "c→b" not in contents

    def test_send_to_unknown_recipient_fails(self, client):
        _, token = register_and_login(client)
        r = client.post("/messages", json={"content": "hi", "recipient": "nobody"}, headers=auth(token))
        assert r.status_code in (400, 404)

    def test_get_messages_empty_initially(self, client):
        _, token = register_and_login(client)
        assert client.get("/messages", headers=auth(token)).json() == []


# ===========================================================================
# 3. SSE / Broadcaster
# ===========================================================================

class TestSSE:

    def test_stream_rejects_no_token(self, client):
        assert client.get("/stream").status_code in (401, 403)

    def test_stream_rejects_bad_token(self, client):
        assert client.get("/stream", headers={"Authorization": "Bearer fake"}).status_code == 401

    def test_broadcast_delivers_dm(self, client):
        alice, alice_token = register_and_login(client, "alice")
        bob, _ = register_and_login(client, "bob")
        q = broadcaster.subscribe()
        try:
            client.post("/messages", json={"recipient": bob, "content": "hello SSE"}, headers=auth(alice_token))
            msg = q.get(timeout=3)
            assert msg["content"] == "hello SSE"
            assert msg["sender"] == alice
        finally:
            broadcaster.unsubscribe(q)


# ===========================================================================
# 4. Groups
# ===========================================================================

class TestGroups:

    def test_create_group(self, client):
        _, token = register_and_login(client, "alice")
        r = client.post("/groups", json={"name": "team", "join_password": None}, headers=auth(token))
        assert r.status_code == 201
        assert r.json()["name"] == "team"

    def test_join_and_approve(self, client):
        _, alice_token = register_and_login(client, "alice")
        _, bob_token = register_and_login(client, "bob")

        group_id = client.post("/groups", json={"name": "team", "join_password": None}, headers=auth(alice_token)).json()["id"]
        req_id = client.post(f"/groups/{group_id}/join", json={"password": None}, headers=auth(bob_token)).json()["id"]

        assert client.post(f"/groups/{group_id}/join-requests/{req_id}/approve", headers=auth(alice_token)).status_code == 200

    def test_join_with_correct_password_auto_approved(self, client):
        _, alice_token = register_and_login(client, "alice")
        _, bob_token = register_and_login(client, "bob")

        group_id = client.post("/groups", json={"name": "locked", "join_password": "pass123"}, headers=auth(alice_token)).json()["id"]
        r = client.post(f"/groups/{group_id}/join", json={"password": "pass123"}, headers=auth(bob_token))
        assert r.json()["status"] == "approved"

    def test_join_wrong_password_stays_pending(self, client):
        _, alice_token = register_and_login(client, "alice")
        _, bob_token = register_and_login(client, "bob")

        group_id = client.post("/groups", json={"name": "locked", "join_password": "pass123"}, headers=auth(alice_token)).json()["id"]
        r = client.post(f"/groups/{group_id}/join", json={"password": "wrong"}, headers=auth(bob_token))
        assert r.json()["status"] == "pending"

    def test_reject_join_request(self, client):
        _, alice_token = register_and_login(client, "alice")
        _, bob_token = register_and_login(client, "bob")

        group_id = client.post("/groups", json={"name": "team", "join_password": None}, headers=auth(alice_token)).json()["id"]
        req_id = client.post(f"/groups/{group_id}/join", json={"password": None}, headers=auth(bob_token)).json()["id"]

        r = client.post(f"/groups/{group_id}/join-requests/{req_id}/reject", headers=auth(alice_token))
        assert r.status_code == 200
        assert r.json()["status"] == "rejected"
