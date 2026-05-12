from single_node import NoCache


def test_nocache_always_misses():
    cache = NoCache()
    cache.put("key1", "value1")
    assert cache.get("key1") is None

    cache.delete("key1")
    assert cache.get("key1") is None
