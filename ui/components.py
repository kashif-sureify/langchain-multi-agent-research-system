"""
HTML building blocks for the Researchers UI. Everything here returns an HTML string for st.html(),
plus a few helpers that prepare report text for display.
Text that comes from the user or the model is escaped before it goes into HTML.
"""

import math
import re
from datetime import datetime
from html import escape

from src.utils.markdown import normalize_markdown
from ui.icons import icon

# The four pipeline steps, in order. "key" matches the step names yielded by
# src.pipelines.pipelines.iter_research_pipeline().
STEPS = [
    {
        "key": "search", "icon": "search", "name": "Search Agent",
        "desc": "Searches the web for recent, reliable sources",
        "running": "Search Agent is searching the web for sources…",
    },
    {
        "key": "reader", "icon": "book-open", "name": "Reader Agent",
        "desc": "Reads the best pages and extracts the key facts",
        "running": "Reader Agent is reading the sources…",
    },
    {
        "key": "writer", "icon": "pen-line", "name": "Writer",
        "desc": "Writes a structured, cited research report",
        "running": "Writer is drafting the report…",
    },
    {
        "key": "critic", "icon": "shield-check", "name": "Critic",
        "desc": "Reviews the report against the research",
        "running": "Critic is reviewing the report…",
    },
]

# Live status lines while "Improve this report" runs (src.pipelines.pipelines.iter_revision_pipeline)
REVISION_STATUS = {
    "search": "Search Agent is looking for sources to fill the gaps…",
    "reader": "Reader Agent is reading the new sources…",
    "writer": "Writer is revising the report with the critic's feedback…",
    "critic": "Critic is re-scoring the revised report…",
}

_SPINNER = '<span class="rs-spinner" aria-hidden="true"></span>'


# ──────────────────────────────────────────────────
# Hero and section headings
# ──────────────────────────────────────────────────

_FEATURES = [
    ("globe", "Live web search"),
    ("book-open", "Source reading"),
    ("file-text", "Cited reports"),
    ("shield-check", "Built-in review"),
    ("history", "Remembers follow-ups"),
]


def hero_html() -> str:
    pills = "".join(f'<span class="rs-feature">{icon(name, 15)}{label}</span>' for name, label in _FEATURES)
    return f"""
<section class="rs-hero">
  <span class="rs-eyebrow">Your AI research team</span>
  <h1 class="rs-headline">Ask anything. Get a <em>cited report.</em></h1>
  <p class="rs-subtitle">Four AI agents search the web, read the best sources, write a structured report
  with citations and review it for accuracy, in about a minute or two.</p>
  <div class="rs-features">{pills}</div>
</section>
"""


def section_head_html(title: str, tag: str = "", subtitle: str = "") -> str:
    """A section title in the display font, with an optional mono tag pill and a one-line subtitle."""
    tag_html = f'<span class="rs-tag">{escape(tag)}</span>' if tag else ""
    subtitle_html = f'<p class="rs-section-sub">{escape(subtitle)}</p>' if subtitle else ""
    return f'<div class="rs-section"><div class="rs-section-row"><h2>{escape(title)}</h2>{tag_html}</div>{subtitle_html}</div>'


def field_label_html(text: str, sparkle: bool = False) -> str:
    """A widget-style label, used where the label sits in a row with a button (the sample topics header)."""
    mark = icon("sparkles", 14, "rs-accent-icon") if sparkle else ""
    return f'<div class="rs-field-label">{mark}{escape(text)}</div>'


def start_hint_html(text: str, icon_name: str = "clock") -> str:
    return f'<div class="rs-hint">{icon(icon_name, 15)}<span>{escape(text)}</span></div>'


def input_footer_html(length: int, limit: int) -> str:
    return (
        '<div class="rs-input-footer"><span>Be specific: a focused question gets a sharper report.</span>'
        f'<span class="rs-mono">{length} / {limit}</span></div>'
    )


def category_hint_html() -> str:
    return '<div class="rs-help">Any subject works, from Photography to Formula 1. The model suggests topics for it.</div>'


# ──────────────────────────────────────────────────
# Pipeline: agent cards, run header, live status
# ──────────────────────────────────────────────────

