"""
State definitions for the Finite State Transducer.

Uses Python enums with __slots__ for memory efficiency.
All states are deterministic with no ambiguity.
"""

from __future__ import annotations

from enum import IntEnum, auto
from typing import Final


class State(IntEnum):
    """
    Inline parsing states for the Mealy Machine FST.
    
    Uses IntEnum for fast comparisons and minimal memory footprint.
    Each state represents a position in the parsing process.
    
    State Diagram (ASCII):
    
    ┌─────────────────────────────────────────────────────────────────┐
    │                        INLINE FST STATES                        │
    ├─────────────────────────────────────────────────────────────────┤
    │                                                                 │
    │   ┌───────┐    '*'     ┌──────────┐    '*'    ┌──────────┐     │
    │   │ TEXT  │───────────►│ STAR_ONE │──────────►│ STAR_TWO │     │
    │   └───┬───┘            └────┬─────┘           └────┬─────┘     │
    │       │                     │                      │            │
    │       │ other               │ other                │ other      │
    │       ▼                     ▼                      ▼            │
    │   output char           start italic           start bold      │
    │                                                                 │
    │   ┌───────────┐        ┌────────────┐                          │
    │   │ IN_ITALIC │◄───────│ STAR_ONE   │ (from TEXT with '*')     │
    │   └─────┬─────┘        └────────────┘                          │
    │         │ '*'                                                   │
    │         ▼                                                       │
    │   ┌──────────────┐                                             │
    │   │ ITALIC_CLOSE │────► output </em>, goto TEXT                │
    │   └──────────────┘                                             │
    │                                                                 │
    │   ┌──────────┐         ┌───────────────┐                       │
    │   │ IN_BOLD  │◄────────│ STAR_TWO      │ (from STAR_ONE)       │
    │   └────┬─────┘         └───────────────┘                       │
    │        │ '*'                                                    │
    │        ▼                                                        │
    │   ┌────────────┐   '*'   ┌─────────────┐                       │
    │   │ BOLD_STAR1 │────────►│ BOLD_CLOSE  │─► output </strong>    │
    │   └────────────┘         └─────────────┘                       │
    │                                                                 │
    │   ┌───────┐    '`'     ┌───────────┐    '`'   ┌───────┐        │
    │   │ TEXT  │───────────►│ IN_CODE   │─────────►│ TEXT  │        │
    │   └───────┘            └───────────┘          └───────┘        │
    │                                                                 │
    └─────────────────────────────────────────────────────────────────┘
    """
    
    # Base text state
    TEXT: int = auto()
    
    # Lookahead states for * vs **
    STAR_ONE: int = auto()
    STAR_TWO: int = auto()
    
    # Italic states
    IN_ITALIC: int = auto()
    ITALIC_STAR: int = auto()
    
    # Bold states  
    IN_BOLD: int = auto()
    BOLD_STAR_ONE: int = auto()
    BOLD_STAR_TWO: int = auto()
    
    # Combined bold+italic states
    IN_BOLD_ITALIC: int = auto()
    BOLD_ITALIC_STAR_ONE: int = auto()
    BOLD_ITALIC_STAR_TWO: int = auto()
    BOLD_ITALIC_STAR_THREE: int = auto()
    
    # Inline code states (`code`)
    IN_CODE: int = auto()


class BlockState(IntEnum):
    """
    Block-level parsing states.
    
    State Diagram (ASCII):
    
    ┌─────────────────────────────────────────────────────────────────┐
    │                        BLOCK FST STATES                         │
    ├─────────────────────────────────────────────────────────────────┤
    │                                                                 │
    │   ┌──────────┐                                                  │
    │   │  START   │ ─────────────────────────────────────────────┐   │
    │   └────┬─────┘                                               │   │
    │        │                                                      │   │
    │    ┌───┴───┐   '#'     ┌──────────┐                          │   │
    │    │ LINE  │──────────►│ HEADING  │──► count #'s, emit <hN>  │   │
    │    │ START │           └──────────┘                          │   │
    │    └───┬───┘                                                  │   │
    │        │                                                      │   │
    │        │   '-'    ┌───────────────┐                          │   │
    │        ├─────────►│ LIST_ITEM     │──► emit <li>             │   │
    │        │          └───────────────┘                          │   │
    │        │                                                      │   │
    │        │   '>'    ┌───────────────┐                          │   │
    │        ├─────────►│ BLOCKQUOTE    │──► emit <blockquote>     │   │
    │        │          └───────────────┘                          │   │
    │        │                                                      │   │
    │        │   '```'  ┌───────────────┐                          │   │
    │        ├─────────►│ CODE_BLOCK    │──► emit <pre><code>      │   │
    │        │          └───────────────┘                          │   │
    │        │                                                      │   │
    │        │   '\n'   ┌───────────────┐                          │   │
    │        ├─────────►│ BLANK_LINE    │──► close paragraph       │   │
    │        │          └───────────────┘                          │   │
    │        │                                                      │   │
    │        │  other   ┌───────────────┐                          │   │
    │        └─────────►│ PARAGRAPH     │──► emit <p>              │   │
    │                   └───────────────┘                          │   │
    │                                                                 │
    └─────────────────────────────────────────────────────────────────┘
    """
    
    # Document start
    START: int = auto()
    
    # Line-level states
    LINE_START: int = auto()
    
    # Heading states (# through ######)
    HEADING_START: int = auto()
    HEADING_HASHES: int = auto()
    HEADING_SPACE: int = auto()
    HEADING_CONTENT: int = auto()
    
    # List states
    LIST_MARKER: int = auto()
    LIST_SPACE: int = auto()
    LIST_CONTENT: int = auto()
    
    # Paragraph state
    PARAGRAPH: int = auto()
    
    # Blank line handling
    BLANK_LINE: int = auto()
    
    # End of document
    END: int = auto()
    
    # Code block states (```)
    CODE_BLOCK_TICK_ONE: int = auto()
    CODE_BLOCK_TICK_TWO: int = auto()
    CODE_BLOCK_CONTENT: int = auto()
    CODE_BLOCK_CLOSE_ONE: int = auto()
    CODE_BLOCK_CLOSE_TWO: int = auto()
    
    # Blockquote states (>)
    BLOCKQUOTE_START: int = auto()
    BLOCKQUOTE_CONTENT: int = auto()


# Character constants for fast comparison
CHAR_STAR: Final[str] = "*"
CHAR_HASH: Final[str] = "#"
CHAR_DASH: Final[str] = "-"
CHAR_SPACE: Final[str] = " "
CHAR_NEWLINE: Final[str] = "\n"
CHAR_TAB: Final[str] = "\t"
CHAR_LT: Final[str] = "<"
CHAR_GT: Final[str] = ">"
CHAR_AMP: Final[str] = "&"
CHAR_QUOT: Final[str] = '"'
CHAR_APOS: Final[str] = "'"
CHAR_BACKTICK: Final[str] = "`"

# Maximum lookahead buffer size
MAX_LOOKAHEAD: Final[int] = 3

# Maximum heading level
MAX_HEADING_LEVEL: Final[int] = 6
