"""
High-level Markdown parser API.

Provides the main Markdown class that users interact with.
Wraps the FST engine with a clean, user-friendly interface.
"""

from __future__ import annotations

from typing import Literal
from functools import lru_cache

from fstmd.core.fsm import FST, OutputMode
from fstmd.core.safe_html import HTMLEscaper
from fstmd.exceptions import InvalidInputError, SecurityError


# Type alias for mode parameter
RenderMode = Literal["safe", "raw"]


class Markdown:
    """
    High-level Markdown to HTML converter.
    
    Uses a Finite State Transducer for O(N) single-pass parsing
    with no backtracking, regex, or AST construction.
    
    Example:
        >>> md = Markdown(mode="safe")
        >>> html = md.render("**Hello** *world*")
        >>> print(html)
        <p><strong>Hello</strong> <em>world</em></p>
    
    Modes:
        - "safe": Escapes all HTML special characters (default, recommended)
        - "raw": Passes through HTML as-is (use only with trusted input)
    
    Security:
        The "safe" mode prevents XSS attacks by escaping:
        - < and > (tag injection)
        - & (entity injection)
        - " and ' (attribute injection)
    
    Thread Safety:
        Markdown instances are thread-safe for rendering.
        Each render call creates its own parsing context.
    """
    
    __slots__ = ("_mode", "_fst", "_strict")
    
    def __init__(
        self, 
        mode: RenderMode = "safe",
        strict: bool = False
    ) -> None:
        """
        Initialize the Markdown parser.
        
        Args:
            mode: Output mode ("safe" or "raw")
            strict: If True, raise exceptions on security issues instead of escaping
        """
        self._mode = mode
        self._strict = strict
        
        output_mode = OutputMode.SAFE if mode == "safe" else OutputMode.RAW
        self._fst = FST(mode=output_mode)
    
    @property
    def mode(self) -> RenderMode:
        """Get the current rendering mode."""
        return self._mode
    
    @property
    def strict(self) -> bool:
        """Get whether strict mode is enabled."""
        return self._strict
    
    def render(self, text: str) -> str:
        """
        Render Markdown text to HTML.
        
        Args:
            text: Markdown input text
            
        Returns:
            HTML output string
            
        Raises:
            InvalidInputError: If input is invalid (None, wrong type, too long)
            SecurityError: In strict mode, if dangerous patterns are detected
        """
        # Validate input
        if text is None:
            raise InvalidInputError("Input cannot be None")
        
        if not isinstance(text, str):
            raise InvalidInputError(f"Input must be string, got {type(text).__name__}")
        
        if not HTMLEscaper.validate_input(text):
            raise InvalidInputError("Input exceeds maximum allowed length")
        
        # Security check in strict mode
        if self._strict and self._mode == "raw":
            if HTMLEscaper.contains_dangerous_pattern(text):
                raise SecurityError("Dangerous pattern detected in raw mode")
        
        # Process through FST
        return self._fst.process(text)
    
    def render_safe(self, text: str) -> str:
        """
        Always render in safe mode, regardless of instance mode.
        
        Convenience method for when you need guaranteed safe output.
        
        Args:
            text: Markdown input text
            
        Returns:
            Safely escaped HTML output
        """
        safe_fst = FST(mode=OutputMode.SAFE)
        
        if text is None:
            raise InvalidInputError("Input cannot be None")
        
        if not isinstance(text, str):
            raise InvalidInputError(f"Input must be string, got {type(text).__name__}")
        
        if not HTMLEscaper.validate_input(text):
            raise InvalidInputError("Input exceeds maximum allowed length")
        
        return safe_fst.process(text)
    
    def __repr__(self) -> str:
        return f"Markdown(mode={self._mode!r}, strict={self._strict!r})"


@lru_cache(maxsize=128)
def render(text: str, mode: RenderMode = "safe") -> str:
    """
    Convenience function to render Markdown to HTML.
    
    Results are cached for repeated calls with the same input.
    
    Args:
        text: Markdown input text
        mode: Output mode ("safe" or "raw")
        
    Returns:
        HTML output string
        
    Example:
        >>> from fstmd import render
        >>> html = render("**bold**")
        >>> print(html)
        <p><strong>bold</strong></p>
    """
    md = Markdown(mode=mode)
    return md.render(text)


def render_unsafe(text: str) -> str:
    """
    Render Markdown without HTML escaping.
    
    WARNING: Only use with trusted input.
    This function does not escape HTML and is vulnerable to XSS.
    
    Args:
        text: Trusted Markdown input text
        
    Returns:
        HTML output string (unescaped)
    """
    md = Markdown(mode="raw")
    return md.render(text)