_STATUS_PILL = {
    "waiting": ("", "Waiting"),
    "running": (_SPINNER, "Running"),
    "done": (icon("check", 12), "Done"),
    "failed": (icon("x", 12), "Failed"),
}


def tracker_html(statuses: list[str]) -> str:
    """The four agents as cards joined by arrows. statuses: one of waiting/running/done/failed per step."""
    parts = []
    for number, (step, status) in enumerate(zip(STEPS, statuses), start=1):
        mark, text = _STATUS_PILL[status]
        if number > 1:
            parts.append(f'<div class="rs-connector">{icon("arrow-right", 16)}</div>')
        parts.append(f"""
<div class="rs-agent rs-agent--{status}">
  <div class="rs-agent-top">
    <span class="rs-agent-icon">{icon(step["icon"], 20)}</span>
    <span class="rs-pill rs-pill--{status}">{mark}{text}</span>
  </div>
  <div class="rs-mono rs-agent-step">Step 0{number}</div>
  <div class="rs-agent-name">{step["name"]}</div>
  <div class="rs-agent-desc">{step["desc"]}</div>
  <div class="rs-progress"><span></span></div>
</div>""")
    return f'<div class="rs-agents">{"".join(parts)}</div>'


def format_duration(seconds: float) -> str:
    seconds = int(round(seconds))
    minutes, secs = divmod(seconds, 60)
    return f"{minutes}m {secs:02d}s" if minutes else f"{secs}s"


def run_header_html(topic: str, number: int, state: str, elapsed: float = 0.0, revision: int = 0) -> str:
    """
    The query as a title with a status pill. state: running, done or failed.
    While running, the m:ss timer ticks in CSS, starting from elapsed seconds, so it stays live between redraws.
    revision is how many times the report has been improved (0 for a fresh report).
    """
    kicker = "Latest research" if number == 1 else f"Question {number} · latest research"
    if revision:
        kicker = f"Revision {revision} · improved report"
    if state == "running":
        delay = f"-{elapsed:.0f}s"
        pill = (f'<span class="rs-run-status rs-run-status--running">{_SPINNER}Running · '
                f'<span class="rs-timer" style="animation-delay: {delay}, {delay};"></span></span>')
    elif state == "done":
        done_text = f"Completed · {format_duration(elapsed)}" if elapsed else "Completed"
        pill = f'<span class="rs-run-status rs-run-status--done">{icon("check", 14)}{done_text}</span>'
    else:
        pill = f'<span class="rs-run-status rs-run-status--failed">{icon("x", 14)}Stopped</span>'
    return f"""
<div class="rs-run-head">
  <div class="rs-run-title">
    <div class="rs-mono rs-run-kicker">{escape(kicker)}</div>
    <h2>{escape(topic)}</h2>
  </div>
  {pill}
</div>
"""


def live_status_html(step_index: int, text: str) -> str:
    return (
        f'<div class="rs-live">{_SPINNER}<span class="rs-live-text">{escape(text)}</span>'
        f'<span class="rs-mono">Step {step_index + 1} of {len(STEPS)}</span></div>'
    )


def empty_state_html() -> str:
    return f"""
<div class="rs-empty">
  <div class="rs-empty-icon">{icon("compass", 26)}</div>
  <h3>Ready when you are</h3>
  <p>Type a topic above or pick a sample, then press <b>Start research</b>. The pipeline takes about a minute or two.</p>
</div>
"""


# ──────────────────────────────────────────────────
# Sidebar
# ──────────────────────────────────────────────────

def sidebar_brand_html() -> str:
    return f"""
<div class="rs-brand">
  <div class="rs-brand-tile">{icon("microscope", 22)}</div>
  <div><div class="rs-brand-name">Researchers</div><div class="rs-brand-sub">Multi-agent AI research assistant</div></div>
</div>
"""


def side_label_html(text: str) -> str:
    return f'<div class="rs-side-label rs-mono">{escape(text)}</div>'


def conversation_empty_html() -> str:
    return f"""
<div class="rs-convo-empty">
  {icon("message-square", 18)}
  <div><b>No questions yet</b><span>Follow-up questions will remember earlier answers.</span></div>
</div>
"""


