"""
Markdown clean-up shared by the pipeline and the UI. Plain Python with no model imports,
so the UI can use it without loading the backend.
"""

import re

_HEADING = re.compile(r"^ {0,3}(#{1,6})(?:[ \t]*#+)*(?:[ \t]+|(?=[A-Z*_]))(.*?)(?:[ \t]+#+)?[ \t]*$")
_ONLY_HASHES = re.compile(r"^ {0,3}#+[ \t]*$")


def normalize_markdown(text: str) -> str:
    """
    Tidy heading markers so a stray "###" never shows: "### ### Title" or "###Title" become "### Title",
    closing "Title ###" markers are dropped, and lines that are only hashes are removed.
    The model sometimes writes doubled markers; the pipeline cleans its reports with this before the Critic
    reads them, so the score isn't lowered for a formatting slip.
    """
    lines = []
    for line in text.splitlines():
        if _ONLY_HASHES.match(line):
            continue
        match = _HEADING.match(line)
        if match and match.group(2).strip():
            # Repeated markers like "## ### Title": the run nearest the text wins
            level = min(len(re.findall(r"#+", line[: match.start(2)])[-1]), 6)
            lines.append(f"{'#' * level} {match.group(2).strip()}")
        else:
            lines.append(line)
    return "\n".join(lines)
