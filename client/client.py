import threading
import httpx
import json
import getpass

BASE_URL = "http://localhost:8000"


def prompt_auth() -> tuple[str, str]:
    print("\n=== Secure Messenger ===")
    print("1) Register")
    print("2) Login")
    choice = input("Choose (1/2): ").strip()

    username = input("Username: ").strip()
    password = getpass.getpass("Password: ")

    if choice == "1":
        email = input("Email (optional, press Enter to skip): ").strip() or None
        resp = httpx.post(f"{BASE_URL}/register", json={"username": username, "password": password, "email": email}, timeout=10.0)
        if resp.status_code != 201:
            print(f"Registration failed: {resp.text}")
            exit(1)
        print(f"  [+] Registered: {username}")

    resp = httpx.post(f"{BASE_URL}/login", json={"username": username, "password": password}, timeout=10.0)
    if resp.status_code != 200:
        print(f"Login failed: {resp.text}")
        exit(1)

    token = resp.json()["access_token"]
    return username, token


def show_history(token: str, my_username: str):
    headers = {"Authorization": f"Bearer {token}"}
    resp = httpx.get(f"{BASE_URL}/messages", headers=headers, timeout=10.0)
    if resp.status_code != 200:
        return
    messages = resp.json()
    if not messages:
        return
    print("\n--- message history ---")
    for msg in messages:
        print(f"  [{msg['sender']} → {msg['recipient']}]: {msg['content']}")
    print("-----------------------\n")


def listen_for_messages(token: str, my_username: str) -> None:
    """Opens a persistent SSE connection. Runs in background thread."""
    headers = {"Authorization": f"Bearer {token}"}
    try:
        with httpx.stream("GET", f"{BASE_URL}/stream", headers=headers, timeout=None) as response:
            for line in response.iter_lines():
                if line.startswith("data: "):
                    message = json.loads(line[6:])
                    if message["sender"] != my_username:
                        print(f"\n  [{message['sender']} → {message['recipient']}]: {message['content']}")
                        print("  > ", end="", flush=True)
    except Exception:
        pass


def main():
    username, token = prompt_auth()
    print(f"\nWelcome, {username}!  (type 'recipient: message' and press Enter, or 'quit' to exit)")

    show_history(token, username)

    listener = threading.Thread(target=listen_for_messages, args=(token, username), daemon=True)
    listener.start()

    headers = {"Authorization": f"Bearer {token}"}

    while True:
        try:
            line = input("  > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if line.lower() == "quit":
            print("Goodbye!")
            break

        if ": " not in line:
            print("  Format: recipient: message")
            continue

        recipient, content = line.split(": ", 1)
        resp = httpx.post(
            f"{BASE_URL}/messages",
            json={"recipient": recipient.strip(), "content": content.strip()},
            headers=headers,
            timeout=10.0,
        )
        if resp.status_code != 201:
            print(f"  Error: {resp.text}")


if __name__ == "__main__":
    main()