def time_ago(time_label: str) -> str:
    """'Just now', '5 min ago', '2 h ago' or the date, from a run's "Nov 15, 2026 · 14:05" time label."""
    try:
        then = datetime.strptime(time_label, "%b %d, %Y · %H:%M")
    except ValueError:
        return time_label
    minutes = (datetime.now() - then).total_seconds() / 60
    if minutes < 2:
        return "Just now"
    if minutes < 60:
        return f"{int(minutes)} min ago"
    if minutes < 24 * 60:
        return f"{int(minutes // 60)} h ago"
    return then.strftime("%b %d")


def history_html(runs: list[dict], pending_topic: str | None = None, pending_text: str = "Researching now…") -> str:
    """The questions asked so far, as numbered cards. pending_topic is the question being researched right now."""
    items = []
    for number, run in enumerate(runs, start=1):
        review = parse_critic(run["feedback"])
        revision = f"Revision {run['revision']} · " if run.get("revision") else ""
        meta = revision + time_ago(run["time"]) + (f" · scored {review['score']:g}/10" if review else "")
        items.append((number, run["topic"], meta, ""))
    if pending_topic:
        items.append((len(runs) + 1, pending_topic, pending_text, " rs-history-meta--running"))
    cards = "".join(
        f'<div class="rs-history-item"><span class="rs-history-num">{number}</span>'
        f'<div><div class="rs-history-q">{escape(topic)}</div>'
        f'<div class="rs-mono rs-history-meta{extra}">{escape(meta)}</div></div></div>'
        for number, topic, meta, extra in items
    )
    return f'<div class="rs-history">{cards}</div>'


def how_it_works_html() -> str:
    items = "".join(
        f'<div class="rs-flow-item"><span class="rs-flow-num">{number}</span>'
        f'<div><b>{s["name"]}</b><span>{s["desc"]}</span></div></div>'
        for number, s in enumerate(STEPS, start=1)
    )
    return f'<div class="rs-flow">{items}</div>'


def sidebar_footer_html() -> str:
    return '<div class="rs-side-footer">Built by <b>Kashif</b></div>'


# ──────────────────────────────────────────────────
# Research trail counts
# ──────────────────────────────────────────────────

def count_sources(search_results: str) -> int:
    """How many sources the Search Agent listed (its "URL:" lines)."""
    return len(re.findall(r"^\s*URL:\s*\S+", search_results, flags=re.MULTILINE))


def count_facts(scraped_content: str) -> int:
    """
    How many facts the Reader Agent extracted: its bullet points, not counting the "Failed Sources" lists.
    A revised report's notes hold several rounds of reading, each with its own failed-sources list.
    """
    count, in_failed_list = 0, False
    for line in scraped_content.splitlines():
        line = line.strip()
        if re.match(r"Failed Sources\s*:?", line, flags=re.IGNORECASE):
            in_failed_list = True
        elif re.match(r"(?:Source\s*:|Additional notes)", line, flags=re.IGNORECASE):
            in_failed_list = False
        elif not in_failed_list and re.match(r"[-*•]\s+\S", line):
            count += 1
    return count


def improve_hint_html() -> str:
    return '<div class="rs-hint">Finds what the critic said was missing, revises this report and scores it again.</div>'


# ──────────────────────────────────────────────────
# Final report
# ──────────────────────────────────────────────────

_SUMMARY_NAMES = re.compile(r"^(?:executive\s+)?summary|^tl;?dr|^overview$", re.IGNORECASE)
_SOURCE_NAMES = re.compile(r"^(?:sources|references|bibliography|works cited)\b", re.IGNORECASE)


def split_report(report: str) -> dict:
    """
    Split a report into title, summary, body and sources for display.
    The writer is asked for: # Title, ## Summary, ## Introduction ... ## Conclusion, ## Sources.
    Anything that doesn't fit stays in the body, so nothing is ever dropped.
    """
    lines = normalize_markdown(report).splitlines()
    title = ""
    for index, line in enumerate(lines):
        if line.startswith("# "):
            title = line[2:].strip()
            del lines[index]
            break

    preamble, sections, current = [], [], None
    for line in lines:
        if line.startswith("## "):
            current = [line[3:].strip(), []]
            sections.append(current)
        elif current is None:
            preamble.append(line)
        else:
            current[1].append(line)

    summary, sources, body = "", "", ["\n".join(preamble).strip()]
    for heading, content in sections:
        text = "\n".join(content).strip()
        if not summary and _SUMMARY_NAMES.match(heading):
            summary = text
        elif not sources and _SOURCE_NAMES.match(heading):
            sources = text
        else:
            body.append(f"## {heading}\n\n{text}")
    return {"title": title, "summary": summary, "body": "\n\n".join(part for part in body if part), "sources": sources}


