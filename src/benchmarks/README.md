# Python Caching Benchmarks

This directory contains the empirical data and reproducible benchmark scripts used to evaluate the architectural
trade-offs of the `single_node` caching library.

## Experiment Logs

1. [`01_macro_io_shielding.md`](./01_macro_io_shielding.md): Demonstrates the systemic latency reduction of caching
   against high-latency I/O operations.
2. [`02_gil_ceiling_cpu_bound.md`](./02_gil_ceiling_cpu_bound.md): Illustrates the limits of CPython multi-threading and
   the overhead of lock-striping in pure CPU-bound contexts.
3. [`03_io_bound_sharding.md`](./03_io_bound_sharding.md): Provides evidence that lock-striping adds structural
   complexity with minimal systemic benefit for typical I/O-bound workloads.

---

## The Single-Node Architectural Boundary

Through rigorous testing against assumed standard workloads (e.g., highly skewed Zipfian database access patterns), we
explored the concurrency boundaries of a single-node Python cache.

The collected evidence suggests that the **`GlobalLockCache` is a highly efficient and pragmatic default for a single
CPython process.**

Under typical operational conditions, efforts to optimize via lock striping (`ShardedLRU`) introduced structural
complexity and routing latency that largely outweighed the concurrency benefits. This behavior is driven by two key
constraints:

1. **The Global Interpreter Lock (GIL):** Prevents true parallel execution of Python bytecode, meaning threaded
   lock-striping yields minimal CPU-bound parallelization.
2. **I/O Latency Dominance:** In I/O-bound scenarios, the time spent waiting for network/database responses dwarfs local
   mutex contention, rendering the global lock effectively uncontended.

### The Multiprocessing Trade-off

A common hypothesis to bypass the GIL is to utilize Python's `multiprocessing` module for true parallel execution. For
an in-memory cache, this introduces two significant architectural challenges:

1. **Memory Isolation:** OS processes do not share memory space natively. Instantiating a cache across multiple
   processes results in isolated caches, which fragments the systemic hit-rate.
2. **IPC Overhead:** Sharing state across processes requires Inter-Process Communication (e.g.,
   `multiprocessing.Manager`). This forces cache reads/writes to be serialized (Pickled) and sent over local sockets.
   The latency of IPC and serialization frequently exceeds the overhead of simply waiting for a threaded global lock.

### The Path Forward: Scaling Beyond the GIL

When systemic throughput requirements exceed the natural concurrency limits of the runtime environment, the architecture
must pivot. Based on our single-node findings, there are two primary engineering paths forward:

1. **Horizontal Scaling (Distributed Architecture):** Transition from a `single_node` embedded model to a multi-node
   `distributed` architecture. By offloading the cache to an external, highly-concurrent engine (e.g., Redis,
   Memcached), we bypass the CPython GIL entirely, allowing multiple Python workers to access shared state concurrently
   over TCP.
2. **Vertical Scaling (Language Swap):** If ultra-low latency, single-node lock striping is a strict technical
   requirement, Python may be the incorrect tool for that specific layer. The caching service should be delegated to a
   language with mature, GIL-free parallel execution models (e.g., Go, Rust, C++).