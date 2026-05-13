import concurrent.futures
import random
import time
from typing import Callable, List

from single_node import GlobalLockCache, ShardedLRU, BaseCache


def execute_pure_cpu_operations(cache: BaseCache, keys_to_access: List[str]) -> int:
    """
    Why: By omitting time.sleep() (zero simulated I/O), we prevent the OS from cleanly context-switching.
    This forces the active threads to violently compete for the Python GIL and internal Mutexes,
    exposing the absolute physical limit of the cache's synchronization logic.
    """
    for key in keys_to_access:
        if cache.get(key) is None:
            cache.put(key, "in_memory_data", ttl=60)
    return len(keys_to_access)


def measure_systemic_throughput(
        cache_factory: Callable[[], BaseCache],
        architecture_name: str,
        thread_count: int,
        thread_workloads: List[List[str]],
        key_space: int
) -> None:
    cache = cache_factory()

    # Pre-warm the cache.
    # Why: We must measure the latency of thread synchronization (locks) and routing (hashing),
    # not the memory allocation overhead of creating new C-level dictionary entries.
    for i in range(key_space):
        cache.put(f"key_{i}", "warm_data", ttl=60)

    start_time = time.perf_counter()

    with concurrent.futures.ThreadPoolExecutor(max_workers=thread_count) as executor:
        # Force eager evaluation of the map iterator to ensure all threads execute during the timer
        list(executor.map(lambda workload: execute_pure_cpu_operations(cache, workload), thread_workloads))

    duration = time.perf_counter() - start_time
    total_operations = thread_count * len(thread_workloads[0])
    operations_per_second = total_operations / duration

    print(f"{architecture_name:.<25} {duration:>7.4f}s | Throughput: {operations_per_second:>9.0f} ops/sec")


if __name__ == "__main__":
    THREAD_COUNT = 32
    OPERATIONS_PER_THREAD = 10000
    TOTAL_OPERATIONS = THREAD_COUNT * OPERATIONS_PER_THREAD
    KEY_SPACE = 1000

    # Set capacity equal to key space to strictly eliminate eviction overhead.
    # Why: Eviction requires CPU cycles to move items inside the OrderedDict.
    # We want to isolate our metrics strictly to Lock Acquisition vs. Hash Routing.
    CACHE_CAPACITY = 1000

    # Uniform Distribution.
    # Why: We must hit all keys equally. If we used a Zipfian (80/20) skew, all threads
    # would hammer "key_0", which routes to a single shard. That would degrade the ShardedLRU
    # into a GlobalLockCache with extra hashing overhead, invalidating the distributed test.
    key_pool = [f"key_{i}" for i in range(KEY_SPACE)]
    thread_workloads = [
        random.choices(key_pool, k=OPERATIONS_PER_THREAD)
        for _ in range(THREAD_COUNT)
    ]

    print("--- THE GIL CEILING BENCHMARK (PURE CPU BOUND) ---")
    print(f"Threads: {THREAD_COUNT} | Total Ops: {TOTAL_OPERATIONS} | Distribution: Uniform")
    print("Hypothesis: GlobalLock will outperform ShardedLRU due to Python's GIL preventing true parallelism.")
    print("-" * 85)

    measure_throughput = lambda factory, name: measure_systemic_throughput(
        factory, name, THREAD_COUNT, thread_workloads, KEY_SPACE
    )

    measure_throughput(lambda: GlobalLockCache(max_size=CACHE_CAPACITY), "Global Lock Cache")
    measure_throughput(lambda: ShardedLRU(total_capacity=CACHE_CAPACITY, num_shards=16), "Sharded LRU (16 Shards)")
