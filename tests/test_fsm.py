"""
Tests for the FST (Finite State Transducer) implementation.
"""

from __future__ import annotations

import pytest
from fstmd.core.fsm import FST, OutputMode, FSTContext
from fstmd.core.states import State, BlockState


class TestFSTBasics:
    """Basic FST functionality tests."""
    
    def test_create_fst(self) -> None:
        """Test FST creation."""
        fst = FST()
        assert fst is not None
    
    def test_create_fst_safe_mode(self) -> None:
        """Test FST creation with safe mode."""
        fst = FST(mode=OutputMode.SAFE)
        assert fst is not None
    
    def test_create_fst_raw_mode(self) -> None:
        """Test FST creation with raw mode."""
        fst = FST(mode=OutputMode.RAW)
        assert fst is not None
    
    def test_process_empty(self) -> None:
        """Test processing empty string."""
        fst = FST()
        result = fst.process("")
        assert result == ""
    
    def test_process_simple_text(self) -> None:
        """Test processing simple text."""
        fst = FST()
        result = fst.process("Hello World")
        assert "Hello World" in result
    
    def test_process_returns_string(self) -> None:
        """Test that process always returns string."""
        fst = FST()
        result = fst.process("test")
        assert isinstance(result, str)


class TestStateTransitions:
    """Tests for FST state transitions."""
    
    def test_text_to_star_one(self) -> None:
        """Test transition from TEXT to STAR_ONE."""
        fst = FST()
        result = fst.process("*")
        # Should handle single star
        assert result is not None
    
    def test_star_one_to_star_two(self) -> None:
        """Test transition from STAR_ONE to STAR_TWO."""
        fst = FST()
        result = fst.process("**")
        # Should handle double star
        assert result is not None
    
    def test_italic_open_close(self) -> None:
        """Test italic state transitions."""
        fst = FST()
        result = fst.process("*text*")
        assert "<em>" in result
        assert "</em>" in result
    
    def test_bold_open_close(self) -> None:
        """Test bold state transitions."""
        fst = FST()
        result = fst.process("**text**")
        assert "<strong>" in result
        assert "</strong>" in result


class TestBlockStates:
    """Tests for block-level state handling."""
    
    def test_paragraph_state(self) -> None:
        """Test paragraph state."""
        fst = FST()
        result = fst.process("paragraph text")
        assert "<p>" in result
        assert "</p>" in result
    
    def test_heading_state(self) -> None:
        """Test heading state."""
        fst = FST()
        result = fst.process("# heading")
        assert "<h1>" in result
        assert "</h1>" in result
    
    def test_list_state(self) -> None:
        """Test list state."""
        fst = FST()
        result = fst.process("- item")
        assert "<ul>" in result
        assert "<li>" in result


class TestContextManagement:
    """Tests for FST context handling."""
    
    def test_context_creation(self) -> None:
        """Test that context is created properly."""
        fst = FST()
        ctx = fst._create_context()
        assert ctx.inline_state == State.TEXT
        assert ctx.block_state == BlockState.START
        assert ctx.pending_stars == 0
    
    def test_context_isolation(self) -> None:
        """Test that each process call has isolated context."""
        fst = FST()
        result1 = fst.process("*italic*")
        result2 = fst.process("**bold**")
        # Both should work correctly without interference
        assert "<em>" in result1
        assert "<strong>" in result2


class TestDeterminism:
    """Tests for deterministic output."""
    
    def test_same_input_same_output(self) -> None:
        """Test that same input produces same output."""
        fst = FST()
        input_text = "**Hello** *World*"
        result1 = fst.process(input_text)
        result2 = fst.process(input_text)
        assert result1 == result2
    
    def test_deterministic_complex(self) -> None:
        """Test determinism with complex input."""
        fst = FST()
        input_text = "# Title\n\n**Bold** and *italic*\n\n- item1\n- item2"
        results = [fst.process(input_text) for _ in range(10)]
        assert all(r == results[0] for r in results)


class TestComplexity:
    """Tests related to O(N) complexity."""
    
    def test_linear_scaling(self) -> None:
        """Test that processing time scales linearly."""
        import time
        
        fst = FST()
        base_text = "Hello **world** and *universe*\n"
        
        # Time for small input
        small_input = base_text * 100
        start = time.perf_counter()
        fst.process(small_input)
        small_time = time.perf_counter() - start
        
        # Time for large input (10x)
        large_input = base_text * 1000
        start = time.perf_counter()
        fst.process(large_input)
        large_time = time.perf_counter() - start
        
        # Large should be roughly 10x small (allow 20x for overhead)
        # This is a rough check for linear complexity
        assert large_time < small_time * 20 if small_time > 0 else True
    
    def test_no_exponential_blowup(self) -> None:
        """Test that pathological input doesn't cause exponential time."""
        fst = FST()
        
        # Pathological input that might cause backtracking in naive parsers
        pathological = "*" * 100 + "a" + "*" * 100
        
        import time
        start = time.perf_counter()
        result = fst.process(pathological)
        elapsed = time.perf_counter() - start
        
        # Should complete quickly (< 1 second for this small input)
        assert elapsed < 1.0
        assert result is not None
