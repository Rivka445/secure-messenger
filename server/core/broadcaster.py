import logging
import queue
from typing import List

log = logging.getLogger(__name__)


class Broadcaster:
    """Thread-safe broadcaster for SSE tests.

    Uses `queue.Queue` objects for subscribers so sync TestClient threads
    can block on .get() while publishers call .put(). This avoids
    cross-thread asyncio wakeup issues in the test harness.
    """

    def __init__(self) -> None:
        self.subscribers: List[queue.Queue] = []

    def subscribe(self) -> queue.Queue:
        q: queue.Queue = queue.Queue()
        self.subscribers.append(q)
        log.info("Subscriber added, total subscribers=%d", len(self.subscribers))
        return q

    def unsubscribe(self, q: queue.Queue) -> None:
        before = len(self.subscribers)
        self.subscribers = [s for s in self.subscribers if s is not q]
        log.info("Subscriber removed, total subscribers=%d (was %d)", len(self.subscribers), before)

    def publish(self, message: dict) -> None:
        subs = list(self.subscribers)
        log.info("Publishing message to %d subscribers", len(subs))
        for q in subs:
            try:
                q.put(message)
            except Exception:
                log.exception("Failed to publish to subscriber")


broadcaster = Broadcaster()
