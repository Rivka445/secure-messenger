"""
test_app.py
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from server.main import app
from server.models import Base, get_db
from server.crypto import encrypt, decrypt


# ---------------------------------------------------------------------------
# Test database setup — uses a separate file, wiped before each test
# ---------------------------------------------------------------------------

TEST_DB_URL = "sqlite:///./test_messenger.db"
test_engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSession = sessionmaker(bind=test_engine, autocommit=False, autoflush=False)


def override_get_db():
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def fresh_db():
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def client():
    return TestClient(app)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def register_and_login(client, username="alice", password="secret123") -> str:
    """Register a user and return their JWT token."""
    client.post("/register", json={"username": username, "password": password})
    response = client.post("/login", json={"username": username, "password": password})
    return response.json()["access_token"]


def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ===========================================================================
# 1. Authentication tests
# ===========================================================================

class TestAuthentication:

    def test_register_success(self, client):
        response = client.post("/register", json={"username": "alice", "password": "secret123"})
        assert response.status_code == 201

    def test_register_duplicate_username(self, client):
        client.post("/register", json={"username": "alice", "password": "secret123"})
        response = client.post("/register", json={"username": "alice", "password": "other-password"})
        assert response.status_code == 400

    def test_register_password_too_short(self, client):
        response = client.post("/register", json={"username": "alice", "password": "abc"})
        assert response.status_code == 422   # Pydantic rejects it before your code runs

    def test_login_success(self, client):
        client.post("/register", json={"username": "alice", "password": "secret123"})
        response = client.post("/login", json={"username": "alice", "password": "secret123"})
        assert response.status_code == 200
        assert "access_token" in response.json()

    def test_login_wrong_password(self, client):
        client.post("/register", json={"username": "alice", "password": "secret123"})
        response = client.post("/login", json={"username": "alice", "password": "wrongpassword"})
        assert response.status_code == 401

    def test_login_unknown_user(self, client):
        response = client.post("/login", json={"username": "ghost", "password": "secret123"})
        assert response.status_code == 401

    def test_messages_require_token(self, client):
        response = client.get("/messages")
        assert response.status_code in (401, 403)

    def test_messages_reject_bad_token(self, client):
        response = client.get("/messages", headers={"Authorization": "Bearer fake-token"})
        assert response.status_code == 401

    def test_messages_accept_valid_token(self, client):
        token = register_and_login(client)
        response = client.get("/messages", headers=auth(token))
        assert response.status_code == 200


# ===========================================================================
# 2. Encryption tests
# ===========================================================================

class TestEncryption:

    def test_encrypt_is_not_plain_text(self):
        assert encrypt("hello world") != "hello world"

    def test_decrypt_round_trip(self):
        original = "this is a secret message"
        assert decrypt(encrypt(original)) == original

    def test_same_message_encrypts_differently_each_time(self):
        # fresh nonce every call → different ciphertext
        assert encrypt("hello") != encrypt("hello")

    def test_tampered_ciphertext_raises(self):
        blob = encrypt("original")
        tampered = blob[:-4] + "XXXX"
        with pytest.raises(Exception):
            decrypt(tampered)

    # TODO — complete this test:
    # After sending a message via POST /messages, query the database directly
    # and verify that the stored ciphertext is NOT the plain text,
    # but that decrypt(ciphertext) DOES return the original plain text.
    def test_messages_are_stored_encrypted(self, client):
        from server.models import Message
        token = register_and_login(client)
        # send a message
        plain = "secret note"
        # ensure recipient exists
        client.post("/register", json={"username": "bob", "password": "secret456"})
        resp = client.post(
            "/messages",
            json={"content": plain, "recipient": "bob"},
            headers=auth(token),
        )
        assert resp.status_code == 201
        # query the DB directly
        db = TestingSession()
        row = db.query(Message).first()
        db.close()
        # assert the ciphertext is not plain text
        # assert decrypt(ciphertext) returns the original
        assert row is not None
        ciphertext = row.ciphertext
        assert ciphertext != plain
        assert decrypt(ciphertext) == plain


# ===========================================================================
# 3. Messaging tests
# ===========================================================================

class TestMessaging:

    def test_send_message_success(self, client):
        alice_token = register_and_login(client, "alice", "secret123")
        register_and_login(client, "bob", "secret456")

        response = client.post(
            "/messages",
            json={"content": "hello bob", "recipient": "bob"},
            headers=auth(alice_token),
        )
        assert response.status_code == 201
        data = response.json()
        assert data["content"] == "hello bob"   # returned decrypted
        assert data["sender"] == "alice"
        assert data["recipient"] == "bob"

    def test_get_messages_returns_decrypted(self, client):
        alice_token = register_and_login(client, "alice", "secret123")
        register_and_login(client, "bob", "secret456")

        client.post("/messages", json={"content": "hi bob", "recipient": "bob"}, headers=auth(alice_token))

        response = client.get("/messages", headers=auth(alice_token))
        assert response.status_code == 200
        messages = response.json()
        assert len(messages) >= 1
        assert messages[0]["content"] == "hi bob"   # must be decrypted, not ciphertext

    #  complete this test:
    # Alice sends a message to Bob. Bob sends a message to Alice.
    # Verify that GET /messages returns ONLY the messages
    # where the requesting user is sender OR recipient.
    def test_user_sees_only_their_messages(self, client):
        alice_token = register_and_login(client, "alice", "secret123")
        bob_token   = register_and_login(client, "bob",   "secret456")
        register_and_login(client, "charlie", "secret789")

        # alice → bob
        # charlie → bob  (alice should NOT see this)
        # alice -> bob
        r1 = client.post(
            "/messages",
            json={"content": "from alice to bob", "recipient": "bob"},
            headers=auth(alice_token),
        )
        assert r1.status_code == 201

        # charlie -> bob
        charlie_token = register_and_login(client, "charlie", "secret789")
        r2 = client.post(
            "/messages",
            json={"content": "from charlie to bob", "recipient": "bob"},
            headers=auth(charlie_token),
        )
        assert r2.status_code == 201

        # bob -> alice
        r3 = client.post(
            "/messages",
            json={"content": "from bob to alice", "recipient": "alice"},
            headers=auth(bob_token),
        )
        assert r3.status_code == 201

        # Now fetch as alice — should see messages where alice is sender OR recipient
        resp = client.get("/messages", headers=auth(alice_token))
        assert resp.status_code == 200
        msgs = resp.json()

        # alice should see her sent message and the one sent to her by bob
        contents = {(m["sender"], m["recipient"], m["content"]) for m in msgs}
        assert ("alice", "bob", "from alice to bob") in contents
        assert ("bob", "alice", "from bob to alice") in contents
        # ensure alice does not see charlie->bob
        assert all(not (m["sender"] == "charlie" and m["recipient"] == "bob") for m in msgs)


# ===========================================================================
# 4. SSE Stream tests
# ===========================================================================

class TestSSEStream:

    def test_stream_rejects_no_token(self, client):
        response = client.get("/stream")
        assert response.status_code in (401, 403)

    def test_stream_rejects_bad_token(self, client):
        response = client.get("/stream", headers={"Authorization": "Bearer fake-token"})
        assert response.status_code == 401

    def test_stream_accepts_valid_token(self, client):
        token = register_and_login(client, "alice", "secret123")
        register_and_login(client, "bob", "secret456")
        # open stream with a short timeout — just verify it connects (200) and streams
        with client.stream("GET", "/stream", headers=auth(token)) as response:
            assert response.status_code == 200
            assert "text/event-stream" in response.headers.get("content-type", "")

    def test_sse_broadcast_delivers_message(self, client):
        """Send a message via POST, verify it appears in the SSE stream."""
        import queue
        import threading
        import json

        alice_token = register_and_login(client, "alice", "secret123")
        register_and_login(client, "bob", "secret456")
        bob_token = register_and_login(client, "bob", "secret456")

        received = queue.Queue()

        def listen():
            with client.stream("GET", "/stream", headers=auth(bob_token)) as resp:
                for line in resp.iter_lines():
                    if line.startswith("data: "):
                        received.put(json.loads(line[6:]))
                        return  # got one message, stop

        t = threading.Thread(target=listen, daemon=True)
        t.start()

        import time
        time.sleep(0.1)  # let the listener connect

        client.post(
            "/messages",
            json={"recipient": "bob", "content": "hello via SSE"},
            headers=auth(alice_token),
        )

        t.join(timeout=3)
        assert not received.empty(), "Bob did not receive the message via SSE"
        msg = received.get()
        assert msg["content"] == "hello via SSE"
        assert msg["sender"] == "alice"
        assert msg["recipient"] == "bob"

    def test_only_relevant_messages_in_stream(self, client):
        """Charlie sends to Bob. Alice's stream should NOT receive it."""
        import queue
        import threading
        import json
        import time

        alice_token = register_and_login(client, "alice", "secret123")
        register_and_login(client, "bob", "secret456")
        bob_token = register_and_login(client, "bob", "secret456")
        charlie_token = register_and_login(client, "charlie", "secret789")

        alice_received = queue.Queue()

        def listen_alice():
            with client.stream("GET", "/stream", headers=auth(alice_token)) as resp:
                for line in resp.iter_lines():
                    if line.startswith("data: "):
                        alice_received.put(json.loads(line[6:]))
                        return

        t = threading.Thread(target=listen_alice, daemon=True)
        t.start()
        time.sleep(0.1)

        # charlie → bob (alice should NOT see this)
        client.post(
            "/messages",
            json={"recipient": "bob", "content": "private to bob"},
            headers=auth(charlie_token),
        )

        # alice → bob (alice SHOULD see this)
        client.post(
            "/messages",
            json={"recipient": "bob", "content": "from alice"},
            headers=auth(alice_token),
        )

        t.join(timeout=3)
        assert not alice_received.empty()
        msg = alice_received.get()
        assert msg["sender"] == "alice"  # alice only sees her own message, not charlie's


