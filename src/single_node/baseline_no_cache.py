from typing import Any, Optional

from single_node import BaseCache


class NoCache(BaseCache):
    """
    STRATEGY: Direct Pass-Through.

    Simulates a system where every request must wait for external I/O.
    Used exclusively as a control group for benchmarking systemic cache value.
    """

    def get(self, key: str) -> Optional[Any]:
        return None

    def put(self, key: str, value: Any, ttl: int = 60) -> None:
        pass

    def delete(self, key: str) -> None:
        pass
