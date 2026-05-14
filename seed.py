import httpx

BASE_URL = "http://localhost:8000"

USERS = [
    {"username": "alice",   "password": "alice-secret"},
    {"username": "bob",     "password": "bob-secret"},
    {"username": "charlie", "password": "charlie-secret"},
]


def seed():
    print("=== Seeding database ===\n")
    for user in USERS:
        resp = httpx.post(f"{BASE_URL}/register", json=user, timeout=10.0)
        if resp.status_code == 201:
            print(f"  [+] Registered:  {user['username']}")
        elif resp.status_code == 400:
            print(f"  [~] Already exists: {user['username']}")
        else:
            print(f"  [!] Error: {resp.text}")
    print("\nDone!")


if __name__ == "__main__":
    seed()