class TestGroupFlows:

    def test_create_group_and_join_flow(self, client):
        alice_token = register_and_login(client, "alice", "secret123")
        bob_token = register_and_login(client, "bob", "secret456")

        # Alice creates a group
        resp = client.post(
            "/groups",
            json={"name": "team-alpha", "join_password": None},
            headers=auth(alice_token),
        )
        assert resp.status_code == 201
        group = resp.json()
        group_id = group["id"]

        # Bob requests to join
        r = client.post(f"/groups/{group_id}/join", json={"password": None, "message": "please"}, headers=auth(bob_token))
        assert r.status_code == 201
        req = r.json()
        req_id = req["id"]

        # Alice lists join requests and approves
        list_resp = client.get(f"/groups/{group_id}/join-requests", headers=auth(alice_token))
        assert list_resp.status_code == 200
        assert any(r["id"] == req_id for r in list_resp.json())

        approve = client.post(f"/groups/{group_id}/join-requests/{req_id}/approve", headers=auth(alice_token))
        assert approve.status_code == 200

        # Now Bob should be able to send a group message and it appears in SSE for members
        import queue, threading, time, json

        received = queue.Queue()

        def listen_bob():
            with client.stream("GET", "/stream", headers=auth(bob_token)) as resp:
                for line in resp.iter_lines():
                    if line.startswith("data: "):
                        received.put(json.loads(line[6:]))
                        return

        t = threading.Thread(target=listen_bob, daemon=True)
        t.start()
        time.sleep(0.1)

        # Bob posts to group
        post = client.post(f"/groups/{group_id}/messages", json={"content": "hello group"}, headers=auth(bob_token))
        assert post.status_code == 201

        t.join(timeout=3)
        assert not received.empty(), "Member did not receive group message via SSE"
        msg = received.get()
        assert msg["type"] == "group"
        assert msg["group_id"] == group_id

    def test_non_member_does_not_receive_group_message(self, client):
        alice_token = register_and_login(client, "alice", "secret123")
        eve_token = register_and_login(client, "eve", "badpass")

        # Alice creates a group
        resp = client.post(
            "/groups",
            json={"name": "team-beta", "join_password": None},
            headers=auth(alice_token),
        )
        assert resp.status_code == 201
        group = resp.json()
        group_id = group["id"]

        # Eve listens on stream
        import queue, threading, time, json
        received = queue.Queue()

        def listen_eve():
            with client.stream("GET", "/stream", headers=auth(eve_token)) as resp:
                for line in resp.iter_lines():
                    if line.startswith("data: "):
                        received.put(json.loads(line[6:]))
                        return

        t = threading.Thread(target=listen_eve, daemon=True)
        t.start()
        time.sleep(0.1)

        # Alice posts to group
        post = client.post(f"/groups/{group_id}/messages", json={"content": "secret note"}, headers=auth(alice_token))
        assert post.status_code == 201

        t.join(timeout=2)
        # Eve should not receive the group message (non-member)
        assert received.empty(), "Non-member received group message"
