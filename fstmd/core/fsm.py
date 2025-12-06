"""
Core Finite State Transducer (Mealy Machine) implementation.

This module contains the main FST engine that processes Markdown
character-by-character with O(N) time complexity.

Key Design Principles:
- Single-pass processing
- No backtracking
- No regex
- No AST construction
- Maximum 2-character lookahead
- Deterministic state transitions
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final
from enum import Enum, auto

from fstmd.core.states import (
    State,
    BlockState,
    CHAR_STAR,
    CHAR_HASH,
    CHAR_DASH,
    CHAR_SPACE,
    CHAR_NEWLINE,
    CHAR_BACKTICK,
    CHAR_GT,
    MAX_HEADING_LEVEL,
)
from fstmd.core.safe_html import HTMLEscaper, escape_html


class OutputMode(Enum):
    """Output mode for the FST."""
    SAFE = auto()   # Escape all HTML
    RAW = auto()    # Pass through raw (trusted input only)


@dataclass(slots=True)
class FSTContext:
    """
    Mutable context for FST processing.
    
    Uses __slots__ for memory efficiency.
    Maintains all state needed during parsing.
    """
    # Output buffer
    output: list[str]
    
    # Current inline state
    inline_state: State
    
    # Current block state
    block_state: BlockState
    
    # Pending stars for lookahead
    pending_stars: int
    
    # Current heading level (1-6)
    heading_level: int
    
    # Whether we're in a list
    in_list: bool
    
    # Whether we're in a paragraph
    in_paragraph: bool
    
    # Buffer for inline content
    inline_buffer: list[str]
    
    # Position in input (for error reporting)
    position: int
    
    # Line number (for error reporting)
    line: int
    
    # Column number (for error reporting)
    column: int
    
    # Blockquote depth (for nested blockquotes)
    blockquote_depth: int
    
    # Whether we're in a code block
    in_code_block: bool
    
    # Buffer for code block content
    code_block_buffer: list[str]
    
    # Pending backticks count for code block detection
    pending_backticks: int


# HTML output constants
HTML_P_OPEN: Final[str] = "<p>"
HTML_P_CLOSE: Final[str] = "</p>"
HTML_UL_OPEN: Final[str] = "<ul>"
HTML_UL_CLOSE: Final[str] = "</ul>"
HTML_LI_OPEN: Final[str] = "<li>"
HTML_LI_CLOSE: Final[str] = "</li>"
HTML_EM_OPEN: Final[str] = "<em>"
HTML_EM_CLOSE: Final[str] = "</em>"
HTML_STRONG_OPEN: Final[str] = "<strong>"
HTML_STRONG_CLOSE: Final[str] = "</strong>"
HTML_BR: Final[str] = "<br>"
HTML_NEWLINE: Final[str] = "\n"
HTML_CODE_OPEN: Final[str] = "<code>"
HTML_CODE_CLOSE: Final[str] = "</code>"
HTML_PRE_OPEN: Final[str] = "<pre>"
HTML_PRE_CLOSE: Final[str] = "</pre>"
HTML_BLOCKQUOTE_OPEN: Final[str] = "<blockquote>"
HTML_BLOCKQUOTE_CLOSE: Final[str] = "</blockquote>"

# Heading tags lookup table
HEADING_OPEN: Final[tuple[str, ...]] = (
    "",  # Index 0 unused
    "<h1>",
    "<h2>",
    "<h3>",
    "<h4>",
    "<h5>",
    "<h6>",
)

HEADING_CLOSE: Final[tuple[str, ...]] = (
    "",  # Index 0 unused
    "</h1>",
    "</h2>",
    "</h3>",
    "</h4>",
    "</h5>",
    "</h6>",
)


class FST:
    """
    Finite State Transducer for Markdown parsing.
    
    Implements a Mealy Machine where output is produced during transitions.
    Processes input character-by-character in O(N) time.
    
    Architecture:
    - Block-level FST handles paragraphs, headings, lists
    - Inline FST handles bold, italic within blocks
    - Both operate in a single pass with no backtracking
    
    Example:
        >>> fst = FST(mode=OutputMode.SAFE)
        >>> result = fst.process("**bold** and *italic*")
        >>> print(result)
        <p><strong>bold</strong> and <em>italic</em></p>
    """
    
    __slots__ = ("_mode", "_escape_fn")
    
    def __init__(self, mode: OutputMode = OutputMode.SAFE) -> None:
        """
        Initialize the FST.
        
        Args:
            mode: Output mode (SAFE escapes HTML, RAW passes through)
        """
        self._mode = mode
        self._escape_fn = escape_html if mode == OutputMode.SAFE else lambda x: x
    
    def _create_context(self) -> FSTContext:
        """Create a fresh parsing context."""
        return FSTContext(
            output=[],
            inline_state=State.TEXT,
            block_state=BlockState.START,
            pending_stars=0,
            heading_level=0,
            in_list=False,
            in_paragraph=False,
            inline_buffer=[],
            position=0,
            line=1,
            column=1,
            blockquote_depth=0,
            in_code_block=False,
            code_block_buffer=[],
            pending_backticks=0,
        )
    
    def process(self, text: str) -> str:
        """
        Process Markdown text and return HTML.
        
        This is the main entry point for parsing.
        Processes the entire input in a single pass.
        
        Args:
            text: Markdown input text
            
        Returns:
            HTML output string
        """
        if not text:
            return ""
        
        # Validate input
        if not HTMLEscaper.validate_input(text):
            return ""
        
        ctx = self._create_context()
        
        # Process character by character
        i = 0
        n = len(text)
        
        while i < n:
            char = text[i]
            
            # Update position tracking
            ctx.position = i
            if char == CHAR_NEWLINE:
                ctx.line += 1
                ctx.column = 1
            else:
                ctx.column += 1
            
            # Process based on block state
            self._process_char(ctx, char, text, i, n)
            i += 1
        
        # Finalize output
        self._finalize(ctx)
        
        return "".join(ctx.output)
    
    def _process_char(
        self, 
        ctx: FSTContext, 
        char: str, 
        text: str, 
        pos: int, 
        length: int
    ) -> None:
        """
        Process a single character through the FST.
        
        This is the core state machine logic.
        """
        match ctx.block_state:
            case BlockState.START | BlockState.LINE_START:
                self._process_line_start(ctx, char, text, pos, length)
            
            case BlockState.HEADING_HASHES:
                self._process_heading_hashes(ctx, char)
            
            case BlockState.HEADING_SPACE:
                self._process_heading_space(ctx, char)
            
            case BlockState.HEADING_CONTENT:
                self._process_heading_content(ctx, char)
            
            case BlockState.LIST_MARKER:
                self._process_list_marker(ctx, char)
            
            case BlockState.LIST_SPACE:
                self._process_list_space(ctx, char)
            
            case BlockState.LIST_CONTENT:
                self._process_list_content(ctx, char)
            
            case BlockState.PARAGRAPH:
                self._process_paragraph(ctx, char)
            
            case BlockState.BLANK_LINE:
                self._process_blank_line(ctx, char, text, pos, length)
            
            case BlockState.CODE_BLOCK_TICK_ONE:
                self._process_code_block_tick_one(ctx, char)
            
            case BlockState.CODE_BLOCK_TICK_TWO:
                self._process_code_block_tick_two(ctx, char)
            
            case BlockState.CODE_BLOCK_CONTENT:
                self._process_code_block_content(ctx, char)
            
            case BlockState.CODE_BLOCK_CLOSE_ONE:
                self._process_code_block_close_one(ctx, char)
            
            case BlockState.CODE_BLOCK_CLOSE_TWO:
                self._process_code_block_close_two(ctx, char)
            
            case BlockState.BLOCKQUOTE_START:
                self._process_blockquote_start(ctx, char, text, pos, length)
            
            case BlockState.BLOCKQUOTE_CONTENT:
                self._process_blockquote_content(ctx, char, text, pos, length)
            
            case _:
                # Default: treat as paragraph content
                self._process_paragraph(ctx, char)
    
    def _process_line_start(
        self, 
        ctx: FSTContext, 
        char: str, 
        text: str,
        pos: int,
        length: int
    ) -> None:
        """Process character at the start of a line."""
        match char:
            case "#":
                ctx.block_state = BlockState.HEADING_HASHES
                ctx.heading_level = 1
            
            case "-":
                # Check if followed by space (list item)
                if pos + 1 < length and text[pos + 1] == CHAR_SPACE:
                    ctx.block_state = BlockState.LIST_MARKER
                else:
                    # Not a list, start paragraph
                    self._start_paragraph(ctx)
                    self._process_inline_char(ctx, char)
            
            case "`":
                # Potential code block start
                ctx.block_state = BlockState.CODE_BLOCK_TICK_ONE
                ctx.pending_backticks = 1
            
            case ">":
                # Blockquote start
                self._start_blockquote(ctx)
                ctx.block_state = BlockState.BLOCKQUOTE_START
            
            case "\n":
                # Blank line
                ctx.block_state = BlockState.BLANK_LINE
                self._close_current_block(ctx)
            
            case " " | "\t":
                # Skip leading whitespace at line start
                pass
            
            case _:
                # Regular content - start or continue paragraph
                self._start_paragraph(ctx)
                self._process_inline_char(ctx, char)
    
    def _process_heading_hashes(self, ctx: FSTContext, char: str) -> None:
        """Process characters while counting heading hashes."""
        match char:
            case "#":
                ctx.heading_level += 1
                if ctx.heading_level > MAX_HEADING_LEVEL:
                    # Too many hashes - treat as paragraph
                    self._start_paragraph(ctx)
                    ctx.inline_buffer.extend(["#"] * ctx.heading_level)
                    ctx.heading_level = 0
                    ctx.block_state = BlockState.PARAGRAPH
            
            case " ":
                # Space after hashes - valid heading
                ctx.block_state = BlockState.HEADING_SPACE
            
            case "\n":
                # Empty heading
                level = min(ctx.heading_level, MAX_HEADING_LEVEL)
                ctx.output.append(HEADING_OPEN[level])
                ctx.output.append(HEADING_CLOSE[level])
                ctx.output.append(HTML_NEWLINE)
                ctx.heading_level = 0
                ctx.block_state = BlockState.LINE_START
            
            case _:
                # No space after hash - treat as paragraph
                self._start_paragraph(ctx)
                ctx.inline_buffer.extend(["#"] * ctx.heading_level)
                ctx.heading_level = 0
                self._process_inline_char(ctx, char)
                ctx.block_state = BlockState.PARAGRAPH
    
    def _process_heading_space(self, ctx: FSTContext, char: str) -> None:
        """Process the space after heading hashes."""
        # Start heading content
        level = min(ctx.heading_level, MAX_HEADING_LEVEL)
        ctx.output.append(HEADING_OPEN[level])
        ctx.block_state = BlockState.HEADING_CONTENT
        
        if char != CHAR_SPACE:
            self._process_inline_char(ctx, char)
    
    def _process_heading_content(self, ctx: FSTContext, char: str) -> None:
        """Process heading content."""
        match char:
            case "\n":
                # End of heading
                self._flush_inline(ctx)
                level = min(ctx.heading_level, MAX_HEADING_LEVEL)
                ctx.output.append(HEADING_CLOSE[level])
                ctx.output.append(HTML_NEWLINE)
                ctx.heading_level = 0
                ctx.block_state = BlockState.LINE_START
                ctx.inline_state = State.TEXT
            
            case _:
                self._process_inline_char(ctx, char)
    
    def _process_list_marker(self, ctx: FSTContext, char: str) -> None:
        """Process list marker (-)."""
        # We already checked for space, so transition to list space
        ctx.block_state = BlockState.LIST_SPACE
    
    def _process_list_space(self, ctx: FSTContext, char: str) -> None:
        """Process space after list marker."""
        if not ctx.in_list:
            ctx.output.append(HTML_UL_OPEN)
            ctx.output.append(HTML_NEWLINE)
            ctx.in_list = True
        
        ctx.output.append(HTML_LI_OPEN)
        ctx.block_state = BlockState.LIST_CONTENT
        
        if char != CHAR_SPACE:
            self._process_inline_char(ctx, char)
    
    def _process_list_content(self, ctx: FSTContext, char: str) -> None:
        """Process list item content."""
        match char:
            case "\n":
                # End of list item
                self._flush_inline(ctx)
                ctx.output.append(HTML_LI_CLOSE)
                ctx.output.append(HTML_NEWLINE)
                ctx.block_state = BlockState.LINE_START
                ctx.inline_state = State.TEXT
            
            case _:
                self._process_inline_char(ctx, char)
    
    def _process_paragraph(self, ctx: FSTContext, char: str) -> None:
        """Process paragraph content."""
        match char:
            case "\n":
                # Check for paragraph break (blank line coming)
                ctx.block_state = BlockState.BLANK_LINE
            
            case _:
                self._process_inline_char(ctx, char)
    
    def _process_blank_line(
        self, 
        ctx: FSTContext, 
        char: str,
        text: str,
        pos: int,
        length: int
    ) -> None:
        """Process potential blank line."""
        match char:
            case "\n":
                # Confirmed blank line - close paragraph and blockquotes
                self._close_current_block(ctx)
                self._close_all_blockquotes(ctx)
                ctx.block_state = BlockState.LINE_START
            
            case " " | "\t":
                # Still might be blank line
                pass
            
            case ">":
                # Blockquote continuation
                if ctx.in_paragraph:
                    # Close current paragraph first
                    self._flush_inline(ctx)
                    ctx.output.append(HTML_P_CLOSE)
                    ctx.output.append(HTML_NEWLINE)
                    ctx.in_paragraph = False
                if ctx.blockquote_depth == 0:
                    # Start new blockquote
                    self._start_blockquote(ctx)
                ctx.block_state = BlockState.BLOCKQUOTE_START
            
            case _:
                # Not a blank line - this is continuation
                if ctx.in_paragraph:
                    # Add space for soft line break
                    ctx.inline_buffer.append(" ")
                ctx.block_state = BlockState.PARAGRAPH
                self._process_line_start(ctx, char, text, pos, length)
    
    def _start_paragraph(self, ctx: FSTContext) -> None:
        """Start a new paragraph if not already in one."""
        if not ctx.in_paragraph:
            self._close_list(ctx)
            ctx.output.append(HTML_P_OPEN)
            ctx.in_paragraph = True
            ctx.block_state = BlockState.PARAGRAPH
    
    def _close_current_block(self, ctx: FSTContext) -> None:
        """Close the current block element."""
        self._flush_inline(ctx)
        
        if ctx.in_paragraph:
            ctx.output.append(HTML_P_CLOSE)
            ctx.output.append(HTML_NEWLINE)
            ctx.in_paragraph = False
        
        self._close_list(ctx)
        ctx.inline_state = State.TEXT
    
    def _close_list(self, ctx: FSTContext) -> None:
        """Close an open list."""
        if ctx.in_list:
            ctx.output.append(HTML_UL_CLOSE)
            ctx.output.append(HTML_NEWLINE)
            ctx.in_list = False
    
    def _process_inline_char(self, ctx: FSTContext, char: str) -> None:
        """
        Process a character through the inline FST.
        
        Handles bold (**), italic (*), and inline code (`) formatting.
        Uses lookahead state for * vs ** disambiguation.
        """
        match ctx.inline_state:
            case State.TEXT:
                self._inline_text(ctx, char)
            
            case State.STAR_ONE:
                self._inline_star_one(ctx, char)
            
            case State.STAR_TWO:
                self._inline_star_two(ctx, char)
            
            case State.IN_ITALIC:
                self._inline_in_italic(ctx, char)
            
            case State.ITALIC_STAR:
                self._inline_italic_star(ctx, char)
            
            case State.IN_BOLD:
                self._inline_in_bold(ctx, char)
            
            case State.BOLD_STAR_ONE:
                self._inline_bold_star_one(ctx, char)
            
            case State.BOLD_STAR_TWO:
                self._inline_bold_star_two(ctx, char)
            
            case State.IN_BOLD_ITALIC:
                self._inline_in_bold_italic(ctx, char)
            
            case State.BOLD_ITALIC_STAR_ONE:
                self._inline_bold_italic_star_one(ctx, char)
            
            case State.BOLD_ITALIC_STAR_TWO:
                self._inline_bold_italic_star_two(ctx, char)
            
            case State.BOLD_ITALIC_STAR_THREE:
                self._inline_bold_italic_star_three(ctx, char)
            
            case State.IN_CODE:
                self._inline_in_code(ctx, char)
            
            case _:
                # Default: output character
                ctx.inline_buffer.append(self._escape_fn(char))
    
    def _inline_text(self, ctx: FSTContext, char: str) -> None:
        """Process character in TEXT state."""
        if char == CHAR_STAR:
            ctx.inline_state = State.STAR_ONE
            ctx.pending_stars = 1
        elif char == CHAR_BACKTICK:
            # Start inline code
            ctx.inline_buffer.append(HTML_CODE_OPEN)
            ctx.inline_state = State.IN_CODE
        else:
            ctx.inline_buffer.append(self._escape_fn(char))
    
    def _inline_star_one(self, ctx: FSTContext, char: str) -> None:
        """Process character in STAR_ONE state (seen one *)."""
        if char == CHAR_STAR:
            ctx.inline_state = State.STAR_TWO
            ctx.pending_stars = 2
        else:
            # Single * means start italic
            ctx.inline_buffer.append(HTML_EM_OPEN)
            ctx.inline_state = State.IN_ITALIC
            ctx.pending_stars = 0
            ctx.inline_buffer.append(self._escape_fn(char))
    
    def _inline_star_two(self, ctx: FSTContext, char: str) -> None:
        """Process character in STAR_TWO state (seen **)."""
        if char == CHAR_STAR:
            # *** = bold + italic
            ctx.inline_buffer.append(HTML_STRONG_OPEN)
            ctx.inline_buffer.append(HTML_EM_OPEN)
            ctx.inline_state = State.IN_BOLD_ITALIC
            ctx.pending_stars = 0
        else:
            # ** means start bold
            ctx.inline_buffer.append(HTML_STRONG_OPEN)
            ctx.inline_state = State.IN_BOLD
            ctx.pending_stars = 0
            ctx.inline_buffer.append(self._escape_fn(char))
    
    def _inline_in_italic(self, ctx: FSTContext, char: str) -> None:
        """Process character while in italic."""
        if char == CHAR_STAR:
            ctx.inline_state = State.ITALIC_STAR
        else:
            ctx.inline_buffer.append(self._escape_fn(char))
    
    def _inline_italic_star(self, ctx: FSTContext, char: str) -> None:
        """Process character after * in italic."""
        if char == CHAR_STAR:
            # ** in italic = close italic, start bold
            ctx.inline_buffer.append(HTML_EM_CLOSE)
            ctx.inline_buffer.append(HTML_STRONG_OPEN)
            ctx.inline_state = State.IN_BOLD
        else:
            # Single * closes italic
            ctx.inline_buffer.append(HTML_EM_CLOSE)
            ctx.inline_state = State.TEXT
            ctx.inline_buffer.append(self._escape_fn(char))
    
    def _inline_in_bold(self, ctx: FSTContext, char: str) -> None:
        """Process character while in bold."""
        if char == CHAR_STAR:
            ctx.inline_state = State.BOLD_STAR_ONE
        else:
            ctx.inline_buffer.append(self._escape_fn(char))
    
    def _inline_bold_star_one(self, ctx: FSTContext, char: str) -> None:
        """Process character after first * in bold."""
        if char == CHAR_STAR:
            # ** closes bold
            ctx.inline_buffer.append(HTML_STRONG_CLOSE)
            ctx.inline_state = State.TEXT
        else:
            # Single * in bold = start nested italic (not standard, treat as literal)
            ctx.inline_buffer.append(CHAR_STAR)
            ctx.inline_buffer.append(self._escape_fn(char))
            ctx.inline_state = State.IN_BOLD
    
    def _inline_bold_star_two(self, ctx: FSTContext, char: str) -> None:
        """Process character after ** in bold (already transitioned)."""
        ctx.inline_buffer.append(self._escape_fn(char))
        ctx.inline_state = State.TEXT
    
    def _inline_in_bold_italic(self, ctx: FSTContext, char: str) -> None:
        """Process character while in bold+italic."""
        if char == CHAR_STAR:
            ctx.inline_state = State.BOLD_ITALIC_STAR_ONE
        else:
            ctx.inline_buffer.append(self._escape_fn(char))
    
    def _inline_bold_italic_star_one(self, ctx: FSTContext, char: str) -> None:
        """Process after first * in bold+italic."""
        if char == CHAR_STAR:
            ctx.inline_state = State.BOLD_ITALIC_STAR_TWO
        else:
            # Single * closes italic only
            ctx.inline_buffer.append(HTML_EM_CLOSE)
            ctx.inline_state = State.IN_BOLD
            ctx.inline_buffer.append(self._escape_fn(char))
    
    def _inline_bold_italic_star_two(self, ctx: FSTContext, char: str) -> None:
        """Process after ** in bold+italic."""
        if char == CHAR_STAR:
            # *** closes both
            ctx.inline_buffer.append(HTML_EM_CLOSE)
            ctx.inline_buffer.append(HTML_STRONG_CLOSE)
            ctx.inline_state = State.TEXT
        else:
            # ** closes bold only
            ctx.inline_buffer.append(HTML_STRONG_CLOSE)
            ctx.inline_state = State.IN_ITALIC
            ctx.inline_buffer.append(self._escape_fn(char))
    
    def _inline_bold_italic_star_three(self, ctx: FSTContext, char: str) -> None:
        """Process after *** in bold+italic."""
        ctx.inline_buffer.append(self._escape_fn(char))
        ctx.inline_state = State.TEXT
    
    def _inline_in_code(self, ctx: FSTContext, char: str) -> None:
        """Process character while in inline code."""
        if char == CHAR_BACKTICK:
            # Close inline code
            ctx.inline_buffer.append(HTML_CODE_CLOSE)
            ctx.inline_state = State.TEXT
        else:
            # In code, we still escape for XSS safety but no Markdown formatting
            ctx.inline_buffer.append(self._escape_fn(char))
    
    # =========================================================================
    # Code Block Methods (```)
    # =========================================================================
    
    def _process_code_block_tick_one(self, ctx: FSTContext, char: str) -> None:
        """Process after seeing first ` at line start."""
        if char == CHAR_BACKTICK:
            ctx.pending_backticks = 2
            ctx.block_state = BlockState.CODE_BLOCK_TICK_TWO
        else:
            # Not a code block, just a single backtick at line start - start paragraph
            self._start_paragraph(ctx)
            ctx.inline_buffer.append(HTML_CODE_OPEN)
            ctx.inline_state = State.IN_CODE
            ctx.inline_buffer.append(self._escape_fn(char))
            ctx.block_state = BlockState.PARAGRAPH
            ctx.pending_backticks = 0
    
    def _process_code_block_tick_two(self, ctx: FSTContext, char: str) -> None:
        """Process after seeing `` at line start."""
        if char == CHAR_BACKTICK:
            # We have ```, start code block
            self._close_current_block(ctx)
            ctx.in_code_block = True
            ctx.output.append(HTML_PRE_OPEN)
            ctx.output.append(HTML_CODE_OPEN)
            ctx.block_state = BlockState.CODE_BLOCK_CONTENT
            ctx.pending_backticks = 0
        elif char == CHAR_NEWLINE:
            # `` followed by newline - treat as literal text
            self._start_paragraph(ctx)
            ctx.inline_buffer.append(CHAR_BACKTICK)
            ctx.inline_buffer.append(CHAR_BACKTICK)
            ctx.block_state = BlockState.LINE_START
            ctx.pending_backticks = 0
        else:
            # `` followed by other char - treat as literal text
            self._start_paragraph(ctx)
            ctx.inline_buffer.append(CHAR_BACKTICK)
            ctx.inline_buffer.append(CHAR_BACKTICK)
            ctx.inline_buffer.append(self._escape_fn(char))
            ctx.block_state = BlockState.PARAGRAPH
            ctx.pending_backticks = 0
    
    def _process_code_block_content(self, ctx: FSTContext, char: str) -> None:
        """Process content inside a code block."""
        if char == CHAR_BACKTICK:
            ctx.block_state = BlockState.CODE_BLOCK_CLOSE_ONE
        elif char == CHAR_NEWLINE:
            ctx.code_block_buffer.append(char)
        else:
            # Escape for XSS but preserve content otherwise
            ctx.code_block_buffer.append(self._escape_fn(char))
    
    def _process_code_block_close_one(self, ctx: FSTContext, char: str) -> None:
        """Process after seeing first ` in code block (potential close)."""
        if char == CHAR_BACKTICK:
            ctx.block_state = BlockState.CODE_BLOCK_CLOSE_TWO
        else:
            # Single backtick in code - just content
            ctx.code_block_buffer.append(CHAR_BACKTICK)
            ctx.code_block_buffer.append(self._escape_fn(char))
            ctx.block_state = BlockState.CODE_BLOCK_CONTENT
    
    def _process_code_block_close_two(self, ctx: FSTContext, char: str) -> None:
        """Process after seeing `` in code block (potential close)."""
        if char == CHAR_BACKTICK:
            # ``` closes the code block
            self._close_code_block(ctx)
            ctx.block_state = BlockState.LINE_START
        elif char == CHAR_NEWLINE:
            # `` followed by newline - not close, just content
            ctx.code_block_buffer.append(CHAR_BACKTICK)
            ctx.code_block_buffer.append(CHAR_BACKTICK)
            ctx.code_block_buffer.append(char)
            ctx.block_state = BlockState.CODE_BLOCK_CONTENT
        else:
            # `` followed by other char - just content
            ctx.code_block_buffer.append(CHAR_BACKTICK)
            ctx.code_block_buffer.append(CHAR_BACKTICK)
            ctx.code_block_buffer.append(self._escape_fn(char))
            ctx.block_state = BlockState.CODE_BLOCK_CONTENT
    
    def _close_code_block(self, ctx: FSTContext) -> None:
        """Close the current code block."""
        if ctx.code_block_buffer:
            content = "".join(ctx.code_block_buffer)
            # Strip leading newline if present
            if content.startswith("\n"):
                content = content[1:]
            # Strip trailing newline if present
            if content.endswith("\n"):
                content = content[:-1]
            ctx.output.append(content)
            ctx.code_block_buffer.clear()
        ctx.output.append(HTML_CODE_CLOSE)
        ctx.output.append(HTML_PRE_CLOSE)
        ctx.output.append(HTML_NEWLINE)
        ctx.in_code_block = False
    
    # =========================================================================
    # Blockquote Methods (>)
    # =========================================================================
    
    def _start_blockquote(self, ctx: FSTContext) -> None:
        """Start a new blockquote or add nesting level."""
        self._close_current_block(ctx)
        ctx.blockquote_depth += 1
        ctx.output.append(HTML_BLOCKQUOTE_OPEN)
    
    def _process_blockquote_start(
        self,
        ctx: FSTContext,
        char: str,
        text: str,
        pos: int,
        length: int
    ) -> None:
        """Process character after seeing > at line start."""
        if char == CHAR_SPACE:
            # > followed by space - start blockquote content
            ctx.block_state = BlockState.BLOCKQUOTE_CONTENT
        elif char == CHAR_GT:
            # Nested blockquote
            ctx.blockquote_depth += 1
            ctx.output.append(HTML_BLOCKQUOTE_OPEN)
            # Stay in BLOCKQUOTE_START to check for more nesting
        elif char == CHAR_NEWLINE:
            # Empty blockquote line
            ctx.block_state = BlockState.LINE_START
        else:
            # > followed by content directly (no space)
            ctx.block_state = BlockState.BLOCKQUOTE_CONTENT
            self._start_paragraph(ctx)
            self._process_inline_char(ctx, char)
    
    def _process_blockquote_content(
        self,
        ctx: FSTContext,
        char: str,
        text: str,
        pos: int,
        length: int
    ) -> None:
        """Process content inside a blockquote."""
        if char == CHAR_NEWLINE:
            # End of line in blockquote
            self._flush_inline(ctx)
            if ctx.in_paragraph:
                ctx.output.append(HTML_P_CLOSE)
                ctx.output.append(HTML_NEWLINE)
                ctx.in_paragraph = False
            ctx.block_state = BlockState.BLANK_LINE
        else:
            # Start paragraph if not started
            if not ctx.in_paragraph:
                ctx.output.append(HTML_P_OPEN)
                ctx.in_paragraph = True
            self._process_inline_char(ctx, char)
    
    def _close_all_blockquotes(self, ctx: FSTContext) -> None:
        """Close all open blockquotes."""
        while ctx.blockquote_depth > 0:
            ctx.output.append(HTML_BLOCKQUOTE_CLOSE)
            ctx.output.append(HTML_NEWLINE)
            ctx.blockquote_depth -= 1
    
    def _flush_inline(self, ctx: FSTContext) -> None:
        """Flush the inline buffer to output, closing any open tags."""
        # Handle any pending stars
        if ctx.pending_stars > 0:
            ctx.inline_buffer.append(CHAR_STAR * ctx.pending_stars)
            ctx.pending_stars = 0
        
        # Close any open inline formatting
        match ctx.inline_state:
            case State.IN_ITALIC | State.ITALIC_STAR:
                ctx.inline_buffer.append(HTML_EM_CLOSE)
            
            case State.IN_BOLD | State.BOLD_STAR_ONE:
                ctx.inline_buffer.append(HTML_STRONG_CLOSE)
            
            case State.IN_BOLD_ITALIC | State.BOLD_ITALIC_STAR_ONE | State.BOLD_ITALIC_STAR_TWO:
                ctx.inline_buffer.append(HTML_EM_CLOSE)
                ctx.inline_buffer.append(HTML_STRONG_CLOSE)
            
            case State.STAR_ONE:
                ctx.inline_buffer.append(CHAR_STAR)
            
            case State.STAR_TWO:
                ctx.inline_buffer.append(CHAR_STAR * 2)
            
            case State.IN_CODE:
                # Close unclosed inline code
                ctx.inline_buffer.append(HTML_CODE_CLOSE)
        
        # Output the buffer
        if ctx.inline_buffer:
            ctx.output.append("".join(ctx.inline_buffer))
            ctx.inline_buffer.clear()
        
        ctx.inline_state = State.TEXT
    
    def _finalize(self, ctx: FSTContext) -> None:
        """Finalize output after processing all input."""
        # Handle code block that was never closed
        if ctx.in_code_block:
            self._close_code_block(ctx)
        
        # Handle pending code block start (incomplete ```)
        if ctx.block_state == BlockState.CODE_BLOCK_TICK_ONE:
            # Single backtick at line start, output as text
            self._start_paragraph(ctx)
            ctx.inline_buffer.append(CHAR_BACKTICK)
        elif ctx.block_state == BlockState.CODE_BLOCK_TICK_TWO:
            # Double backtick at line start, output as text
            self._start_paragraph(ctx)
            ctx.inline_buffer.append(CHAR_BACKTICK * 2)
        elif ctx.block_state == BlockState.CODE_BLOCK_CLOSE_ONE:
            # Single backtick at potential close
            ctx.code_block_buffer.append(CHAR_BACKTICK)
            self._close_code_block(ctx)
        elif ctx.block_state == BlockState.CODE_BLOCK_CLOSE_TWO:
            # Double backtick at potential close
            ctx.code_block_buffer.append(CHAR_BACKTICK * 2)
            self._close_code_block(ctx)
        
        # Flush any remaining inline content
        self._flush_inline(ctx)
        
        # Close any open blocks
        if ctx.in_paragraph:
            ctx.output.append(HTML_P_CLOSE)
            ctx.in_paragraph = False
        
        # Close any open heading
        if ctx.block_state == BlockState.HEADING_CONTENT and ctx.heading_level > 0:
            level = min(ctx.heading_level, MAX_HEADING_LEVEL)
            ctx.output.append(HEADING_CLOSE[level])
            ctx.heading_level = 0
        elif ctx.heading_level > 0:
            # Heading started but content not yet begun
            level = min(ctx.heading_level, MAX_HEADING_LEVEL)
            ctx.output.append(HEADING_OPEN[level])
            ctx.output.append(HEADING_CLOSE[level])
            ctx.heading_level = 0
        
        # Close any open list item (if we ended mid-list)
        if ctx.block_state == BlockState.LIST_CONTENT:
            ctx.output.append(HTML_LI_CLOSE)
            ctx.output.append(HTML_NEWLINE)
        
        self._close_list(ctx)
        
        # Close any open blockquotes
        self._close_all_blockquotes(ctx)
