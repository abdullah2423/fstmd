"""
Transition table for the Finite State Transducer.

Implements deterministic state transitions with output functions.
Uses immutable tuples for memory efficiency and cache-friendliness.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final
from functools import cache

from fstmd.core.states import (
    State,
    CHAR_STAR,
)


@dataclass(frozen=True, slots=True)
class Transition:
    """
    Represents a single FST transition.
    
    Attributes:
        next_state: The state to transition to
        output: The HTML output to emit (empty string for no output)
        consume: Whether to consume the input character
    """
    next_state: State
    output: str
    consume: bool = True


# Type alias for transition key
TransitionKey = tuple[State, str]

# HTML output constants - using Final for compiler optimization hints
HTML_EM_OPEN: Final[str] = "<em>"
HTML_EM_CLOSE: Final[str] = "</em>"
HTML_STRONG_OPEN: Final[str] = "<strong>"
HTML_STRONG_CLOSE: Final[str] = "</strong>"
HTML_EMPTY: Final[str] = ""


class TransitionTable:
    """
    Transition table implementing the Mealy Machine for inline Markdown.
    
    The table maps (current_state, input_char) -> Transition.
    Uses a dictionary with tuple keys for O(1) lookups.
    
    Key Design Decisions:
    1. Two-character lookahead for * vs ** disambiguation
    2. No backtracking - all decisions are final
    3. Output is generated during transitions (Mealy machine)
    4. Missing transitions fall back to default behavior
    """
    
    __slots__ = ("_table", "_default_outputs")
    
    def __init__(self) -> None:
        self._table: dict[TransitionKey, Transition] = {}
        self._default_outputs: dict[State, str] = {}
        self._build_table()
    
    def _build_table(self) -> None:
        """Build the complete transition table."""
        # TEXT state transitions
        self._add(State.TEXT, CHAR_STAR, Transition(State.STAR_ONE, HTML_EMPTY, True))
        
        # STAR_ONE state - lookahead for * vs **
        self._add(State.STAR_ONE, CHAR_STAR, Transition(State.STAR_TWO, HTML_EMPTY, True))
        # Any other char after single * means italic start
        
        # STAR_TWO state - we've seen **, start bold
        self._add(State.STAR_TWO, CHAR_STAR, Transition(State.IN_BOLD_ITALIC, HTML_STRONG_OPEN + HTML_EM_OPEN, True))
        # Any other char means bold start
        
        # IN_ITALIC state transitions
        self._add(State.IN_ITALIC, CHAR_STAR, Transition(State.ITALIC_STAR, HTML_EMPTY, True))
        
        # ITALIC_STAR - potential close
        self._add(State.ITALIC_STAR, CHAR_STAR, Transition(State.IN_BOLD, HTML_EM_CLOSE + HTML_STRONG_OPEN, True))
        # Any other char closes italic
        
        # IN_BOLD state transitions
        self._add(State.IN_BOLD, CHAR_STAR, Transition(State.BOLD_STAR_ONE, HTML_EMPTY, True))
        
        # BOLD_STAR_ONE - first star seen in bold
        self._add(State.BOLD_STAR_ONE, CHAR_STAR, Transition(State.BOLD_STAR_TWO, HTML_EMPTY, True))
        
        # BOLD_STAR_TWO - second star seen, close bold
        self._add(State.BOLD_STAR_TWO, CHAR_STAR, Transition(State.TEXT, HTML_STRONG_CLOSE + CHAR_STAR, True))
        
        # IN_BOLD_ITALIC state transitions
        self._add(State.IN_BOLD_ITALIC, CHAR_STAR, Transition(State.BOLD_ITALIC_STAR_ONE, HTML_EMPTY, True))
        
        # BOLD_ITALIC_STAR_ONE
        self._add(State.BOLD_ITALIC_STAR_ONE, CHAR_STAR, Transition(State.BOLD_ITALIC_STAR_TWO, HTML_EMPTY, True))
        
        # BOLD_ITALIC_STAR_TWO
        self._add(State.BOLD_ITALIC_STAR_TWO, CHAR_STAR, Transition(State.BOLD_ITALIC_STAR_THREE, HTML_EMPTY, True))
        
        # BOLD_ITALIC_STAR_THREE - close both
        self._add(State.BOLD_ITALIC_STAR_THREE, CHAR_STAR, Transition(State.TEXT, HTML_EM_CLOSE + HTML_STRONG_CLOSE + CHAR_STAR, True))
        
        # Set default outputs for states (when no specific transition matches)
        self._default_outputs = {
            State.TEXT: HTML_EMPTY,
            State.IN_ITALIC: HTML_EMPTY,
            State.IN_BOLD: HTML_EMPTY,
            State.IN_BOLD_ITALIC: HTML_EMPTY,
        }
    
    def _add(self, state: State, char: str, transition: Transition) -> None:
        """Add a transition to the table."""
        self._table[(state, char)] = transition
    
    @cache
    def get(self, state: State, char: str) -> Transition | None:
        """
        Get the transition for a (state, char) pair.
        
        Returns None if no specific transition exists.
        Cached for repeated lookups.
        """
        return self._table.get((state, char))
    
    def get_default_output(self, state: State) -> str:
        """Get the default output for a state."""
        return self._default_outputs.get(state, HTML_EMPTY)


# Singleton instance for reuse
_TRANSITION_TABLE: TransitionTable | None = None


def get_transition_table() -> TransitionTable:
    """Get the singleton transition table instance."""
    global _TRANSITION_TABLE
    if _TRANSITION_TABLE is None:
        _TRANSITION_TABLE = TransitionTable()
    return _TRANSITION_TABLE
