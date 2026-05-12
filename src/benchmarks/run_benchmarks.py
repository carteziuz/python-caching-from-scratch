import concurrent.futures
import random
import time
from typing import Callable, List

from single_node import NoCache, GlobalLockCache, BaseCache


def expensive_io_operation(key: str) -> str:
    """Simulates external I/O (e.g., Network API or DB call with 10ms latency)."""
    time.sleep(0.01)
    return f"data_{key}"


def run_workload(cache: BaseCache, keys: List[str], operation_func: Callable) -> tuple[int, int]:
    """Executes a stream of requests against the cache."""
    hits = 0
    external_calls = 0

    for k in keys:
        if cache.get(k) is not None:
            hits += 1
        else:
            # Cache Miss: Fetch from source and populate cache
            res = operation_func(k)
            cache.put(k, res, ttl=30)
            external_calls += 1

    return hits, external_calls


def execute_benchmark(
        cache_factory: Callable[[], BaseCache],
        name: str,
        threads: int,
        workload: List[List[str]]) -> None:
    """Orchestrates the concurrent execution and calculates metrics."""
    cache = cache_factory()
    start_time = time.perf_counter()

    with concurrent.futures.ThreadPoolExecutor(max_workers=threads) as executor:
        results = list(executor.map(lambda w: run_workload(cache, w, expensive_io_operation), workload))

    duration = time.perf_counter() - start_time
    total_hits = sum(r[0] for r in results)
    total_calls = sum(r[1] for r in results)
    total_requests = total_hits + total_calls
    hit_rate = (total_hits / total_requests) * 100 if total_requests > 0 else 0.0

    print(f"{name:.<25} {duration:>7.4f}s | Hit Rate: {hit_rate:>6.2f}% | DB Calls: {total_calls}")


if __name__ == "__main__":
    THREADS = 16
    CAPACITY = 100
    REQUESTS_PER_THREAD = 100
    TOTAL_REQUESTS = THREADS * REQUESTS_PER_THREAD
    KEY_SPACE = 100

    # Generate a realistic workload using a Zipfian distribution (s=1).
    # This creates a power-law access pattern where a small number of "hot" keys
    # receive the vast majority of traffic, perfectly simulating real-world database skew.
    weights = [1.0 / (i + 1) for i in range(KEY_SPACE)]

    # workload is a List[List[str]] where each inner list is the sequence of keys a thread will request.
    # Due to the Zipfian weights, low-index keys (key_0, key_1) dominate the sequences.
    #
    # SAMPLE VISUALIZATION (If THREADS=3 and REQUESTS_PER_THREAD=5):
    # [
    #    ["key_0", "key_0", "key_3", "key_1", "key_0"],  # Thread-0's queue (heavy contention on key_0)
    #    ["key_1", "key_2", "key_0", "key_0", "key_8"],  # Thread-1's queue
    #    ["key_0", "key_1", "key_14", "key_0", "key_2"]  # Thread-2's queue
    # ]
    workload = [
        random.choices(
            [f"key_{i}" for i in range(KEY_SPACE)],
            weights=weights,
            k=REQUESTS_PER_THREAD
        )
        for _ in range(THREADS)
    ]

    print(f"--- SYSTEMIC I/O SHIELDING BENCHMARK ---")
    print(f"Threads: {THREADS} | Total Requests: {TOTAL_REQUESTS} | Cache Capacity: {CAPACITY}")
    print("-" * 75)

    # Run Control Group (Direct DB calls)
    execute_benchmark(lambda: NoCache(), "Baseline (No Cache)", THREADS, workload)

    # Run Test Group (Global Lock Cache)
    execute_benchmark(lambda: GlobalLockCache(max_size=CAPACITY), "Global Lock Cache", THREADS, workload)
