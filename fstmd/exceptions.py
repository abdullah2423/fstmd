"""
Exception classes for FSTMD.

All exceptions are lightweight with __slots__ for memory efficiency.
"""

from __future__ import annotations


class FSTMDError(Exception):
    """
    Base exception for all FSTMD errors.
    
    Provides a common base class for catching all library-specific errors.
    """
    __slots__ = ("message", "position", "line", "column")
    
    def __init__(
        self, 
        message: str, 
        position: int = -1, 
        line: int = -1, 
        column: int = -1
    ) -> None:
        super().__init__(message)
        self.message = message
        self.position = position
        self.line = line
        self.column = column
    
    def __str__(self) -> str:
        if self.line > 0 and self.column > 0:
            return f"{self.message} at line {self.line}, column {self.column}"
        if self.position >= 0:
            return f"{self.message} at position {self.position}"
        return self.message


class InvalidInputError(FSTMDError):
    """
    Raised when input validation fails.
    
    This includes:
    - None input
    - Non-string input
    - Input exceeding maximum length
    """
    __slots__ = ()
    
    def __init__(self, message: str = "Invalid input") -> None:
        super().__init__(message)


class SecurityError(FSTMDError):
    """
    Raised when a security violation is detected.
    
    This includes:
    - Script injection attempts
    - Dangerous URL schemes
    - Other XSS vectors
    """
    __slots__ = ("pattern",)
    
    def __init__(self, message: str = "Security violation detected", pattern: str = "") -> None:
        super().__init__(message)
        self.pattern = pattern
    
    def __str__(self) -> str:
        if self.pattern:
            return f"{self.message}: detected pattern '{self.pattern}'"
        return self.message


class StateError(FSTMDError):
    """
    Raised when an invalid state transition is attempted.
    
    This is primarily for internal debugging and should not
    occur in normal operation due to the deterministic nature
    of the FST.
    """
    __slots__ = ("from_state", "to_state", "input_char")
    
    def __init__(
        self, 
        message: str = "Invalid state transition",
        from_state: str = "",
        to_state: str = "",
        input_char: str = ""
    ) -> None:
        super().__init__(message)
        self.from_state = from_state
        self.to_state = to_state
        self.input_char = input_char
    
    def __str__(self) -> str:
        if self.from_state and self.to_state:
            return f"{self.message}: {self.from_state} -> {self.to_state} on '{self.input_char}'"
        return self.message


class ParserError(FSTMDError):
    """
    Raised when a parsing error occurs.
    
    Includes position information for debugging.
    """
    __slots__ = ()
