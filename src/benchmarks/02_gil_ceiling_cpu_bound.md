# The GIL Ceiling (Pure CPU Bound)

**Objective:** Evaluate the performance of a single global lock (`GlobalLockCache`) versus lock striping (`ShardedLRU`)
under a pure CPU/Memory workload with zero simulated I/O. This isolates lock contention and OS thread scheduling to
demonstrate the physical limits of Python multi-threading.

## Execution Environment

* **Threads:** 32
* **Total Operations:** 320,000 (10,000 per thread)
* **Workload Distribution:** Uniform. Access probabilities are equal across the key space to perfectly distribute hash
  routing across all shards.
* **Simulated I/O Latency:** 0ms.

## Results

```text
--- THE GIL CEILING BENCHMARK (PURE CPU BOUND) ---
Threads: 32 | Total Ops: 320000 | Distribution: Uniform
Hypothesis: GlobalLock will outperform ShardedLRU due to Python's GIL preventing true parallelism.
--------------------------------------------------------------------------------
Global Lock Cache........  0.1494s | Throughput:   2141534 ops/sec
Sharded LRU (16 Shards)..  0.2233s | Throughput:   1433093 ops/sec
```

## Architectural Conclusions

1. **The GIL Paradox:** In pure-Python multi-threading, CPU-bound tasks cannot execute in true parallel. The CPython
   Global Interpreter Lock (GIL) dictates that only one thread can execute Python bytecode at any given time, forcing
   the OS to serialize execution regardless of core count.
2. **Negative Returns on Sharding:** Because true concurrency is blocked by the GIL, `ShardedLRU` provides zero
   parallelization benefits. Instead, it incurs a severe throughput penalty (dropping from ~2.1M to ~1.4M ops/sec)
   purely due to the CPU overhead of computing `hash()` and modulo routing on every request.
3. **The Single-Node Boundary:** This data empirically shows evidence that for single-node, pure-Python processing, a
   `GlobalLockCache` acts as a highly efficient single lane and is superior. Lock-striping only yields
   positive systemic returns when the GIL boundary is bypassed (e.g., via multi-processing or external distributed
   systems).
