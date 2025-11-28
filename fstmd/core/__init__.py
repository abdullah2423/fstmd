"""
Core module for the Finite State Transducer Markdown Engine.
"""

from __future__ import annotations

from fstmd.core.states import State, BlockState
from fstmd.core.fsm import FST
from fstmd.core.transitions import TransitionTable
from fstmd.core.safe_html import HTMLEscaper

__all__ = [
    "State",
    "BlockState",
    "FST",
    "TransitionTable",
    "HTMLEscaper",
]
