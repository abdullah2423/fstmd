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
    
    # Link states [text](url)
    LINK_OPEN: int = auto()           # Seen [
    LINK_TEXT: int = auto()           # Collecting link text
    LINK_TEXT_STAR_ONE: int = auto()  # Seen * in link text
    LINK_TEXT_STAR_TWO: int = auto()  # Seen ** in link text
    LINK_TEXT_ITALIC: int = auto()    # In italic within link text
    LINK_TEXT_BOLD: int = auto()      # In bold within link text
    LINK_TEXT_CLOSE: int = auto()     # Seen ]
    LINK_URL_OPEN: int = auto()       # Seen (
    LINK_URL: int = auto()            # Collecting URL
    
    # Image states ![alt](url)
    IMAGE_BANG: int = auto()          # Seen !
    IMAGE_OPEN: int = auto()          # Seen ![
    IMAGE_ALT: int = auto()           # Collecting alt text
    IMAGE_ALT_CLOSE: int = auto()     # Seen ]
    IMAGE_URL_OPEN: int = auto()      # Seen (
    IMAGE_URL: int = auto()           # Collecting URL


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
    
    # Nested list states - supports -, *, and numbered lists with indentation
    NESTED_LIST_INDENT: int = auto()     # Counting indentation at line start
    NESTED_LIST_MARKER: int = auto()     # Seen list marker (-, *, digit)
    NESTED_LIST_NUMBER: int = auto()     # Collecting number for ordered list
    NESTED_LIST_CONTENT: int = auto()    # List item content
    
    # Table states (GFM subset)
    TABLE_ROW: int = auto()              # Processing table row content
    TABLE_SEPARATOR: int = auto()        # Processing separator row (---, :---:)
    TABLE_CELL: int = auto()             # Processing cell content


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
CHAR_LBRACKET: Final[str] = "["
CHAR_RBRACKET: Final[str] = "]"
CHAR_LPAREN: Final[str] = "("
CHAR_RPAREN: Final[str] = ")"
CHAR_BANG: Final[str] = "!"
CHAR_PIPE: Final[str] = "|"
CHAR_COLON: Final[str] = ":"
CHAR_DOT: Final[str] = "."

# Maximum lookahead buffer size
MAX_LOOKAHEAD: Final[int] = 3

# Maximum heading level
MAX_HEADING_LEVEL: Final[int] = 6
