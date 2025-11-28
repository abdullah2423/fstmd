"""
Command-line interface for FSTMD.
"""

from __future__ import annotations

import sys
from fstmd import Markdown


def main() -> int:
    """Main entry point for CLI."""
    if len(sys.argv) < 2:
        print("Usage: fstmd <markdown_text>", file=sys.stderr)
        print("       echo 'markdown' | fstmd -", file=sys.stderr)
        return 1
    
    if sys.argv[1] == "-":
        text = sys.stdin.read()
    else:
        text = " ".join(sys.argv[1:])
    
    md = Markdown(mode="safe")
    result = md.render(text)
    print(result)
    return 0


if __name__ == "__main__":
    sys.exit(main())
