import concurrent.futures
import random
import time
from typing import Callable, List

from single_node import NoCache, GlobalLockCache, ShardedLRU, BaseCache


def simulated_database_call(key: str) -> str:
    """
    Simulates a 10ms blocking I/O operation.
    CRITICAL: During time.sleep(), Python releases the GIL,
    allowing other threads to execute.
    """
    time.sleep(0.01)
    return f"data_{key}"


def io_bound_workload(cache: BaseCache, keys: List[str]) -> tuple[int, int]:
    """
    Executes a standard read-through cache pattern.
    The lock is only held during get() and put(), NOT during the I/O fetch.
    """
    hits = 0
    db_calls = 0

    for k in keys:
        # Fast path: In-memory (Holds lock briefly)
        if cache.get(k) is not None:
            hits += 1
        else:
            # Slow path: I/O Fetch (GIL released, Lock NOT held)
            result = simulated_database_call(k)
            # Write path: In-memory (Holds lock briefly)
            cache.put(k, result, ttl=30)
            db_calls += 1

    return hits, db_calls


def execute_io_benchmark(cache_factory: Callable[[], BaseCache], name: str, threads: int,
                         workload: List[List[str]]) -> None:
    cache = cache_factory()
    start_time = time.perf_counter()

    with concurrent.futures.ThreadPoolExecutor(max_workers=threads) as executor:
        results = list(executor.map(lambda w: io_bound_workload(cache, w), workload))

    duration = time.perf_counter() - start_time
    total_hits = sum(r[0] for r in results)
    total_calls = sum(r[1] for r in results)
    total_requests = total_hits + total_calls
    hit_rate = (total_hits / total_requests) * 100 if total_requests > 0 else 0.0

    print(f"{name:.<25} {duration:>7.4f}s | Hit Rate: {hit_rate:>6.2f}% | DB Calls: {total_calls}")


if __name__ == "__main__":
    THREADS = 32
    REQUESTS_PER_THREAD = 100
    TOTAL_REQUESTS = THREADS * REQUESTS_PER_THREAD
    KEY_SPACE = 200
    CAPACITY = 200

    # ZIPFIAN DISTRIBUTION:
    # We return to the 80/20 rule to simulate realistic database skew, ensuring high cache hit rates.
    weights = [1.0 / (i + 1) for i in range(KEY_SPACE)]
    workload = [
        random.choices([f"key_{i}" for i in range(KEY_SPACE)], weights=weights, k=REQUESTS_PER_THREAD)
        for _ in range(THREADS)
    ]

    print(f"--- I/O SHIELDING BENCHMARK (GIL RELEASED) ---")
    print(f"Threads: {THREADS} | Total Requests: {TOTAL_REQUESTS} | Distribution: Zipfian")
    print("-" * 85)

    execute_benchmark = lambda factory, name: execute_io_benchmark(factory, name, THREADS, workload)

    # Run the Control Group
    execute_benchmark(lambda: NoCache(), "Baseline (No Cache)")

    # Run the Test Groups
    execute_benchmark(lambda: GlobalLockCache(max_size=CAPACITY), "Global Lock Cache")
    execute_benchmark(lambda: ShardedLRU(total_capacity=CAPACITY, num_shards=16), "Sharded LRU (16 Shards)")
