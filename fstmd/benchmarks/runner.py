"""
Benchmark runner for FSTMD.

Compares performance against:
- Python-Markdown
- commonmark-py
- markdown-it-py
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable
from functools import lru_cache


@dataclass(slots=True, frozen=True)
class BenchmarkResult:
    """Result of a single benchmark run."""
    name: str
    iterations: int
    total_time_ms: float
    avg_time_ms: float
    throughput_chars_per_sec: float
    input_size: int
    
    def __str__(self) -> str:
        return (
            f"{self.name}:\n"
            f"  Iterations: {self.iterations}\n"
            f"  Total time: {self.total_time_ms:.2f} ms\n"
            f"  Avg time: {self.avg_time_ms:.4f} ms\n"
            f"  Throughput: {self.throughput_chars_per_sec:.0f} chars/sec\n"
            f"  Input size: {self.input_size} chars"
        )


# Test documents of varying sizes
SMALL_DOC = """# Hello World

This is a **bold** and *italic* test.

- Item 1
- Item 2
- Item 3
"""

MEDIUM_DOC = """# FSTMD Benchmark Document

## Introduction

This is a **medium-sized** document for *benchmarking* the FSTMD library.
It contains various **Markdown** elements including *inline* formatting.

## Features

- Fast O(N) parsing
- No backtracking
- Pure FST implementation
- Zero dependencies

## Performance

The library processes text **character by character** using a *finite state transducer*.
This ensures **consistent** performance regardless of input complexity.

### Technical Details

The parser uses a **Mealy machine** with *deterministic* transitions.
Each character is processed *exactly once* with no lookahead beyond **2 characters**.

## Conclusion

