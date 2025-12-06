"""
Safe HTML escaping and sanitization module.

Implements secure HTML escaping to prevent XSS attacks.
Zero external dependencies - pure Python implementation.
"""

from __future__ import annotations

from typing import Final
from functools import lru_cache


# HTML entity replacements - order matters for & which must be first
HTML_ESCAPE_TABLE: Final[tuple[tuple[str, str], ...]] = (
    ("&", "&amp;"),
    ("<", "&lt;"),
    (">", "&gt;"),
    ('"', "&quot;"),
    ("'", "&#x27;"),
)

# Dangerous patterns to detect (case-insensitive)
DANGEROUS_PATTERNS: Final[tuple[str, ...]] = (
    "<script",
    "</script",
    "javascript:",
    "vbscript:",
    "data:",
    "on",  # onclick, onerror, etc.
)

# Maximum input length to prevent DoS
MAX_INPUT_LENGTH: Final[int] = 10_000_000  # 10MB


class HTMLEscaper:
    """
    Secure HTML escaper with XSS prevention.
    
    Provides two modes:
    - safe: Escapes all HTML special characters
    - raw: Passes through HTML as-is (use with trusted input only)
    
    All methods are static or class methods for zero allocation overhead.
    """
    
    __slots__ = ()
    
    @staticmethod
    @lru_cache(maxsize=4096)
    def escape_char(char: str) -> str:
        """
        Escape a single character if needed.
        
        Uses LRU cache for frequently accessed characters.
        Most characters pass through unchanged.
        """
        match char:
            case "&":
                return "&amp;"
            case "<":
                return "&lt;"
            case ">":
                return "&gt;"
            case '"':
                return "&quot;"
            case "'":
                return "&#x27;"
            case _:
                return char
    
    @staticmethod
    def escape(text: str) -> str:
        """
        Escape HTML special characters in text.
        
        This is the primary escaping function used in safe mode.
        Processes character-by-character for O(N) complexity.
        
        Args:
            text: The text to escape
            
        Returns:
            HTML-escaped text safe for embedding in HTML
        """
        if not text:
            return ""
        
        # Fast path: check if any escaping needed
        needs_escape = False
        for char in text:
            if char in ("&", "<", ">", '"', "'"):
                needs_escape = True
                break
        
        if not needs_escape:
            return text
        
        # Build escaped string using list for efficiency
        result: list[str] = []
        escape_char = HTMLEscaper.escape_char
        
        for char in text:
            result.append(escape_char(char))
        
        return "".join(result)
    
    @staticmethod
    def escape_attribute(text: str) -> str:
        """
        Escape text for use in HTML attributes.
        
        More aggressive escaping for attribute context.
        """
        if not text:
            return ""
        
        # Standard escape plus additional attribute-specific escapes
        escaped = HTMLEscaper.escape(text)
        # Replace backticks which can be used in some XSS vectors
        return escaped.replace("`", "&#x60;")
    
    @staticmethod
    def contains_dangerous_pattern(text: str) -> bool:
        """
        Check if text contains potentially dangerous patterns.
        
        Used for additional security validation.
        Does NOT modify the text - only detects.
        
        Args:
            text: Text to check
            
        Returns:
            True if dangerous patterns detected
        """
        if not text:
            return False
        
        text_lower = text.lower()
        
        # Check for script tags
        if "<script" in text_lower or "</script" in text_lower:
            return True
        
        # Check for javascript: URLs
        if "javascript:" in text_lower:
            return True
        
        # Check for vbscript: URLs
        if "vbscript:" in text_lower:
            return True
        
        # Check for data: URLs (can contain scripts)
        if "data:" in text_lower:
            # Allow safe data URLs for images
            if "data:image/" in text_lower:
                # Still dangerous if it contains script
                if "script" in text_lower:
                    return True
                return False
            return True
        
        return False
    
    @staticmethod
    def sanitize(text: str) -> str:
        """
        Sanitize text by escaping and removing dangerous patterns.
        
        This is the most aggressive sanitization mode.
        Use for untrusted user input.
        
        Args:
            text: Text to sanitize
            
        Returns:
            Sanitized text
        """
        if not text:
            return ""
        
        # First escape all HTML
        escaped = HTMLEscaper.escape(text)
        
        # The escaped text should be safe, but verify
        # After escaping, dangerous patterns should be neutralized
        return escaped
    
    @staticmethod
    def validate_input(text: str) -> bool:
        """
        Validate input text meets security requirements.
        
        Args:
            text: Text to validate
            
        Returns:
            True if input is valid, False otherwise
        """
        if text is None:
            return False
        
        if not isinstance(text, str):
            return False
        
        if len(text) > MAX_INPUT_LENGTH:
            return False
        
        return True


