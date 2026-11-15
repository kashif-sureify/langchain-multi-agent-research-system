"""
Turn a finished research run into a PDF: a short header, the report, then the critic's review.

The report is Markdown, so it's converted to HTML with markdown-it-py and laid out by
PyMuPDF's Story engine, which keeps links clickable and has fallback fonts for characters
like "—", "→" or "≈".
"""

import re
from html import escape

import pymupdf
from markdown_it import MarkdownIt

from ui.components import parse_critic, score_grade

# html=False: any raw HTML in the model's output is shown as text instead of being rendered
_markdown = MarkdownIt("commonmark", {"html": False}).enable("table")

# A bare URL that isn't already part of a Markdown link "[text](url)" or an autolink "<url>".
# Trailing punctuation such as a sentence-ending "." is left out of the link.
_BARE_URL = re.compile(r"(?<![<(\[\w/])(https?://[^\s<>()\[\]]*[^\s<>()\[\].,;:!?'\"])")


def _to_html(markdown_text: str) -> str:
    """Render Markdown to HTML, making bare URLs clickable (Streamlit does this on screen, Markdown doesn't)."""
    return _markdown.render(_BARE_URL.sub(r"<\1>", markdown_text))

PAGE = pymupdf.paper_rect("a4")
CONTENT = PAGE + (56, 60, -56, -64)  # page margins in points: left, top, right, bottom
FOOTER_Y = PAGE.height - 34
KEEP_WITH_NEXT = 110  # a heading closer than this (points) to the page bottom moves to the next page
GREY = (0.45, 0.48, 0.55)

LEVEL_COLORS = {"success": "#15803D", "warning": "#B45309", "danger": "#DC2626"}

CSS = """
* { font-family: sans-serif; }
body { font-size: 10.5pt; color: #1F2430; line-height: 1.45; }
p { margin-top: 0; margin-bottom: 7pt; }
h1 { font-size: 19pt; color: #312E81; margin-top: 4pt; margin-bottom: 8pt; }
h2 { font-size: 14pt; color: #1F2430; margin-top: 16pt; margin-bottom: 6pt; }
h3 { font-size: 12pt; color: #1F2430; margin-top: 12pt; margin-bottom: 5pt; }
h4 { font-size: 11pt; margin-top: 10pt; margin-bottom: 4pt; }
ul, ol { margin-top: 0; margin-bottom: 7pt; }
li { margin-bottom: 3pt; }
a { color: #4F46E5; text-decoration: none; }
code, pre { font-family: monospace; font-size: 9.5pt; color: #3730A3; }
blockquote { color: #5D6678; margin-left: 12pt; }
hr { color: #E4E7F0; margin-top: 10pt; margin-bottom: 10pt; }
table { border-collapse: collapse; margin-bottom: 8pt; }
th, td { border: 0.5pt solid #D5D9E4; padding: 3pt 5pt; font-size: 9.5pt; }
th { background-color: #F1F3F9; }

.brand { font-size: 8.5pt; font-weight: bold; color: #6366F1; letter-spacing: 1pt; margin-bottom: 2pt; }
.meta { font-size: 9pt; color: #5D6678; margin-bottom: 0; }
.score { font-size: 12pt; margin-bottom: 6pt; }
.verdict { font-size: 11pt; font-style: italic; }
"""


def _critic_html(feedback: str) -> str:
    review = parse_critic(feedback)
    if not review:  # the critic didn't follow the expected format; include its reply as-is
        return _to_html(feedback)

    grade, level = score_grade(review["score"])
    strengths = "".join(f"<li>{escape(item)}</li>" for item in review["strengths"]) or "<li>None listed</li>"
    improvements = "".join(f"<li>{escape(item)}</li>" for item in review["improvements"]) or "<li>None listed</li>"
    verdict = escape(review["verdict"]) or "No verdict given."
    return f"""
<p class="score"><b>Score: {review["score"]:g}/10</b> &#183;
  <span style="color: {LEVEL_COLORS[level]};"><b>{grade}</b></span></p>
<p class="verdict">{verdict}</p>
<h3>Strengths</h3>
<ul>{strengths}</ul>
<h3>Areas to improve</h3>
<ul>{improvements}</ul>
"""


def _number_headings(html: str) -> str:
    """Give every heading an id, so its position on the page can be looked up after layout."""
    counter = iter(range(1, 10_000))
    return re.sub(r"<h([1-4])>", lambda m: f'<h{m.group(1)} id="h{next(counter)}">', html)


def _layout(html: str, break_before: set[str]) -> tuple[pymupdf.Document, list]:
    """Lay out the HTML into pages, starting a new page before each heading id in break_before."""
    for heading_id in break_before:
        html = html.replace(f'id="{heading_id}"', f'id="{heading_id}" style="page-break-before: always"', 1)
    positions = []
    story = pymupdf.Story(html=html, user_css=CSS)
    doc = story.write_with_links(lambda rect_number, filled: (PAGE, CONTENT, None), positionfn=positions.append)
    return doc, positions


def _stranded_heading(positions: list, already_moved: set[str]) -> str | None:
    """Return the id of the first heading left alone at the bottom of a page, if any."""
    for position in positions:
        heading_id = getattr(position, "id", "")
        top = position.rect[1]
        if heading_id and heading_id not in already_moved and top > CONTENT.y1 - KEEP_WITH_NEXT:
            return heading_id
    return None


def report_pdf(run: dict) -> bytes:
    """Build the PDF for one run. run needs topic, time, report and feedback."""
    html = _number_headings(f"""
<p class="brand">RESEARCHERS &#183; AI RESEARCH REPORT</p>
<p class="meta"><b>Topic:</b> {escape(run["topic"])}<br/><b>Generated:</b> {escape(run["time"])}</p>
<hr/>
{_to_html(run["report"])}
<hr/>
<h2>Critic review</h2>
{_critic_html(run["feedback"])}
""")

    # Lay out, then move any heading stranded at the bottom of a page to the next page and lay out again
    break_before: set[str] = set()
    doc, positions = _layout(html, break_before)
    for _ in range(10):
        stranded = _stranded_heading(positions, break_before)
        if not stranded:
            break
        break_before.add(stranded)
        doc.close()
        doc, positions = _layout(html, break_before)

    total = doc.page_count
    for number, page in enumerate(doc, start=1):
        page.insert_text((CONTENT.x0, FOOTER_Y), "Generated by Researchers", fontsize=8, fontname="helv", color=GREY)
        label = f"Page {number} of {total}"
        width = pymupdf.get_text_length(label, fontname="helv", fontsize=8)
        page.insert_text((CONTENT.x1 - width, FOOTER_Y), label, fontsize=8, fontname="helv", color=GREY)

    doc.set_metadata({"title": run["topic"], "author": "Researchers", "creator": "Researchers"})
    data = doc.tobytes(garbage=3, deflate=True)
    doc.close()
    return data
