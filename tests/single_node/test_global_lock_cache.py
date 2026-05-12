from unittest.mock import patch

from single_node import GlobalLockCache


class TestGlobalLockCache:
    def test_basic_put_get(self):
        cache = GlobalLockCache(max_size=10)
        cache.put("a", 1)
        assert cache.get("a") == 1
        assert cache.get("b") is None

    def test_lru_eviction(self):
        cache = GlobalLockCache(max_size=2)
        cache.put("a", 1)
        cache.put("b", 2)
        cache.put("c", 3)

        assert cache.get("a") is None
        assert cache.get("b") == 2
        assert cache.get("c") == 3

    @patch('single_node.global_lock_cache.time.time')
    def test_ttl_expiration(self, mock_time):
        mock_time.return_value = 1000.0
        cache = GlobalLockCache(max_size=10)
        cache.put("a", 1, ttl=5)

        assert cache.get("a") == 1

        mock_time.return_value = 1006.0
        assert cache.get("a") is None

    def test_delete(self):
        cache = GlobalLockCache(max_size=10)
        cache.put("a", 1)
        cache.delete("a")
        assert cache.get("a") is None
