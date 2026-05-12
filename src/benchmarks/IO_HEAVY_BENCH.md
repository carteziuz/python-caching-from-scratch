# I/O Bound Sharding Comparison

**Objective:** Evaluate if lock striping (`ShardedLRU`) provides systemic benefits over a single lock (`GlobalLockCache`) when threads actively release the GIL during blocking I/O.

## Execution Environment
* **Threads:** 32
* **Total Requests:** 3,200 (100 per thread)
* **Workload Distribution:** Zipfian (s=1) simulating real-world database skew.
* **Simulated I/O Latency:** 10ms per cache miss.

## Results
```text
--- I/O SHIELDING BENCHMARK (GIL RELEASED) ---
Threads: 32 | Total Requests: 3200 | Distribution: Zipfian
-------------------------------------------------------------------------------------
Baseline (No Cache)......  1.0685s | Hit Rate:   0.00% | DB Calls: 3200
Global Lock Cache........  0.1163s | Hit Rate:  90.75% | DB Calls: 296
Sharded LRU (16 Shards)..  0.1366s | Hit Rate:  90.19% | DB Calls: 314
```

## Conclusions

A 10ms I/O delay mathematically dwarfs lock acquisition times. Because Python threads drop the GIL during the I/O sleep, the global lock is effectively uncontended.

The data proves that the ShardedLRU provides no systemic latency benefit in an I/O-bound context. Furthermore, it results in a slightly lower hit rate (90.19% vs 90.75%) due to the fragmented capacity of individual shards, and executes slightly slower due to the overhead of hashing and routing keys to specific locks.

**Verdict**: For I/O-heavy single-node applications, GlobalLockCache is the superior implementation due to its simplicity, strict LRU accuracy, and lack of computational overhead.