_CITATION = re.compile(r"(?<![\w:])\[(\d{1,3}(?:\s*[,–-]\s*\d{1,3})*)\](?![(:])")


def mark_citations(markdown: str) -> str:
    """
    Wrap citation markers like [1], [2, 3] or [1][5] in Streamlit's colored-text syntax; CSS gives them the brand color.
    Markdown links "[text](url)" and reference definitions "[1]: url" are left alone.
    """
    return _CITATION.sub(r":blue[[\1]]", markdown)


_LINK = re.compile(r"\[([^\]]+)\]\((https?://[^)\s]+)\)")
_URL = re.compile(r"https?://[^\s<>()\[\]]*[^\s<>()\[\].,;:!?'\"]")


def parse_sources(sources: str) -> list[dict]:
    """Turn the Sources section ("[1] Title - URL" lines, or Markdown links) into numbered entries."""
    entries = []
    for line in sources.splitlines():
        line = line.strip()
        if not line:
            continue
        # An optional bullet or "3." list number, then an optional "[3]" citation number
        prefix = re.match(r"^(?:[-*•]\s*)?(?:(\d+)[.)]\s*)?(?:\[(\d+)\][.):]?\s*)?", line)
        number = prefix.group(2) or prefix.group(1)
        rest = line[prefix.end():]
        link = _LINK.search(rest)
        if link:
            title, url = link.group(1), link.group(2)
        else:
            url_match = _URL.search(rest)
            url = url_match.group(0) if url_match else ""
            title = rest
            if url_match:  # the title is the text before the URL, or after it if nothing comes before
                before, after = rest[: url_match.start()], rest[url_match.end():]
                title = before if before.strip(" -–—:|·.(") else after
            title = re.sub(r"^[\s\-–—:|·.)]+|[\s\-–—:|·.(]+$", "", title).strip(" *_\"'")
        entries.append({"number": number or str(len(entries) + 1), "title": title or url, "url": url})
    return entries


def read_minutes(text: str) -> int:
    return max(1, math.ceil(len(text.split()) / 220))


def report_head_html(title: str, n_sources: int, minutes: int) -> str:
    sources = f"{n_sources} source{'s' if n_sources != 1 else ''}"
    return (f'<div class="rs-mono rs-report-kicker">Research report · {sources} · {minutes} min read</div>'
            f'<h1 class="rs-report-title">{escape(title)}</h1>')


def summary_label_html() -> str:
    return '<div class="rs-mono rs-summary-label">Summary</div>'


def sources_html(entries: list[dict]) -> str:
    items = []
    for entry in entries:
        url = entry["url"]
        link = ""
        if url:
            shown = re.sub(r"^https?://(www\.)?", "", url).rstrip("/")
            shown = shown if len(shown) <= 70 else shown[:69] + "…"
            link = (f'<a href="{escape(url, quote=True)}" target="_blank" rel="noopener noreferrer">'
                    f'{escape(shown)}{icon("external-link", 13)}</a>')
        items.append(f'<li><span class="rs-source-num rs-mono">{escape(entry["number"])}</span>'
                     f'<div><b>{escape(entry["title"])}</b>{link}</div></li>')
    return f'<h2 class="rs-sources-title">Sources</h2><ol class="rs-sources">{"".join(items)}</ol>'


# ──────────────────────────────────────────────────
# Critic review
# ──────────────────────────────────────────────────

_SECTION_NAMES = r"(?:Strengths|Areas to Improve|One line verdict)"


