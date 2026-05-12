from unittest.mock import patch

from single_node import ShardedLRU


class TestShardedLRU:
    def test_basic_put_get(self):
        cache = ShardedLRU(total_capacity=10, num_shards=2)
        cache.put("a", 1)
        assert cache.get("a") == 1
        assert cache.get("b") is None

    def test_lru_eviction(self):
        cache = ShardedLRU(total_capacity=2, num_shards=2)

        for i in range(10):
            cache.put(f"key_{i}", i)

        hits = sum(1 for i in range(10) if cache.get(f"key_{i}") is not None)
        assert hits <= 2

    @patch('single_node.sharded_cache.time.time')
    def test_ttl_expiration(self, mock_time):
        mock_time.return_value = 1000.0
        cache = ShardedLRU(total_capacity=10, num_shards=2)
        cache.put("a", 1, ttl=5)

        assert cache.get("a") == 1

        mock_time.return_value = 1006.0
        assert cache.get("a") is None

    def test_delete(self):
        cache = ShardedLRU(total_capacity=10, num_shards=2)
        cache.put("a", 1)
        cache.delete("a")
        assert cache.get("a") is None
