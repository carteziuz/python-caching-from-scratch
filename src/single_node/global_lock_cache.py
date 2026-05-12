import time
import threading
from collections import OrderedDict
from typing import Any, Optional

from single_node import BaseCache


class GlobalLockCache(BaseCache):
    """
    STRATEGY: Single Global Lock.

    Highly optimized for low-overhead, zero-routing execution.
    Best for environments with low thread-to-core ratios where the OS
    does not force heavy context switching.
    """

    def __init__(self, max_size: int = 100):
        self.lock = threading.RLock()
        self.max_size = max_size
        self.store: OrderedDict[str, Any] = OrderedDict()
        self.expiry: dict[str, int] = {}

    def get(self, key: str) -> Optional[Any]:
        with self.lock:
            # Check existence and TTL
            if key not in self.store or time.time() > self.expiry.get(key, 0):
                return None

            # The LRU Tax: A Read is a Write operation
            self.store.move_to_end(key)
            return self.store[key]

    def put(self, key: str, value: Any, ttl: int = 60) -> None:
        with self.lock:
            self.store[key] = value
            self.expiry[key] = time.time() + ttl
            self.store.move_to_end(key)

            # O(1) Eviction
            if len(self.store) > self.max_size:
                self.store.popitem(last=False)

    def delete(self, key: str) -> None:
        with self.lock:
            self.store.pop(key, None)
            self.expiry.pop(key, None)
