import os
import threading
import time
from collections import OrderedDict
from typing import Any, Optional

from single_node.base_cache import BaseCache


class CacheShard:
    """
    Internal concurrency boundary.
    Manages a strictly allocated fraction of the total cache capacity
    protected by an isolated lock.
    """

    def __init__(self, capacity: int):
        self.capacity = capacity
        self.lock = threading.RLock()
        self.store: OrderedDict[str, Any] = OrderedDict()
        self.expiry: dict[str, float] = {}

    def get(self, key: str) -> Optional[Any]:
        with self.lock:
            if key not in self.store or time.time() > self.expiry.get(key, 0):
                return None
            self.store.move_to_end(key)
            return self.store[key]

    def put(self, key: str, value: Any, ttl: int) -> None:
        with self.lock:
            self.store[key] = value
            self.expiry[key] = time.time() + ttl
            self.store.move_to_end(key)

            if len(self.store) > self.capacity:
                self.store.popitem(last=False)

    def delete(self, key: str) -> None:
        with self.lock:
            self.store.pop(key, None)
            self.expiry.pop(key, None)


class ShardedLRU(BaseCache):
    """
    STRATEGY: Lock Striping (Vertical Scaling).

    Partitions the key space across multiple independent shards using deterministic hashing.
    Prevents thread serialization bottlenecks in highly concurrent workloads by distributing
    lock contention.
    """

    def __init__(self, total_capacity: int = 100, num_shards: Optional[int] = None):
        # Default to 4x logical cores to heavily distribute lock acquisition probabilities
        self.num_shards = num_shards or (os.cpu_count() or 1) * 4

        # Floor division ensures capacity bounds are strictly respected
        shard_capacity = max(1, total_capacity // self.num_shards)

        self.shards = [CacheShard(shard_capacity) for _ in range(self.num_shards)]

    def _get_shard(self, key: str) -> CacheShard:
        """Determines the routing topology for a given key."""
        shard_index = hash(key) % self.num_shards
        return self.shards[shard_index]

    def get(self, key: str) -> Optional[Any]:
        return self._get_shard(key).get(key)

    def put(self, key: str, value: Any, ttl: int = 60) -> None:
        self._get_shard(key).put(key, value, ttl)

    def delete(self, key: str) -> None:
        self._get_shard(key).delete(key)
