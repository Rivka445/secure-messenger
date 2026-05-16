import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from server.main import app
from server.models import Base, get_db

TEST_DB_URL = "sqlite:///./tests/test_messenger.db"
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


def register_and_login(client, username="alice", password="secret123") -> tuple[str, str]:
    import secrets
    uname = f"{username}-{secrets.token_hex(4)}"
    client.post("/register", json={"username": uname, "password": password, "email": f"{uname}@test.com"})
    token = client.post("/login", json={"username": uname, "password": password}).json()["access_token"]
    return uname, token


def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}