FSTMD provides **fast** and *reliable* Markdown parsing for Python 3.13+.
"""

LARGE_DOC = MEDIUM_DOC * 100  # ~50KB of markdown


def _time_function(func: Callable[[], str], iterations: int) -> float:
    """Time a function over multiple iterations, return total time in seconds."""
    start = time.perf_counter()
    for _ in range(iterations):
        func()
    end = time.perf_counter()
    return end - start


def benchmark_fstmd(
    text: str = MEDIUM_DOC,
    iterations: int = 1000,
    mode: str = "safe"
) -> BenchmarkResult:
    """
    Benchmark FSTMD on the given text.
    
    Args:
        text: Markdown text to parse
        iterations: Number of iterations
        mode: Parsing mode ("safe" or "raw")
        
    Returns:
        BenchmarkResult with timing data
    """
    from fstmd import Markdown
    
    md = Markdown(mode=mode)  # type: ignore[arg-type]
    
    # Warmup
    for _ in range(10):
        md.render(text)
    
    # Clear any caches that might affect results
    render_func = lambda: md.render(text)  # noqa: E731
    
    total_time = _time_function(render_func, iterations)
    total_time_ms = total_time * 1000
    avg_time_ms = total_time_ms / iterations
    input_size = len(text)
    throughput = (input_size * iterations) / total_time if total_time > 0 else 0
    
    return BenchmarkResult(
        name="FSTMD",
        iterations=iterations,
        total_time_ms=total_time_ms,
        avg_time_ms=avg_time_ms,
        throughput_chars_per_sec=throughput,
        input_size=input_size,
    )


def _benchmark_python_markdown(text: str, iterations: int) -> BenchmarkResult | None:
    """Benchmark Python-Markdown library."""
    try:
        import markdown
        
        md = markdown.Markdown()
        
        # Warmup
        for _ in range(10):
            md.reset()
            md.convert(text)
        
        def render() -> str:
            md.reset()
            return md.convert(text)
        
        total_time = _time_function(render, iterations)
        total_time_ms = total_time * 1000
        avg_time_ms = total_time_ms / iterations
        input_size = len(text)
        throughput = (input_size * iterations) / total_time if total_time > 0 else 0
        
        return BenchmarkResult(
            name="Python-Markdown",
            iterations=iterations,
            total_time_ms=total_time_ms,
            avg_time_ms=avg_time_ms,
            throughput_chars_per_sec=throughput,
            input_size=input_size,
        )
    except ImportError:
        return None


def _benchmark_commonmark(text: str, iterations: int) -> BenchmarkResult | None:
    """Benchmark commonmark-py library."""
    try:
        import commonmark
        
        parser = commonmark.Parser()
        renderer = commonmark.HtmlRenderer()
        
        # Warmup
        for _ in range(10):
            ast = parser.parse(text)
            renderer.render(ast)
        
        def render() -> str:
            ast = parser.parse(text)
            return renderer.render(ast)
        
        total_time = _time_function(render, iterations)
        total_time_ms = total_time * 1000
        avg_time_ms = total_time_ms / iterations
        input_size = len(text)
        throughput = (input_size * iterations) / total_time if total_time > 0 else 0
        
        return BenchmarkResult(
            name="CommonMark-Py",
            iterations=iterations,
            total_time_ms=total_time_ms,
            avg_time_ms=avg_time_ms,
            throughput_chars_per_sec=throughput,
            input_size=input_size,
        )
    except ImportError:
        return None


def _benchmark_markdown_it(text: str, iterations: int) -> BenchmarkResult | None:
    """Benchmark markdown-it-py library."""
    try:
        from markdown_it import MarkdownIt
        
        md = MarkdownIt()
        
        # Warmup
        for _ in range(10):
            md.render(text)
        
        def render() -> str:
            return md.render(text)
        
        total_time = _time_function(render, iterations)
        total_time_ms = total_time * 1000
        avg_time_ms = total_time_ms / iterations
        input_size = len(text)
        throughput = (input_size * iterations) / total_time if total_time > 0 else 0
        
        return BenchmarkResult(
            name="markdown-it-py",
            iterations=iterations,
            total_time_ms=total_time_ms,
            avg_time_ms=avg_time_ms,
            throughput_chars_per_sec=throughput,
            input_size=input_size,
        )
    except ImportError:
        return None


def benchmark_comparison(
    text: str = MEDIUM_DOC,
    iterations: int = 1000
) -> list[BenchmarkResult]:
    """
    Run benchmarks comparing FSTMD with other libraries.
    
    Args:
        text: Markdown text to parse
        iterations: Number of iterations
        
    Returns:
        List of BenchmarkResult objects, sorted by throughput
    """
    results: list[BenchmarkResult] = []
    
    # Always benchmark FSTMD
    results.append(benchmark_fstmd(text, iterations))
    
    # Try to benchmark other libraries
    python_md = _benchmark_python_markdown(text, iterations)
    if python_md:
        results.append(python_md)
    
    commonmark_result = _benchmark_commonmark(text, iterations)
    if commonmark_result:
        results.append(commonmark_result)
    
    markdown_it_result = _benchmark_markdown_it(text, iterations)
    if markdown_it_result:
        results.append(markdown_it_result)
    
    # Sort by throughput (fastest first)
    results.sort(key=lambda r: r.throughput_chars_per_sec, reverse=True)
    
    return results


def run_benchmarks(
    sizes: tuple[str, ...] = ("small", "medium", "large"),
    iterations: int = 1000
) -> dict[str, list[BenchmarkResult]]:
    """
    Run comprehensive benchmarks across different document sizes.
    
    Args:
        sizes: Document sizes to test ("small", "medium", "large")
        iterations: Number of iterations per test
        
    Returns:
        Dictionary mapping size names to benchmark results
    """
    docs = {
        "small": SMALL_DOC,
        "medium": MEDIUM_DOC,
        "large": LARGE_DOC,
    }
    
    results: dict[str, list[BenchmarkResult]] = {}
    
    for size in sizes:
        if size in docs:
            results[size] = benchmark_comparison(docs[size], iterations)
    
    return results


def print_benchmark_results(results: dict[str, list[BenchmarkResult]]) -> None:
    """Pretty-print benchmark results."""
    for size, benchmark_results in results.items():
        print(f"\n{'=' * 60}")
        print(f"Document Size: {size.upper()}")
        print(f"{'=' * 60}")
        
        if not benchmark_results:
            print("No results")
            continue
        
        # Header
        print(f"{'Library':<20} {'Avg (ms)':<12} {'Throughput':<15} {'Relative':<10}")
        print("-" * 60)
        
        # Use fastest as baseline
        baseline = benchmark_results[0].throughput_chars_per_sec
        
        for result in benchmark_results:
            relative = result.throughput_chars_per_sec / baseline if baseline > 0 else 0
            throughput_str = f"{result.throughput_chars_per_sec / 1_000_000:.2f}M/s"
            print(
                f"{result.name:<20} "
                f"{result.avg_time_ms:<12.4f} "
                f"{throughput_str:<15} "
                f"{relative:.2f}x"
            )


if __name__ == "__main__":
    print("FSTMD Benchmark Suite")
    print("=" * 60)
    
    results = run_benchmarks()
    print_benchmark_results(results)
