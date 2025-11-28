"""
FSTMD - Finite-State Markdown Engine

A pure Finite State Transducer (Mealy Machine) based Markdown to HTML converter.
Provides O(N) single-pass processing with no backtracking, regex, or AST.

Example:
    >>> from fstmd import Markdown
    >>> md = Markdown(mode="safe")
    >>> html = md.render("**Hello** *world*")
    >>> print(html)
    <p><strong>Hello</strong> <em>world</em></p>
"""

from __future__ import annotations

from fstmd.parser import Markdown
from fstmd.core.states import State
from fstmd.core.fsm import FST
from fstmd.exceptions import FSTMDError, InvalidInputError, SecurityError

__version__ = "1.0.0"
__author__ = "FSTMD Contributors"
__all__ = [
    "Markdown",
    "State",
    "FST",
    "FSTMDError",
    "InvalidInputError",
    "SecurityError",
    "__version__",
]
