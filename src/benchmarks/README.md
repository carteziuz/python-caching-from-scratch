# Benchmark Results: Systemic I/O Shielding

The following benchmark demonstrates the macro-level impact of introducing an in-memory caching layer in front of simulated external I/O (e.g., database queries, network requests) under highly concurrent workloads.

## Execution Environment
* **Threads:** 16
* **Total Requests:** 1600 (100 per thread)
* **Workload Distribution:** Zipfian (s=1) representing a high-contention 80/20 power-law access pattern.
* **Simulated I/O Latency:** 10ms per cache miss.
* **Cache Capacity:** 100 items.

## Results: Global Lock vs. Baseline

```text
--- SYSTEMIC I/O SHIELDING BENCHMARK ---
Threads: 16 | Total Requests: 1600 | Cache Capacity: 100
---------------------------------------------------------------------------
Baseline (No Cache)......  1.0319s | Hit Rate:   0.00% | DB Calls: 1600
Global Lock Cache........  0.1148s | Hit Rate:  90.50% | DB Calls: 152