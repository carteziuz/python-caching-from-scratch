from abc import ABC, abstractmethod
from typing import Any, Optional


class BaseCache(ABC):
    """
    ARCHITECTURAL CONTRACT: Base Cache Interface.

    Enforces the Liskov Substitution Principle (LSP). Any system depending
    on this interface can transparently swap out the underlying cache
    implementation (NoCache -> GlobalLock -> Sharded) without altering
    upstream business logic.
    """

    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """
        Retrieve an item from the cache.
        Returns None if the key does not exist or has expired.
        """
        pass

    @abstractmethod
    def put(self, key: str, value: Any, ttl: int = 60) -> None:
        """
        Insert or update an item in the cache.

        Args:
            key: The unique identifier for the cached item.
            value: The data to store.
            ttl: Time-To-Live in seconds.
        """
        pass

    @abstractmethod
    def delete(self, key: str) -> None:
        """
        Explicitly remove an item from the cache.
        """
        pass