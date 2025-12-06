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
    CHAR_LBRACKET,
    CHAR_RBRACKET,
    CHAR_LPAREN,
    CHAR_RPAREN,
    CHAR_BANG,
    CHAR_PIPE,
    CHAR_COLON,
    CHAR_DOT,
    MAX_HEADING_LEVEL,
)
from fstmd.core.safe_html import HTMLEscaper, escape_html, sanitize_url, is_safe_url


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
    
    # Link/Image parsing buffers (shared via helper logic)
    link_text_buffer: list[str]    # Buffer for [text] portion
    link_url_buffer: list[str]     # Buffer for (url) portion
    link_text_state: State         # Inline state within link text (for nested formatting)
    link_text_formatting: list[str]  # Stack of open formatting in link text
    
    # Nested list state - stack of (list_type, indent_level)
    # list_type: "ul" for unordered, "ol" for ordered
    list_stack: list[tuple[str, int]]
    
    # Current indentation level being parsed
    current_indent: int
    
    # Pending list marker character (-, *, or digit)
    pending_list_marker: str
    
    # Pending number for ordered lists
    pending_list_number: str
    
    # Table state
    in_table: bool
    table_header_row: list[str]          # Raw header cells
    table_alignments: list[str]          # "left", "center", "right", or ""
    table_row_buffer: list[str]          # Current row cells
    table_cell_buffer: list[str]         # Current cell content
    table_has_body: bool                 # Whether we've seen body rows


# HTML output constants
HTML_P_OPEN: Final[str] = "<p>"
HTML_P_CLOSE: Final[str] = "</p>"
HTML_UL_OPEN: Final[str] = "<ul>"
HTML_UL_CLOSE: Final[str] = "</ul>"
HTML_OL_OPEN: Final[str] = "<ol>"
HTML_OL_CLOSE: Final[str] = "</ol>"
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
HTML_A_OPEN_START: Final[str] = '<a href="'
HTML_A_OPEN_END: Final[str] = '">'
HTML_A_CLOSE: Final[str] = "</a>"
HTML_IMG_START: Final[str] = '<img src="'
HTML_IMG_ALT: Final[str] = '" alt="'
HTML_IMG_END: Final[str] = '"/>'