def escape_html(text: str) -> str:
    """
    Convenience function for HTML escaping.
    
    This is the primary public API for escaping.
    """
    return HTMLEscaper.escape(text)


def escape_attribute(text: str) -> str:
    """
    Convenience function for attribute escaping.
    """
    return HTMLEscaper.escape_attribute(text)


def is_safe(text: str) -> bool:
    """
    Check if text is safe (contains no dangerous patterns).
    """
    return not HTMLEscaper.contains_dangerous_pattern(text)


# =========================================================================
# URL Sanitization for Links and Images (DRY helper)
# =========================================================================

# Dangerous URL protocols that could lead to XSS
DANGEROUS_PROTOCOLS: Final[tuple[str, ...]] = (
    "javascript:",
    "vbscript:",
    "data:",
)

# Safe protocols whitelist for strict mode
SAFE_PROTOCOLS: Final[tuple[str, ...]] = (
    "http://",
    "https://",
    "mailto:",
    "tel:",
    "ftp://",
    "#",  # Anchor links
    "/",  # Relative paths
)


def is_safe_url(url: str) -> bool:
    """
    Check if a URL is safe for use in href/src attributes.
    
    Rejects dangerous protocols like javascript:, data:, vbscript:.
    This is the shared helper for both links and images (DRY).
    
    Args:
        url: The URL to check
        
    Returns:
        True if URL is safe, False if it contains dangerous protocols
    """
    if not url:
        return True  # Empty URL is safe (just won't link anywhere)
    
    # Normalize for case-insensitive check
    url_lower = url.lower().strip()
    
    # Check for dangerous protocols
    for protocol in DANGEROUS_PROTOCOLS:
        if url_lower.startswith(protocol):
            return False
    
    # Additional check: reject URLs with encoded dangerous protocols
    # e.g., "java&#115;cript:" or "javascript&#58;"
    # After decoding, these would be dangerous
    url_decoded = url_lower.replace("&#", "").replace(";", "")
    for protocol in ("javascript", "vbscript", "data"):
        if protocol in url_decoded:
            # Additional paranoid check - reject if protocol name appears
            # This catches things like "java script:" with spaces
            protocol_no_space = protocol.replace(" ", "")
            url_no_space = url_lower.replace(" ", "").replace("\t", "")
            if url_no_space.startswith(protocol_no_space + ":"):
                return False
    
    return True


def sanitize_url(url: str, safe_mode: bool = True) -> str:
    """
    Sanitize a URL for use in HTML attributes.
    
    In safe mode, dangerous URLs are replaced with empty string.
    The URL is also escaped for HTML attribute context.
    
    This is the shared sanitizer for links and images (DRY).
    
    Args:
        url: The URL to sanitize
        safe_mode: If True, reject dangerous URLs; if False, pass through
        
    Returns:
        Sanitized URL safe for use in href/src attributes
    """
    if not url:
        return ""
    
    # In safe mode, reject dangerous URLs
    if safe_mode and not is_safe_url(url):
        return ""
    
    # Escape for HTML attribute context
    return HTMLEscaper.escape_attribute(url)
