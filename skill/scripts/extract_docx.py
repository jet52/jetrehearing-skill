#!/usr/bin/env python3
"""Extract text from .docx opinions, preserving [¶N] paragraph numbering.

Usage:
    python3 extract_docx.py opinion.docx > opinion.txt
    python3 extract_docx.py opinion.docx --json

Outputs plain text with paragraph numbering preserved, or structured JSON.
Requires: python-docx (pip install python-docx)
"""

import argparse
import json
import re
import sys
from pathlib import Path

try:
    from docx import Document
    from docx.opc.exceptions import PackageNotFoundError
except ImportError:
    print(
        "ERROR: python-docx is not installed.\n"
        "Install with: pip install python-docx",
        file=sys.stderr,
    )
    sys.exit(1)


def _extract_footnotes(doc) -> dict[int, str]:
    """Extract footnotes from the document, keyed by footnote ID."""
    footnotes = {}
    # Access the footnotes part if it exists
    try:
        footnote_part = doc.part.package.part_related_by(
            "http://schemas.openxmlformats.org/officeDocument/2006/relationships/footnotes"
        )
    except KeyError:
        return footnotes

    from lxml import etree

    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    for fn in footnote_part.element.findall(".//w:footnote", ns):
        fn_id = fn.get(f'{{{ns["w"]}}}id')
        if fn_id is None or fn_id in ("0", "-1"):
            # Skip separator and continuation separator
            continue
        text_parts = []
        for para in fn.findall(".//w:p", ns):
            runs = para.findall(".//w:r/w:t", ns)
            text_parts.append("".join(r.text or "" for r in runs))
        footnotes[int(fn_id)] = " ".join(text_parts).strip()

    return footnotes


def _detect_heading(paragraph) -> int | None:
    """Detect if a paragraph uses a heading style. Returns heading level or None."""
    style_name = paragraph.style.name if paragraph.style else ""
    if style_name.startswith("Heading"):
        try:
            return int(style_name.split()[-1])
        except (ValueError, IndexError):
            return 1
    return None


def _extract_para_number(text: str) -> int | None:
    """Extract [¶N] paragraph number from text."""
    match = re.match(r"\[¶(\d+)\]", text.strip())
    if match:
        return int(match.group(1))
    return None


def extract_docx(path: Path) -> list[dict]:
    """Extract paragraphs from a .docx file.

    Returns a list of dicts:
        {para_num: int|None, text: str, style: str, heading_level: int|None, footnotes: list[str]}
    """
    try:
        doc = Document(str(path))
    except PackageNotFoundError:
        print(f"Error: Not a valid .docx file: {path}", file=sys.stderr)
        sys.exit(1)

    footnotes = _extract_footnotes(doc)
    results = []

    for para in doc.paragraphs:
        text = para.text.strip()
        if not text:
            continue

        para_num = _extract_para_number(text)
        heading_level = _detect_heading(para)
        style_name = para.style.name if para.style else ""

        # Collect footnote references in this paragraph
        para_footnotes = []
        from lxml import etree
        ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
        for fn_ref in para._element.findall(".//w:footnoteReference", ns):
            fn_id = fn_ref.get(f'{{{ns["w"]}}}id')
            if fn_id and int(fn_id) in footnotes:
                para_footnotes.append(footnotes[int(fn_id)])

        results.append({
            "para_num": para_num,
            "text": text,
            "style": style_name,
            "heading_level": heading_level,
            "footnotes": para_footnotes,
        })

    return results


def format_plain(paragraphs: list[dict]) -> str:
    """Format extracted paragraphs as plain text."""
    lines = []
    for p in paragraphs:
        if p["heading_level"] is not None:
            prefix = "#" * p["heading_level"] + " "
            lines.append(f"\n{prefix}{p['text']}\n")
        else:
            lines.append(p["text"])

        for fn in p["footnotes"]:
            lines.append(f"  [footnote: {fn}]")

    return "\n\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Extract text from .docx opinions with paragraph numbering."
    )
    parser.add_argument("docx_file", type=Path, help=".docx file to extract")
    parser.add_argument(
        "--json", action="store_true", default=False,
        help="Output as JSON array"
    )
    args = parser.parse_args()

    if not args.docx_file.exists():
        print(f"Error: file not found: {args.docx_file}", file=sys.stderr)
        sys.exit(1)

    paragraphs = extract_docx(args.docx_file)

    if args.json:
        print(json.dumps(paragraphs, indent=2, ensure_ascii=False))
    else:
        print(format_plain(paragraphs))


if __name__ == "__main__":
    main()