# Table HTML constants
HTML_TABLE_OPEN: Final[str] = "<table>"
HTML_TABLE_CLOSE: Final[str] = "</table>"
HTML_THEAD_OPEN: Final[str] = "<thead>"
HTML_THEAD_CLOSE: Final[str] = "</thead>"
HTML_TBODY_OPEN: Final[str] = "<tbody>"
HTML_TBODY_CLOSE: Final[str] = "</tbody>"
HTML_TR_OPEN: Final[str] = "<tr>"
HTML_TR_CLOSE: Final[str] = "</tr>"
HTML_TH_OPEN: Final[str] = "<th>"
HTML_TH_CLOSE: Final[str] = "</th>"
HTML_TD_OPEN: Final[str] = "<td>"
HTML_TD_CLOSE: Final[str] = "</td>"
HTML_TH_ALIGN_LEFT: Final[str] = '<th style="text-align:left">'
HTML_TH_ALIGN_CENTER: Final[str] = '<th style="text-align:center">'
HTML_TH_ALIGN_RIGHT: Final[str] = '<th style="text-align:right">'
HTML_TD_ALIGN_LEFT: Final[str] = '<td style="text-align:left">'
HTML_TD_ALIGN_CENTER: Final[str] = '<td style="text-align:center">'
HTML_TD_ALIGN_RIGHT: Final[str] = '<td style="text-align:right">'

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
            link_text_buffer=[],
            link_url_buffer=[],
            link_text_state=State.TEXT,
            link_text_formatting=[],
            # Nested list state
            list_stack=[],
            current_indent=0,
            pending_list_marker="",
            pending_list_number="",
            # Table state
            in_table=False,
            table_header_row=[],
            table_alignments=[],
            table_row_buffer=[],
            table_cell_buffer=[],
            table_has_body=False,
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
            
            # Nested list states
            case BlockState.NESTED_LIST_INDENT:
                self._process_nested_list_indent(ctx, char, text, pos, length)
            
            case BlockState.NESTED_LIST_MARKER:
                self._process_nested_list_marker(ctx, char, text, pos, length)
            
            case BlockState.NESTED_LIST_NUMBER:
                self._process_nested_list_number(ctx, char, text, pos, length)
            
            case BlockState.NESTED_LIST_CONTENT:
                self._process_nested_list_content(ctx, char, text, pos, length)
            
            # Table states
            case BlockState.TABLE_ROW:
                self._process_table_row(ctx, char, text, pos, length)
            
            case BlockState.TABLE_SEPARATOR:
                self._process_table_separator(ctx, char, text, pos, length)
            
            case BlockState.TABLE_CELL:
                self._process_table_cell(ctx, char, text, pos, length)
            
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
            
            case "-" | "*":
                # Check if followed by space (list item) or if it's a table separator
                if pos + 1 < length and text[pos + 1] == CHAR_SPACE:
                    # Unordered list item at indent 0
                    ctx.current_indent = 0
                    ctx.pending_list_marker = char
                    ctx.block_state = BlockState.NESTED_LIST_MARKER
                elif char == "-" and self._is_table_separator_line(text, pos, length):
                    # This might be a table separator - but only if we're in a table context
                    # At line start, this would be invalid, so treat as paragraph
                    self._start_paragraph(ctx)
                    self._process_inline_char(ctx, char)
                else:
                    # Not a list, start paragraph
                    self._start_paragraph(ctx)
                    self._process_inline_char(ctx, char)
            
            case "|":
                # Potential table row
                self._start_table_row(ctx, text, pos, length)
            
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
                # Indentation - could be nested list or continuation
                if ctx.list_stack:
                    # We're in a list context - check for nested list
                    ctx.current_indent = 1 if char == CHAR_SPACE else 4
                    ctx.block_state = BlockState.NESTED_LIST_INDENT
                else:
                    # Skip leading whitespace at line start (not in list)
                    pass
            
            case _ if char.isdigit():
                # Potential ordered list (1. 2. etc.)
                ctx.current_indent = 0
                ctx.pending_list_number = char
                ctx.block_state = BlockState.NESTED_LIST_NUMBER
            
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
                # But first, flush any partial link/image state
                self._flush_inline(ctx)
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
            self._close_all_nested_lists(ctx)
            self._close_table(ctx)
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
        self._close_all_nested_lists(ctx)
        self._close_table(ctx)
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
        
        Handles bold (**), italic (*), inline code (`), links [text](url),
        and images ![alt](url) formatting.
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
            
            # Link states
            case State.LINK_OPEN:
                self._inline_link_open(ctx, char)
            
            case State.LINK_TEXT:
                self._inline_link_text(ctx, char)
            
            case State.LINK_TEXT_STAR_ONE:
                self._inline_link_text_star_one(ctx, char)
            
            case State.LINK_TEXT_STAR_TWO:
                self._inline_link_text_star_two(ctx, char)
            
            case State.LINK_TEXT_ITALIC:
                self._inline_link_text_italic(ctx, char)
            
            case State.LINK_TEXT_BOLD:
                self._inline_link_text_bold(ctx, char)
            
            case State.LINK_TEXT_CLOSE:
                self._inline_link_text_close(ctx, char)
            
            case State.LINK_URL_OPEN:
                self._inline_link_url_open(ctx, char)
            
            case State.LINK_URL:
                self._inline_link_url(ctx, char)
            
            # Image states
            case State.IMAGE_BANG:
                self._inline_image_bang(ctx, char)
            
            case State.IMAGE_OPEN:
                self._inline_image_open(ctx, char)
            
            case State.IMAGE_ALT:
                self._inline_image_alt(ctx, char)
            
            case State.IMAGE_ALT_CLOSE:
                self._inline_image_alt_close(ctx, char)
            
            case State.IMAGE_URL_OPEN:
                self._inline_image_url_open(ctx, char)
            
            case State.IMAGE_URL:
                self._inline_image_url(ctx, char)
            
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
        elif char == CHAR_LBRACKET:
            # Potential link start [
            ctx.inline_state = State.LINK_OPEN
            ctx.link_text_buffer.clear()
            ctx.link_url_buffer.clear()
            ctx.link_text_formatting.clear()
        elif char == CHAR_BANG:
            # Potential image start !
            ctx.inline_state = State.IMAGE_BANG
            ctx.link_text_buffer.clear()
            ctx.link_url_buffer.clear()
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
    # Link Methods [text](url) - DRY: shares URL helper with images
    # =========================================================================
    
    def _inline_link_open(self, ctx: FSTContext, char: str) -> None:
        """Process character after seeing [ (potential link start)."""
        if char == CHAR_RBRACKET:
            # Empty link text [] - not a valid link, output literally
            ctx.inline_buffer.append(CHAR_LBRACKET)
            ctx.inline_buffer.append(CHAR_RBRACKET)
            ctx.inline_state = State.TEXT
        elif char == CHAR_NEWLINE:
            # Newline breaks link - output [ and the newline
            ctx.inline_buffer.append(CHAR_LBRACKET)
            ctx.inline_state = State.TEXT
            # Don't append newline here, let block handle it
        else:
            # Start collecting link text
            ctx.inline_state = State.LINK_TEXT
            ctx.link_text_buffer.clear()
            ctx.link_text_formatting.clear()
            if char == CHAR_STAR:
                # Potential formatting in link text
                ctx.inline_state = State.LINK_TEXT_STAR_ONE
            else:
                ctx.link_text_buffer.append(self._escape_fn(char))
    
    def _inline_link_text(self, ctx: FSTContext, char: str) -> None:
        """Process character while collecting link text."""
        if char == CHAR_RBRACKET:
            # End of link text - wait for (
            ctx.inline_state = State.LINK_TEXT_CLOSE
        elif char == CHAR_STAR:
            # Potential formatting
            ctx.inline_state = State.LINK_TEXT_STAR_ONE
        elif char == CHAR_NEWLINE:
            # Newline breaks link - output all accumulated text
            self._abort_link(ctx)
        elif char == CHAR_LBRACKET:
            # Nested [ - abort link, treat as literal
            self._abort_link(ctx)
            ctx.inline_buffer.append(CHAR_LBRACKET)
        else:
            ctx.link_text_buffer.append(self._escape_fn(char))
    
    def _inline_link_text_star_one(self, ctx: FSTContext, char: str) -> None:
        """Process after * in link text."""
        if char == CHAR_STAR:
            # ** - start bold
            ctx.link_text_buffer.append(HTML_STRONG_OPEN)
            ctx.link_text_formatting.append("strong")
            ctx.inline_state = State.LINK_TEXT_BOLD
        elif char == CHAR_RBRACKET:
            # * followed by ] - add * and close link text
            ctx.link_text_buffer.append(CHAR_STAR)
            ctx.inline_state = State.LINK_TEXT_CLOSE
        elif char == CHAR_NEWLINE:
            ctx.link_text_buffer.append(CHAR_STAR)
            self._abort_link(ctx)
        else:
            # Single * - start italic
            ctx.link_text_buffer.append(HTML_EM_OPEN)
            ctx.link_text_formatting.append("em")
            ctx.link_text_buffer.append(self._escape_fn(char))
            ctx.inline_state = State.LINK_TEXT_ITALIC
    
    def _inline_link_text_star_two(self, ctx: FSTContext, char: str) -> None:
        """Process after ** in link text (within bold)."""
        if char == CHAR_STAR:
            # *** - close bold
            ctx.link_text_buffer.append(HTML_STRONG_CLOSE)
            if ctx.link_text_formatting and ctx.link_text_formatting[-1] == "strong":
                ctx.link_text_formatting.pop()
            ctx.inline_state = State.LINK_TEXT
        elif char == CHAR_RBRACKET:
            # ** followed by ] - close bold and end link text
            ctx.link_text_buffer.append(HTML_STRONG_CLOSE)
            if ctx.link_text_formatting and ctx.link_text_formatting[-1] == "strong":
                ctx.link_text_formatting.pop()
            ctx.inline_state = State.LINK_TEXT_CLOSE
        elif char == CHAR_NEWLINE:
            self._abort_link(ctx)
        else:
            # ** closes bold
            ctx.link_text_buffer.append(HTML_STRONG_CLOSE)
            if ctx.link_text_formatting and ctx.link_text_formatting[-1] == "strong":
                ctx.link_text_formatting.pop()
            ctx.link_text_buffer.append(self._escape_fn(char))
            ctx.inline_state = State.LINK_TEXT
    
    def _inline_link_text_italic(self, ctx: FSTContext, char: str) -> None:
        """Process character while in italic within link text."""
        if char == CHAR_STAR:
            # * closes italic
            ctx.link_text_buffer.append(HTML_EM_CLOSE)
            if ctx.link_text_formatting and ctx.link_text_formatting[-1] == "em":
                ctx.link_text_formatting.pop()
            ctx.inline_state = State.LINK_TEXT
        elif char == CHAR_RBRACKET:
            # End link text (close italic first)
            ctx.link_text_buffer.append(HTML_EM_CLOSE)
            if ctx.link_text_formatting and ctx.link_text_formatting[-1] == "em":
                ctx.link_text_formatting.pop()
            ctx.inline_state = State.LINK_TEXT_CLOSE
        elif char == CHAR_NEWLINE:
            self._abort_link(ctx)
        else:
            ctx.link_text_buffer.append(self._escape_fn(char))
    
    def _inline_link_text_bold(self, ctx: FSTContext, char: str) -> None:
        """Process character while in bold within link text."""
        if char == CHAR_STAR:
            # Potential close
            ctx.inline_state = State.LINK_TEXT_STAR_TWO
        elif char == CHAR_RBRACKET:
            # End link text (close bold first)
            ctx.link_text_buffer.append(HTML_STRONG_CLOSE)
            if ctx.link_text_formatting and ctx.link_text_formatting[-1] == "strong":
                ctx.link_text_formatting.pop()
            ctx.inline_state = State.LINK_TEXT_CLOSE
        elif char == CHAR_NEWLINE:
            self._abort_link(ctx)
        else:
            ctx.link_text_buffer.append(self._escape_fn(char))
    
    def _inline_link_text_close(self, ctx: FSTContext, char: str) -> None:
        """Process character after ] (expecting ( for URL)."""
        if char == CHAR_LPAREN:
            # Valid link syntax [text](
            ctx.inline_state = State.LINK_URL_OPEN
            ctx.link_url_buffer.clear()
        else:
            # Not a link - output [text] literally (including the ])
            ctx.inline_buffer.append(CHAR_LBRACKET)
            # Close any open formatting
            for fmt in reversed(ctx.link_text_formatting):
                if fmt == "em":
                    ctx.link_text_buffer.append(HTML_EM_CLOSE)
                elif fmt == "strong":
                    ctx.link_text_buffer.append(HTML_STRONG_CLOSE)
            ctx.inline_buffer.extend(ctx.link_text_buffer)
            ctx.inline_buffer.append(CHAR_RBRACKET)  # Add the closing bracket
            ctx.link_text_buffer.clear()
            ctx.link_url_buffer.clear()
            ctx.link_text_formatting.clear()
            ctx.inline_state = State.TEXT
            # Process current char through normal text handling
            self._inline_text(ctx, char)
    
    def _inline_link_url_open(self, ctx: FSTContext, char: str) -> None:
        """Process first character of URL."""
        if char == CHAR_RPAREN:
            # Empty URL [text]() - still valid, creates link with empty href
            self._complete_link(ctx)
        elif char == CHAR_NEWLINE:
            # Newline breaks link
            self._abort_link_with_parens(ctx)
        else:
            ctx.link_url_buffer.append(char)
            ctx.inline_state = State.LINK_URL
    
    def _inline_link_url(self, ctx: FSTContext, char: str) -> None:
        """Process character while collecting URL."""
        if char == CHAR_RPAREN:
            # End of URL
            self._complete_link(ctx)
        elif char == CHAR_NEWLINE:
            # Newline breaks link
            self._abort_link_with_parens(ctx)
        else:
            ctx.link_url_buffer.append(char)
    
    def _complete_link(self, ctx: FSTContext) -> None:
        """Complete link and output HTML. Uses shared URL sanitization (DRY)."""
        url = "".join(ctx.link_url_buffer)
        text = "".join(ctx.link_text_buffer)
        
        # Sanitize URL using shared helper (DRY with images)
        safe_mode = self._mode == OutputMode.SAFE
        sanitized_url = sanitize_url(url, safe_mode)
        
        if safe_mode and not sanitized_url and url:
            # URL was rejected as unsafe - output as plain text
            ctx.inline_buffer.append(CHAR_LBRACKET)
            ctx.inline_buffer.append(text)
            ctx.inline_buffer.append(CHAR_RBRACKET)
            ctx.inline_buffer.append(CHAR_LPAREN)
            ctx.inline_buffer.append(self._escape_fn(url))
            ctx.inline_buffer.append(CHAR_RPAREN)
        else:
            # Output link HTML
            ctx.inline_buffer.append(HTML_A_OPEN_START)
            ctx.inline_buffer.append(sanitized_url)
            ctx.inline_buffer.append(HTML_A_OPEN_END)
            ctx.inline_buffer.append(text)
            ctx.inline_buffer.append(HTML_A_CLOSE)
        
        # Clear buffers and return to text state
        ctx.link_text_buffer.clear()
        ctx.link_url_buffer.clear()
        ctx.link_text_formatting.clear()
        ctx.inline_state = State.TEXT
    
    def _abort_link(self, ctx: FSTContext) -> None:
        """Abort link parsing and output accumulated text literally."""
        ctx.inline_buffer.append(CHAR_LBRACKET)
        # Close any open formatting
        for fmt in reversed(ctx.link_text_formatting):
            if fmt == "em":
                ctx.link_text_buffer.append(HTML_EM_CLOSE)
            elif fmt == "strong":
                ctx.link_text_buffer.append(HTML_STRONG_CLOSE)
        ctx.inline_buffer.extend(ctx.link_text_buffer)
        ctx.link_text_buffer.clear()
        ctx.link_url_buffer.clear()
        ctx.link_text_formatting.clear()
        ctx.inline_state = State.TEXT
    
    def _abort_link_with_parens(self, ctx: FSTContext) -> None:
        """Abort link parsing when we've already seen ( ."""
        ctx.inline_buffer.append(CHAR_LBRACKET)
        # Close any open formatting
        for fmt in reversed(ctx.link_text_formatting):
            if fmt == "em":
                ctx.link_text_buffer.append(HTML_EM_CLOSE)
            elif fmt == "strong":
                ctx.link_text_buffer.append(HTML_STRONG_CLOSE)
        ctx.inline_buffer.extend(ctx.link_text_buffer)
        ctx.inline_buffer.append(CHAR_RBRACKET)
        ctx.inline_buffer.append(CHAR_LPAREN)
        ctx.inline_buffer.extend(ctx.link_url_buffer)
        ctx.link_text_buffer.clear()
        ctx.link_url_buffer.clear()
        ctx.link_text_formatting.clear()
        ctx.inline_state = State.TEXT
    
    # =========================================================================
    # Image Methods ![alt](url) - DRY: shares URL helper with links
    # =========================================================================
    
    def _inline_image_bang(self, ctx: FSTContext, char: str) -> None:
        """Process character after ! (potential image start)."""
        if char == CHAR_LBRACKET:
            # Valid image start ![
            ctx.inline_state = State.IMAGE_OPEN
            ctx.link_text_buffer.clear()
            ctx.link_url_buffer.clear()
        else:
            # Not an image - output ! and process char
            ctx.inline_buffer.append(CHAR_BANG)
            ctx.inline_state = State.TEXT
            self._inline_text(ctx, char)
    
    def _inline_image_open(self, ctx: FSTContext, char: str) -> None:
        """Process character after ![ (image alt text start)."""
        if char == CHAR_RBRACKET:
            # Empty alt text ![] - valid but unusual
            ctx.inline_state = State.IMAGE_ALT_CLOSE
        elif char == CHAR_NEWLINE:
            # Newline breaks image
            ctx.inline_buffer.append(CHAR_BANG)
            ctx.inline_buffer.append(CHAR_LBRACKET)
            ctx.inline_state = State.TEXT
        else:
            ctx.link_text_buffer.append(char)  # Don't escape alt text yet
            ctx.inline_state = State.IMAGE_ALT
    
    def _inline_image_alt(self, ctx: FSTContext, char: str) -> None:
        """Process character while collecting image alt text."""
        if char == CHAR_RBRACKET:
            # End of alt text
            ctx.inline_state = State.IMAGE_ALT_CLOSE
        elif char == CHAR_NEWLINE:
            # Newline breaks image
            self._abort_image(ctx)
        elif char == CHAR_LBRACKET:
            # Nested [ - abort
            self._abort_image(ctx)
            ctx.inline_buffer.append(CHAR_LBRACKET)
        else:
            ctx.link_text_buffer.append(char)
    
    def _inline_image_alt_close(self, ctx: FSTContext, char: str) -> None:
        """Process character after ] in image (expecting ()."""
        if char == CHAR_LPAREN:
            # Valid image syntax ![alt](
            ctx.inline_state = State.IMAGE_URL_OPEN
            ctx.link_url_buffer.clear()
        else:
            # Not an image - output ![alt] literally (including the ])
            ctx.inline_buffer.append(CHAR_BANG)
            ctx.inline_buffer.append(CHAR_LBRACKET)
            ctx.inline_buffer.extend([self._escape_fn(c) for c in ctx.link_text_buffer])
            ctx.inline_buffer.append(CHAR_RBRACKET)  # Add the closing bracket
            ctx.link_text_buffer.clear()
            ctx.link_url_buffer.clear()
            ctx.inline_state = State.TEXT
            self._inline_text(ctx, char)
    
    def _inline_image_url_open(self, ctx: FSTContext, char: str) -> None:
        """Process first character of image URL."""
        if char == CHAR_RPAREN:
            # Empty URL ![alt]() - still valid, creates img with empty src
            self._complete_image(ctx)
        elif char == CHAR_NEWLINE:
            # Newline breaks image
            self._abort_image_with_parens(ctx)
        else:
            ctx.link_url_buffer.append(char)
            ctx.inline_state = State.IMAGE_URL
    
    def _inline_image_url(self, ctx: FSTContext, char: str) -> None:
        """Process character while collecting image URL."""
        if char == CHAR_RPAREN:
            # End of URL
            self._complete_image(ctx)
        elif char == CHAR_NEWLINE:
            # Newline breaks image
            self._abort_image_with_parens(ctx)
        else:
            ctx.link_url_buffer.append(char)
    
    def _complete_image(self, ctx: FSTContext) -> None:
        """Complete image and output HTML. Uses shared URL sanitization (DRY)."""
        url = "".join(ctx.link_url_buffer)
        alt = "".join(ctx.link_text_buffer)
        
        # Sanitize URL using shared helper (DRY with links)
        safe_mode = self._mode == OutputMode.SAFE
        sanitized_url = sanitize_url(url, safe_mode)
        
        if safe_mode and not sanitized_url and url:
            # URL was rejected as unsafe - output as plain text
            ctx.inline_buffer.append(CHAR_BANG)
            ctx.inline_buffer.append(CHAR_LBRACKET)
            ctx.inline_buffer.append(self._escape_fn(alt))
            ctx.inline_buffer.append(CHAR_RBRACKET)
            ctx.inline_buffer.append(CHAR_LPAREN)
            ctx.inline_buffer.append(self._escape_fn(url))
            ctx.inline_buffer.append(CHAR_RPAREN)
        else:
            # Output image HTML
            # Escape alt text for attribute context
            escaped_alt = self._escape_fn(alt) if self._mode == OutputMode.SAFE else alt
            ctx.inline_buffer.append(HTML_IMG_START)
            ctx.inline_buffer.append(sanitized_url)
            ctx.inline_buffer.append(HTML_IMG_ALT)
            ctx.inline_buffer.append(escaped_alt)
            ctx.inline_buffer.append(HTML_IMG_END)
        
        # Clear buffers and return to text state
        ctx.link_text_buffer.clear()
        ctx.link_url_buffer.clear()
        ctx.inline_state = State.TEXT
    
    def _abort_image(self, ctx: FSTContext) -> None:
        """Abort image parsing and output accumulated text literally."""
        ctx.inline_buffer.append(CHAR_BANG)
        ctx.inline_buffer.append(CHAR_LBRACKET)
        ctx.inline_buffer.extend([self._escape_fn(c) for c in ctx.link_text_buffer])
        ctx.link_text_buffer.clear()
        ctx.link_url_buffer.clear()
        ctx.inline_state = State.TEXT
    
    def _abort_image_with_parens(self, ctx: FSTContext) -> None:
        """Abort image parsing when we've already seen ( ."""
        ctx.inline_buffer.append(CHAR_BANG)
        ctx.inline_buffer.append(CHAR_LBRACKET)
        ctx.inline_buffer.extend([self._escape_fn(c) for c in ctx.link_text_buffer])
        ctx.inline_buffer.append(CHAR_RBRACKET)
        ctx.inline_buffer.append(CHAR_LPAREN)
        ctx.inline_buffer.extend([self._escape_fn(c) for c in ctx.link_url_buffer])
        ctx.link_text_buffer.clear()
        ctx.link_url_buffer.clear()
        ctx.inline_state = State.TEXT
    
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
    
    # =========================================================================
    # Nested List Methods (-, *, 1.)
    # =========================================================================
    
    def _process_nested_list_indent(
        self,
        ctx: FSTContext,
        char: str,
        text: str,
        pos: int,
        length: int
    ) -> None:
        """Process indentation at line start (potential nested list)."""
        if char == CHAR_SPACE:
            ctx.current_indent += 1
        elif char == "\t":
            ctx.current_indent += 4  # Tab = 4 spaces
        elif char in ("-", "*"):
            # Check if followed by space (nested list item)
            if pos + 1 < length and text[pos + 1] == CHAR_SPACE:
                ctx.pending_list_marker = char
                ctx.block_state = BlockState.NESTED_LIST_MARKER
            else:
                # Not a list item - handle as content
                self._handle_indented_content(ctx, char)
        elif char.isdigit():
            # Potential ordered list
            ctx.pending_list_number = char
            ctx.block_state = BlockState.NESTED_LIST_NUMBER
        elif char == CHAR_NEWLINE:
            # Empty indented line - close nested lists as needed
            self._close_nested_lists_to_indent(ctx, 0)
            ctx.block_state = BlockState.LINE_START
        else:
            # Non-list content at this indent
            self._handle_indented_content(ctx, char)
    
    def _process_nested_list_marker(
        self,
        ctx: FSTContext,
        char: str,
        text: str,
        pos: int,
        length: int
    ) -> None:
        """Process after seeing list marker (- or *)."""
        if char == CHAR_SPACE:
            # Valid list item marker
            self._start_nested_list_item(ctx, "ul")
            ctx.block_state = BlockState.NESTED_LIST_CONTENT
        else:
            # Not a valid list marker - treat as paragraph
            self._abort_list_marker(ctx, char)
    
    def _process_nested_list_number(
        self,
        ctx: FSTContext,
        char: str,
        text: str,
        pos: int,
        length: int
    ) -> None:
        """Process while collecting ordered list number."""
        if char.isdigit():
            ctx.pending_list_number += char
        elif char == CHAR_DOT:
            # Check if followed by space
            if pos + 1 < length and text[pos + 1] == CHAR_SPACE:
                ctx.block_state = BlockState.NESTED_LIST_MARKER
                ctx.pending_list_marker = "1"  # Mark as ordered list
            else:
                # Not a valid list - treat as paragraph
                self._abort_list_number(ctx, char)
        else:
            # Not a valid ordered list - treat as paragraph
            self._abort_list_number(ctx, char)
    
    def _process_nested_list_content(
        self,
        ctx: FSTContext,
        char: str,
        text: str,
        pos: int,
        length: int
    ) -> None:
        """Process content inside a list item."""
        if char == CHAR_NEWLINE:
            # End of list item content - don't close <li> yet, might have nested content
            self._flush_inline(ctx)
            ctx.block_state = BlockState.LINE_START
            ctx.inline_state = State.TEXT
        else:
            self._process_inline_char(ctx, char)
    
    def _start_nested_list_item(self, ctx: FSTContext, list_type: str) -> None:
        """Start a new nested list item at the current indentation level."""
        # Close paragraph if open
        if ctx.in_paragraph:
            self._flush_inline(ctx)
            ctx.output.append(HTML_P_CLOSE)
            ctx.output.append(HTML_NEWLINE)
            ctx.in_paragraph = False
        
        # Determine target indent level (2 spaces per level)
        target_level = ctx.current_indent // 2
        
        # If ordered list marker, override list_type
        if ctx.pending_list_marker == "1":
            list_type = "ol"
        
        # Get current depth (number of open lists)
        current_depth = len(ctx.list_stack)
        
        if current_depth == 0:
            # No list open yet - open the first one
            self._open_nested_list(ctx, list_type, target_level)
        elif target_level > ctx.list_stack[-1][1]:
            # Going deeper - open nested list (inside current li)
            self._open_nested_list(ctx, list_type, target_level)
        elif target_level < ctx.list_stack[-1][1]:
            # Going shallower - close nested lists
            while ctx.list_stack and ctx.list_stack[-1][1] > target_level:
                ctx.output.append(HTML_LI_CLOSE)
                ctx.output.append(HTML_NEWLINE)
                self._close_nested_list(ctx)
            # Close the previous item at this level if we have one
            if ctx.list_stack:
                ctx.output.append(HTML_LI_CLOSE)
                ctx.output.append(HTML_NEWLINE)
        else:
            # Same level - close previous item
            ctx.output.append(HTML_LI_CLOSE)
            ctx.output.append(HTML_NEWLINE)
            # Check if list type changed
            if ctx.list_stack and ctx.list_stack[-1][0] != list_type:
                self._close_nested_list(ctx)
                self._open_nested_list(ctx, list_type, target_level)
        
        # Output list item
        ctx.output.append(HTML_LI_OPEN)
        # Note: Don't set ctx.in_list here - that's for the old list system
        
        # Clear pending markers
        ctx.pending_list_marker = ""
        ctx.pending_list_number = ""
        ctx.current_indent = 0
    
    def _open_nested_list(self, ctx: FSTContext, list_type: str, level: int) -> None:
        """Open a new nested list."""
        if list_type == "ol":
            ctx.output.append(HTML_OL_OPEN)
        else:
            ctx.output.append(HTML_UL_OPEN)
        ctx.output.append(HTML_NEWLINE)
        ctx.list_stack.append((list_type, level))
    
    def _close_nested_list(self, ctx: FSTContext) -> None:
        """Close the innermost nested list."""
        if ctx.list_stack:
            list_type, _ = ctx.list_stack.pop()
            if list_type == "ol":
                ctx.output.append(HTML_OL_CLOSE)
            else:
                ctx.output.append(HTML_UL_CLOSE)
            ctx.output.append(HTML_NEWLINE)
        if not ctx.list_stack:
            ctx.in_list = False
    
    def _close_nested_lists_to_indent(self, ctx: FSTContext, target_level: int) -> None:
        """Close all nested lists down to the target indentation level."""
        while ctx.list_stack and len(ctx.list_stack) > target_level:
            # Close the current item
            ctx.output.append(HTML_LI_CLOSE)
            ctx.output.append(HTML_NEWLINE)
            self._close_nested_list(ctx)
    
    def _close_all_nested_lists(self, ctx: FSTContext) -> None:
        """Close all open nested lists."""
        while ctx.list_stack:
            ctx.output.append(HTML_LI_CLOSE)
            ctx.output.append(HTML_NEWLINE)
            self._close_nested_list(ctx)
    
    def _handle_indented_content(self, ctx: FSTContext, char: str) -> None:
        """Handle non-list content that appeared after indentation."""
        # This is either continuation content or a new paragraph
        if ctx.list_stack:
            # In a list context - this could be continued list item
            # For simplicity, treat as new paragraph outside list
            self._close_all_nested_lists(ctx)
        self._start_paragraph(ctx)
        self._process_inline_char(ctx, char)
        ctx.current_indent = 0
    
    def _abort_list_marker(self, ctx: FSTContext, char: str) -> None:
        """Abort list marker parsing and treat as paragraph."""
        self._start_paragraph(ctx)
        # Output the indent as spaces
        for _ in range(ctx.current_indent):
            ctx.inline_buffer.append(CHAR_SPACE)
        # Output the marker character
        ctx.inline_buffer.append(self._escape_fn(ctx.pending_list_marker))
        # Process current char
        self._process_inline_char(ctx, char)
        ctx.pending_list_marker = ""
        ctx.current_indent = 0
    
    def _abort_list_number(self, ctx: FSTContext, char: str) -> None:
        """Abort ordered list number parsing and treat as paragraph."""
        self._start_paragraph(ctx)
        # Output the indent as spaces
        for _ in range(ctx.current_indent):
            ctx.inline_buffer.append(CHAR_SPACE)
        # Output the number
        ctx.inline_buffer.append(self._escape_fn(ctx.pending_list_number))
        # Process current char
        self._process_inline_char(ctx, char)
        ctx.pending_list_number = ""
        ctx.current_indent = 0
    
    # =========================================================================
    # Table Methods (GFM subset)
    # =========================================================================
    
    def _is_table_separator_line(self, text: str, pos: int, length: int) -> bool:
        """Check if from current position we have a table separator line."""
        # A separator line contains only |, -, :, and spaces
        i = pos
        has_dash = False
        while i < length:
            c = text[i]
            if c == CHAR_NEWLINE:
                break
            if c == CHAR_DASH:
                has_dash = True
            elif c not in (CHAR_PIPE, CHAR_COLON, CHAR_SPACE, CHAR_DASH):
                return False
            i += 1
        return has_dash
    
    def _start_table_row(
        self,
        ctx: FSTContext,
        text: str,
        pos: int,
        length: int
    ) -> None:
        """Start processing a potential table row."""
        # Don't close things if we're already in a table
        if not ctx.in_table:
            if ctx.in_paragraph:
                self._flush_inline(ctx)
                ctx.output.append(HTML_P_CLOSE)
                ctx.output.append(HTML_NEWLINE)
                ctx.in_paragraph = False
            
            self._close_all_nested_lists(ctx)
        
        # Start collecting row
        ctx.table_row_buffer.clear()
        ctx.table_cell_buffer.clear()
        ctx.block_state = BlockState.TABLE_ROW
    
    def _process_table_row(
        self,
        ctx: FSTContext,
        char: str,
        text: str,
        pos: int,
        length: int
    ) -> None:
        """Process characters in a table row."""
        if char == CHAR_PIPE:
            # End of cell, start new one
            cell = "".join(ctx.table_cell_buffer).strip()
            ctx.table_row_buffer.append(cell)
            ctx.table_cell_buffer.clear()
        elif char == CHAR_NEWLINE:
            # End of row
            cell = "".join(ctx.table_cell_buffer).strip()
            if cell:  # Don't add empty trailing cell
                ctx.table_row_buffer.append(cell)
            ctx.table_cell_buffer.clear()
            self._finish_table_row(ctx, text, pos, length)
        else:
            ctx.table_cell_buffer.append(char)
    
    def _finish_table_row(
        self,
        ctx: FSTContext,
        text: str,
        pos: int,
        length: int
    ) -> None:
        """Finish processing a table row and determine next action."""
        row = ctx.table_row_buffer[:]  # Copy the row
        
        # Remove leading empty cell if row started with |
        if row and row[0] == "":
            row = row[1:]
        
        # Remove trailing empty cell if row ended with |
        if row and row[-1] == "":
            row = row[:-1]
        
        if not ctx.in_table:
            # This is potentially a header row
            # Check if next line is separator
            next_line_start = pos + 1
            if next_line_start < length and self._is_separator_row(text, next_line_start, length):
                # This is a header row - store it
                ctx.table_header_row = row
                ctx.in_table = True
                ctx.table_has_body = False
                ctx.block_state = BlockState.LINE_START
            else:
                # Not a table - output as paragraph
                self._output_row_as_paragraph(ctx, row)
                ctx.block_state = BlockState.LINE_START
        elif not ctx.table_alignments:
            # We have a header but no alignments yet - this should be separator
            if self._parse_separator_row(ctx, row):
                # Valid separator - output table header
                self._output_table_header(ctx)
                ctx.block_state = BlockState.LINE_START
            else:
                # Invalid separator - abort table
                self._abort_table(ctx, row)
        else:
            # This is a body row
            self._output_table_body_row(ctx, row)
            ctx.block_state = BlockState.LINE_START
        
        ctx.table_row_buffer.clear()
    
    def _is_separator_row(self, text: str, pos: int, length: int) -> bool:
        """Check if the line starting at pos is a valid table separator."""
        i = pos
        has_dash = False
        pipe_count = 0
        
        while i < length:
            c = text[i]
            if c == CHAR_NEWLINE:
                break
            if c == CHAR_DASH:
                has_dash = True
            elif c == CHAR_PIPE:
                pipe_count += 1
            elif c not in (CHAR_COLON, CHAR_SPACE):
                return False
            i += 1
        
        return has_dash and pipe_count > 0
    
    def _parse_separator_row(self, ctx: FSTContext, row: list[str]) -> bool:
        """Parse a separator row and extract alignments. Returns True if valid."""
        alignments = []
        
        for cell in row:
            cell = cell.strip()
            if not cell:
                alignments.append("")
                continue
            
            # Check for alignment patterns
            left_colon = cell.startswith(CHAR_COLON)
            right_colon = cell.endswith(CHAR_COLON)
            
            # Remove colons for validation
            inner = cell.strip(CHAR_COLON)
            
            # Must have at least one dash
            if not inner or not all(c == CHAR_DASH for c in inner):
                return False
            
            if left_colon and right_colon:
                alignments.append("center")
            elif right_colon:
                alignments.append("right")
            elif left_colon:
                alignments.append("left")
            else:
                alignments.append("")
        
        ctx.table_alignments = alignments
        return True
    
    def _output_table_header(self, ctx: FSTContext) -> None:
        """Output the table header row."""
        ctx.output.append(HTML_TABLE_OPEN)
        ctx.output.append(HTML_NEWLINE)
        ctx.output.append(HTML_THEAD_OPEN)
        ctx.output.append(HTML_NEWLINE)
        ctx.output.append(HTML_TR_OPEN)
        
        for i, cell in enumerate(ctx.table_header_row):
            alignment = ctx.table_alignments[i] if i < len(ctx.table_alignments) else ""
            self._output_table_cell(ctx, cell, is_header=True, alignment=alignment)
        
        ctx.output.append(HTML_TR_CLOSE)
        ctx.output.append(HTML_NEWLINE)
        ctx.output.append(HTML_THEAD_CLOSE)
        ctx.output.append(HTML_NEWLINE)
    
    def _output_table_body_row(self, ctx: FSTContext, row: list[str]) -> None:
        """Output a table body row."""
        if not ctx.table_has_body:
            ctx.output.append(HTML_TBODY_OPEN)
            ctx.output.append(HTML_NEWLINE)
            ctx.table_has_body = True
        
        ctx.output.append(HTML_TR_OPEN)
        
        for i, cell in enumerate(row):
            alignment = ctx.table_alignments[i] if i < len(ctx.table_alignments) else ""
            self._output_table_cell(ctx, cell, is_header=False, alignment=alignment)
        
        ctx.output.append(HTML_TR_CLOSE)
        ctx.output.append(HTML_NEWLINE)
    
    def _output_table_cell(
        self,
        ctx: FSTContext,
        content: str,
        is_header: bool,
        alignment: str
    ) -> None:
        """Output a single table cell with proper escaping."""
        # Choose opening tag based on header/alignment
        if is_header:
            if alignment == "left":
                ctx.output.append(HTML_TH_ALIGN_LEFT)
            elif alignment == "center":
                ctx.output.append(HTML_TH_ALIGN_CENTER)
            elif alignment == "right":
                ctx.output.append(HTML_TH_ALIGN_RIGHT)
            else:
                ctx.output.append(HTML_TH_OPEN)
        else:
            if alignment == "left":
                ctx.output.append(HTML_TD_ALIGN_LEFT)
            elif alignment == "center":
                ctx.output.append(HTML_TD_ALIGN_CENTER)
            elif alignment == "right":
                ctx.output.append(HTML_TD_ALIGN_RIGHT)
            else:
                ctx.output.append(HTML_TD_OPEN)
        
        # Process cell content through inline parser for formatting
        # Create a mini-context for cell content parsing
        escaped_content = self._process_inline_content(ctx, content)
        ctx.output.append(escaped_content)
        
        # Close tag
        if is_header:
            ctx.output.append(HTML_TH_CLOSE)
        else:
            ctx.output.append(HTML_TD_CLOSE)
    
    def _process_inline_content(self, ctx: FSTContext, content: str) -> str:
        """Process inline content and return HTML string."""
        # Save current inline state
        saved_state = ctx.inline_state
        saved_buffer = ctx.inline_buffer[:]
        saved_pending = ctx.pending_stars
        
        # Reset for fresh inline processing
        ctx.inline_state = State.TEXT
        ctx.inline_buffer = []
        ctx.pending_stars = 0
        
        # Process each character
        for char in content:
            self._process_inline_char(ctx, char)
        
        # Flush any pending inline state
        if ctx.pending_stars > 0:
            ctx.inline_buffer.append(CHAR_STAR * ctx.pending_stars)
            ctx.pending_stars = 0
        
        # Close any open formatting
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
                ctx.inline_buffer.append(HTML_CODE_CLOSE)
        
        result = "".join(ctx.inline_buffer)
        
        # Restore state
        ctx.inline_state = saved_state
        ctx.inline_buffer = saved_buffer
        ctx.pending_stars = saved_pending
        
        return result
    
    def _output_row_as_paragraph(self, ctx: FSTContext, row: list[str]) -> None:
        """Output a row as paragraph content (not a table)."""
        content = CHAR_PIPE + CHAR_PIPE.join(row) + CHAR_PIPE
        self._start_paragraph(ctx)
        for char in content:
            self._process_inline_char(ctx, char)
    
    def _abort_table(self, ctx: FSTContext, row: list[str]) -> None:
        """Abort table parsing and output accumulated content as paragraphs."""
        # Output header row as paragraph
        self._output_row_as_paragraph(ctx, ctx.table_header_row)
        self._flush_inline(ctx)
        ctx.output.append(HTML_P_CLOSE)
        ctx.output.append(HTML_NEWLINE)
        ctx.in_paragraph = False
        
        # Output current row as paragraph
        self._output_row_as_paragraph(ctx, row)
        
        # Reset table state
        ctx.in_table = False
        ctx.table_header_row.clear()
        ctx.table_alignments.clear()
        ctx.table_has_body = False
    
    def _close_table(self, ctx: FSTContext) -> None:
        """Close an open table."""
        if ctx.in_table:
            if ctx.table_has_body:
                ctx.output.append(HTML_TBODY_CLOSE)
                ctx.output.append(HTML_NEWLINE)
            ctx.output.append(HTML_TABLE_CLOSE)
            ctx.output.append(HTML_NEWLINE)
            ctx.in_table = False
            ctx.table_header_row.clear()
            ctx.table_alignments.clear()
            ctx.table_has_body = False

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
            
            # Link states - abort and output literally
            case State.LINK_OPEN:
                ctx.inline_buffer.append(CHAR_LBRACKET)
            
            case State.LINK_TEXT | State.LINK_TEXT_STAR_ONE | State.LINK_TEXT_STAR_TWO | State.LINK_TEXT_ITALIC | State.LINK_TEXT_BOLD:
                ctx.inline_buffer.append(CHAR_LBRACKET)
                # Close any open formatting in link text
                for fmt in reversed(ctx.link_text_formatting):
                    if fmt == "em":
                        ctx.link_text_buffer.append(HTML_EM_CLOSE)
                    elif fmt == "strong":
                        ctx.link_text_buffer.append(HTML_STRONG_CLOSE)
                ctx.inline_buffer.extend(ctx.link_text_buffer)
            
            case State.LINK_TEXT_CLOSE:
                ctx.inline_buffer.append(CHAR_LBRACKET)
                ctx.inline_buffer.extend(ctx.link_text_buffer)
                ctx.inline_buffer.append(CHAR_RBRACKET)
            
            case State.LINK_URL_OPEN | State.LINK_URL:
                ctx.inline_buffer.append(CHAR_LBRACKET)
                ctx.inline_buffer.extend(ctx.link_text_buffer)
                ctx.inline_buffer.append(CHAR_RBRACKET)
                ctx.inline_buffer.append(CHAR_LPAREN)
                ctx.inline_buffer.extend([self._escape_fn(c) for c in ctx.link_url_buffer])
            
            # Image states - abort and output literally
            case State.IMAGE_BANG:
                ctx.inline_buffer.append(CHAR_BANG)
            
            case State.IMAGE_OPEN | State.IMAGE_ALT:
                ctx.inline_buffer.append(CHAR_BANG)
                ctx.inline_buffer.append(CHAR_LBRACKET)
                ctx.inline_buffer.extend([self._escape_fn(c) for c in ctx.link_text_buffer])
            
            case State.IMAGE_ALT_CLOSE:
                ctx.inline_buffer.append(CHAR_BANG)
                ctx.inline_buffer.append(CHAR_LBRACKET)
                ctx.inline_buffer.extend([self._escape_fn(c) for c in ctx.link_text_buffer])
                ctx.inline_buffer.append(CHAR_RBRACKET)
            
            case State.IMAGE_URL_OPEN | State.IMAGE_URL:
                ctx.inline_buffer.append(CHAR_BANG)
                ctx.inline_buffer.append(CHAR_LBRACKET)
                ctx.inline_buffer.extend([self._escape_fn(c) for c in ctx.link_text_buffer])
                ctx.inline_buffer.append(CHAR_RBRACKET)
                ctx.inline_buffer.append(CHAR_LPAREN)
                ctx.inline_buffer.extend([self._escape_fn(c) for c in ctx.link_url_buffer])
        
        # Clear link/image buffers
        ctx.link_text_buffer.clear()
        ctx.link_url_buffer.clear()
        ctx.link_text_formatting.clear()
        
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
        
        # Handle pending nested list content - flush but don't close li yet
        # (will be closed by _close_all_nested_lists)
        if ctx.block_state == BlockState.NESTED_LIST_CONTENT:
            self._flush_inline(ctx)
        
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
        
        # Close any open list item (if we ended mid-list) - old list system
        if ctx.block_state == BlockState.LIST_CONTENT:
            ctx.output.append(HTML_LI_CLOSE)
            ctx.output.append(HTML_NEWLINE)
        
        self._close_list(ctx)
        
        # Close all nested lists (new nested list system)
        self._close_all_nested_lists(ctx)
        
        # Finish any pending table row before closing table
        if ctx.in_table and (ctx.table_row_buffer or ctx.table_cell_buffer):
            # Flush any pending cell content
            if ctx.table_cell_buffer:
                ctx.table_row_buffer.append("".join(ctx.table_cell_buffer).strip())
                ctx.table_cell_buffer.clear()
            
            # Get the row - no need to remove leading/trailing empty cells here
            # because _start_table_row handles leading pipe and trailing pipes
            # add actual empty cells only if there's content between them
            row = ctx.table_row_buffer[:]
            
            # If we have alignments, this is a body row
            if ctx.table_alignments and row:
                self._output_table_body_row(ctx, row)
            
            ctx.table_row_buffer.clear()
        
        # Close any open table
        self._close_table(ctx)
        
        # Close any open blockquotes
        self._close_all_blockquotes(ctx)
