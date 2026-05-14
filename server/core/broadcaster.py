import asyncio
from typing import Set


class Broadcaster:
    """Simple in-memory broadcaster used for Server-Sent Events (SSE).

    Each subscriber is represented by an asyncio.Queue instance. Publishers
    place dict messages onto every subscriber queue.
    """

    def __init__(self) -> None:
        self.subscribers: Set[asyncio.Queue] = set()

    async def subscribe(self) -> asyncio.Queue:
        """Create and register a new asyncio.Queue for a subscriber.

        Returns the queue that the caller should listen on.
        """
        queue: asyncio.Queue = asyncio.Queue()
        self.subscribers.add(queue)
        return queue

    async def unsubscribe(self, queue: asyncio.Queue) -> None:
        """Unregister a subscriber queue."""
        self.subscribers.discard(queue)

    async def publish(self, message: dict) -> None:
        """Publish a message (dict) to all subscriber queues.

        This iterates the subscriber set and puts the message onto each queue.
        """
        for queue in self.subscribers:
            await queue.put(message)


broadcaster = Broadcaster()