def _section(text: str, name: str) -> str:
    """Return the body of a 'Name:' section, up to the next known section or the end."""
    match = re.search(
        rf"^\s*{name}\s*:?\s*$(.*?)(?=^\s*{_SECTION_NAMES}\s*:?\s*$|\Z)",
        text, flags=re.IGNORECASE | re.MULTILINE | re.DOTALL,
    )
    return match.group(1).strip() if match else ""


def _bullets(block: str) -> list[str]:
    items = []
    for line in block.splitlines():
        line = line.strip()
        if not line:
            continue
        line = re.sub(r"^(?:[-*•]|\d+[.)])\s*", "", line)
        if line and line != "...":
            items.append(line)
    return items


def parse_critic(feedback: str) -> dict | None:
    """
    Split the Critic's reply (Score / Strengths / Areas to Improve / One line verdict)
    into parts. Returns None if the reply doesn't follow that format, so the UI can
    fall back to showing it as plain text.
    """
    # Drop markdown decoration the model sometimes adds: **bold**, ### headings
    text = feedback.replace("**", "")
    text = re.sub(r"^\s*#{1,6}\s*", "", text, flags=re.MULTILINE)

    score_match = re.search(r"Score\s*:\s*(\d+(?:\.\d+)?)\s*/\s*10", text, flags=re.IGNORECASE)
    strengths = _bullets(_section(text, "Strengths"))
    improvements = _bullets(_section(text, "Areas to Improve"))
    verdict = " ".join(_bullets(_section(text, "One line verdict")))

    if not score_match or not (strengths or improvements):
        return None
    return {
        "score": min(float(score_match.group(1)), 10.0),
        "strengths": strengths,
        "improvements": improvements,
        "verdict": verdict,
    }


def score_grade(score: float) -> tuple[str, str]:
    """Return (grade label, level) for a critic score. level is success, warning or danger. Also used by the PDF."""
    if score >= 8:
        return "Strong report", "success"
    if score >= 6:
        return "Good, with gaps", "warning"
    return "Needs work", "danger"


def score_change_html(score: float, previous_score: float | None) -> str:
    """A chip comparing a revised report's score with the score before the revision."""
    if previous_score is None:
        return ""
    change = score - previous_score
    if change > 0:
        return f'<span class="rs-delta rs-delta--up">{icon("trending-up", 14)}+{change:g} from {previous_score:g}/10</span>'
    if change < 0:
        return f'<span class="rs-delta rs-delta--down">{icon("trending-down", 14)}{change:g} from {previous_score:g}/10</span>'
    return f'<span class="rs-delta">Same as before ({previous_score:g}/10)</span>'


def critic_html(review: dict, n_sources: int, previous_score: float | None = None) -> str:
    score = review["score"]
    grade, _ = score_grade(score)
    good = score >= 6  # the ring and badge turn amber below 6/10
    tone = "done" if good else "running"

    def bullet_list(items: list[str]) -> str:
        return "".join(f"<li>{escape(item)}</li>" for item in items) or "<li>None listed</li>"

    verdict = escape(review["verdict"]) or "No verdict given."
    checked = f"Checked against {n_sources} source{'s' if n_sources != 1 else ''}" if n_sources else ""
    return f"""
<div class="rs-critic">
  <div class="rs-critic-head">
    <div class="rs-ring rs-ring--{tone}" style="--pct: {score * 10:.0f};">
      <div class="rs-ring-value">{score:g}<small>/10</small></div>
    </div>
    <div class="rs-critic-verdict">
      <div class="rs-mono rs-label">Critic's verdict</div>
      <p class="rs-verdict">{verdict}</p>
      <div class="rs-critic-meta">
        <span class="rs-grade rs-grade--{tone}">{icon("check" if good else "alert-triangle", 13)}{grade}</span>
        {score_change_html(score, previous_score)}
        <span class="rs-checked">{checked}</span>
      </div>
    </div>
  </div>
  <div class="rs-critic-cols">
    <div class="rs-col rs-col--good"><h4>{icon("check", 16)}Strengths</h4><ul>{bullet_list(review["strengths"])}</ul></div>
    <div class="rs-col rs-col--improve"><h4>{icon("wrench", 16)}Areas to improve</h4><ul>{bullet_list(review["improvements"])}</ul></div>
  </div>
</div>
"""
