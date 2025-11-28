"""
Benchmarking utilities for FSTMD.

Provides micro-benchmarks comparing FSTMD with other Markdown libraries.
"""

from __future__ import annotations

from fstmd.benchmarks.runner import (
    run_benchmarks,
    benchmark_fstmd,
    benchmark_comparison,
    BenchmarkResult,
)

__all__ = [
    "run_benchmarks",
    "benchmark_fstmd",
    "benchmark_comparison",
    "BenchmarkResult",
]
