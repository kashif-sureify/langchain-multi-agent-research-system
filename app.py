"""
Researchers: the Streamlit frontend for the multi-agent research pipeline.

Run with:  streamlit run app.py

This file only handles the UI. The research itself happens in the backend
(src/pipelines/pipelines.py), which the app calls through iter_research_pipeline().
Styling lives in ui/theme.py and the HTML building blocks in ui/components.py.
"""

import random
import re
import sys
import time
import uuid
from datetime import datetime

import streamlit as st

from src.topics.categories import CATEGORIES, CATEGORY_BY_NAME, Category
from ui import components as ui
from ui.theme import THEME_LABELS, theme_css

SAMPLES_SHOWN = 6  # how many sample topics appear at once
AVOID_LIMIT = 30  # how many already-shown ideas to send back to the model, so it suggests new ones
OTHERS = "Others"  # the last category button, where the user types their own category
TOPIC_LIMIT = 500  # longest question the topic box accepts (shown as "0 / 500")


# ──────────────────────────────────────────────────
# Backend
# ──────────────────────────────────────────────────

def load_backend():
    """Import the research pipeline, showing a clear fix on the page instead of a traceback if setup is wrong."""
    try:
        from src.pipelines import pipelines
    except KeyError as missing:
        st.error(
            f"Missing environment variable {missing}. "
            "Add it to the `.env` file in the project root, then restart the app."
        )
        st.stop()
    except ModuleNotFoundError as error:
        st.error(
            f"**Missing Python package `{error.name}`.**\n\n"
            f"Streamlit is running with `{sys.executable}`, which doesn't have this project's packages. "
            "This usually means another project's virtual environment is active in your terminal.\n\n"
            "Stop the app (Ctrl+C) and start it with this project's environment:\n\n"
            "```bash\n.venv/bin/streamlit run app.py\n```\n\n"
            "If you are already using this project's environment, install the packages with "
            "`pip install -r requirements.txt`."
        )
        st.stop()
    return pipelines


# ──────────────────────────────────────────────────
# Session state and callbacks
# ──────────────────────────────────────────────────

def init_state() -> None:
    ss = st.session_state
    if "theme" not in ss:
        requested = st.query_params.get("theme", "system")
        ss.theme = requested if requested in THEME_LABELS else "system"
        ss.theme_choice = ss.theme
    ss.setdefault("thread_id", str(uuid.uuid4()))  # one conversation per browser session
    ss.setdefault("runs", [])
    ss.setdefault("topic", "")
    ss.setdefault("sample_topics", starter_topics())  # shown while no category is picked
    ss.setdefault("ideas", {})  # category name -> the ideas on screen for it
    ss.setdefault("ideas_seen", {})  # category name -> every idea shown for it so far
    if ss.pop("clear_topic", False):  # set after a run, so the box is empty for a follow-up
        ss.topic = ""


def on_theme_change() -> None:
    choice = st.session_state.theme_choice
    if choice is None:  # clicking the selected option again clears it; keep the current theme
        st.session_state.theme_choice = st.session_state.theme
        return
    st.session_state.theme = choice
    st.query_params["theme"] = choice  # kept in the URL, so a page refresh remembers it


def on_sample_pick() -> None:
    if st.session_state.sample_pick:
        st.session_state.topic = st.session_state.sample_pick
    st.session_state.sample_pick = None


def on_more_ideas() -> None:
    ss = st.session_state
    if ss.get("category_pick") is None:  # no category: deal a new mix of saved examples
        ss.sample_topics = starter_topics(exclude=ss.sample_topics)
    else:  # a category: ask the model for new ideas on this run
        ss.refresh_ideas = True


# ──────────────────────────────────────────────────
# Sample topics
# ──────────────────────────────────────────────────

def starter_topics(exclude: list[str] | None = None) -> list[str]:
    """A mix of saved examples, one from each of several random categories. Instant, with no model call."""
    exclude = exclude or []
    picks = random.sample(CATEGORIES, min(SAMPLES_SHOWN, len(CATEGORIES)))
    topics = []
    for category in picks:
        fresh = [topic for topic in category.examples if topic not in exclude] or list(category.examples)
        topics.append(random.choice(fresh))
    return topics


def category_label(name: str) -> str:
    return ":material/auto_awesome: Others" if name == OTHERS else CATEGORY_BY_NAME[name].label


def picked_category() -> Category | None:
    """The category to show ideas for: a built-in one, the one typed under Others, or None for the starter mix."""
    ss = st.session_state
    name = ss.get("category_pick")
    if name != OTHERS:
        return CATEGORY_BY_NAME.get(name)
    typed = " ".join(ss.get("custom_category", "").split())
    if not typed:
        return None
    # A typed category has no saved examples, so the model works from its name alone
    return Category(name=typed, icon="auto_awesome", focus=f"anything related to {typed}", examples=())


def generate_ideas(category: Category) -> list[str]:
    """New ideas for a category from the model, falling back to the saved examples if the call fails."""
    seen = st.session_state.ideas_seen.setdefault(category.name.casefold(), [])
    try:
        with st.spinner(f"Finding {category.name} ideas…"):
            ideas = load_backend().suggest_topics(category, avoid=seen[-AVOID_LIMIT:], count=SAMPLES_SHOWN)
    except Exception as error:
        print(f"Topic ideas failed for {category.name}: {error}", file=sys.stderr)
        unseen = [topic for topic in category.examples if topic not in seen] or list(category.examples)
        if unseen:
            st.toast("Couldn't generate new ideas right now, so here are some saved examples.", icon=":material/warning:")
        else:  # a typed category has no saved examples to fall back on
            st.toast("Couldn't generate ideas right now. Please try again.", icon=":material/warning:")
        ideas = random.sample(unseen, min(SAMPLES_SHOWN, len(unseen)))
    seen.extend(ideas)
    return ideas


def current_sample_topics(category: Category | None) -> list[str]:
    """The topics to show: the starter mix, or the category's ideas (generated on first pick and on "More ideas")."""
    ss = st.session_state
    if category is None:
        return ss.sample_topics
    key = category.name.casefold()  # so typing "photography" or "Photography" shares the same ideas
    if key not in ss.ideas or ss.pop("refresh_ideas", False):
        ss.ideas[key] = generate_ideas(category)
    return ss.ideas[key]


def render_sample_topics(category: Category | None) -> None:
    """The sample topics as a grid of topic cards, under a header row with the Shuffle ideas button."""
    topics = current_sample_topics(category)
    with st.container(key="topics_head"):
        label_column, action_column = st.columns([3, 1], vertical_alignment="center")
        label_column.html(ui.field_label_html(f"{category.name} ideas" if category else "Try a sample topic", sparkle=bool(category)))
        action_column.button(
            "Shuffle ideas" if topics else "Try again",
            icon=":material/shuffle:",
            key="more_ideas",
            type="tertiary",
            on_click=on_more_ideas,
        )
    if topics:
        st.pills(
            "Sample topics",
            topics,
            key="sample_pick",
            on_change=on_sample_pick,
            label_visibility="collapsed",
            width="stretch",
        )
        if st.session_state.topic in topics:  # highlight the topic card that is in the text box now
            position = topics.index(st.session_state.topic) + 1
            st.html(
                f'<style>.st-key-sample_pick [role="radiogroup"] > button:nth-of-type({position}) '
                "{ background: var(--brand-soft) !important; border-color: var(--brand-primary) !important; }</style>"
            )
    else:
        st.caption(f"No ideas for {category.name} yet.")


def on_new_conversation() -> None:
    st.session_state.thread_id = str(uuid.uuid4())
    st.session_state.runs = []
    st.session_state.topic = ""


def on_improve(run_index: int) -> None:
    """ "Improve this report": main() picks this up and revises that run's report with the critic's feedback."""
    st.session_state.improve_request = run_index


# ──────────────────────────────────────────────────
# Layout
# ──────────────────────────────────────────────────

def draw_history(slot, runs: list[dict], pending_topic: str | None = None, pending_text: str = "Researching now…") -> None:
    """The sidebar's conversation list, or its empty state. pending_topic is the question being researched now."""
    if runs or pending_topic:
        slot.html(ui.history_html(runs, pending_topic, pending_text))
    else:
        slot.html(ui.conversation_empty_html())


def render_sidebar():
    """The sidebar. Returns the conversation list's placeholder, so a live run can add its question to it."""
    runs = st.session_state.runs
    with st.sidebar:
        st.html(ui.sidebar_brand_html())

        st.html(ui.side_label_html("Appearance"))
        st.segmented_control(
            "Theme",
            options=list(THEME_LABELS),
            format_func=THEME_LABELS.get,
            key="theme_choice",
            on_change=on_theme_change,
            label_visibility="collapsed",
            width="stretch",
        )

        st.html(ui.side_label_html("Conversation"))
        history = st.empty()
        draw_history(history, runs)
        st.button("New conversation", icon=":material/add:", on_click=on_new_conversation, disabled=not runs, width="stretch")

        st.html(ui.side_label_html("How it works"))
        st.html(ui.how_it_works_html())

        with st.container(key="side_footer"):
            st.html(ui.sidebar_footer_html())
    return history


def render_input():
    """
    The query card: topic box, categories, sample topics and the start button.
    Returns (clicked, start_slot); start_slot holds the button, so it can show "Researching…" during a run.
    """
    has_runs = bool(st.session_state.runs)
    with st.container(key="input_card"):
        st.text_area(
            "Ask a follow-up, or research something new" if has_runs else "What would you like to research?",
            key="topic",
            height=132,
            max_chars=TOPIC_LIMIT,
            placeholder="Write your research topic here or pick a category below",
        )
        st.html(ui.input_footer_html(len(st.session_state.topic), TOPIC_LIMIT))

        st.pills(
            "Explore by category",
            [*CATEGORY_BY_NAME, OTHERS],
            format_func=category_label,
            key="category_pick",
        )
        typing_own = st.session_state.category_pick == OTHERS
        if typing_own:
            # A form, so the category is only sent when the button is clicked (or Enter is pressed)
            with st.form("custom_category_form", border=False):
                field, submit = st.columns([3, 1.25], vertical_alignment="bottom")
                field.text_input(
                    "Your category",
                    key="custom_category",
                    max_chars=60,
                    placeholder="e.g. Photography, Formula 1, Ancient Rome",
                )
                asked = submit.form_submit_button("Get sample prompts", icon=":material/auto_awesome:", width="stretch")
            if asked and not st.session_state.custom_category.strip():
                st.caption("Type a category first, then click Get sample prompts.")
            else:
                st.html(ui.category_hint_html())
        category = picked_category()
        if category or not typing_own:  # under Others, wait until a category has been typed
            render_sample_topics(category)

        with st.container(key="start_row", horizontal=True, vertical_alignment="center", gap="medium"):
            start_slot = st.empty()
            clicked = start_slot.button(
                "Start research :material/arrow_forward:", icon=":material/auto_awesome:", type="primary"
            )
            if has_runs:
                st.html(ui.start_hint_html("Follow-ups remember this conversation. Try “go deeper on the second finding”.", "history"))
            else:
                st.html(ui.start_hint_html("Takes about 1–2 minutes. You'll see each agent's progress live below."))
    return clicked, start_slot


def plural(count: int, word: str) -> str:
    return f"{count} {word}{'' if count == 1 else 's'}"


def trail_label(step: str, run: dict) -> tuple[str, str]:
    """The (label, icon) of a step's output expander, with a count badge such as "6 sources"."""
    if step == "search":
        count = ui.count_sources(run["search_results"])
        badge = f" :gray-badge[{plural(count, 'source')}]" if count else ""
        return f"Step 1 · Sources found{badge}", ":material/search:"
    if step == "reader":
        count = ui.count_facts(run["scraped_content"])
        badge = f" :gray-badge[{plural(count, 'fact')}]" if count else ""
        return f"Step 2 · Reader Agent: notes from the sources{badge}", ":material/menu_book:"
    minutes = ui.read_minutes(run["report"])
    return f"Step 3 · Report draft :gray-badge[{minutes} min read]", ":material/edit_note:"


def trail_body(step: str, run: dict) -> str:
    return {"search": run.get("search_results"), "reader": run.get("scraped_content")}.get(step) or ui.normalize_markdown(run["report"])


def run_live(topic: str, history_slot, improve: dict | None = None) -> bool:
    """
    Run the pipeline, updating the agent cards and live status as each agent finishes. Returns True on success.
    With improve (an earlier run), the agents revise that run's report using its critic review instead of starting over.
    """
    backend = load_backend()
    statuses = ["waiting"] * len(ui.STEPS)
    number = len(st.session_state.runs) + 1
    revision = improve.get("revision", 0) + 1 if improve else 0
    started = time.monotonic()
    draw_history(history_slot, st.session_state.runs, topic, "Improving now…" if improve else "Researching now…")

    header = st.empty()
    tracker = st.empty()
    live = st.container()
    status_line = st.empty()

    def draw(state: str = "running") -> None:
        header.html(ui.run_header_html(topic, number, state, time.monotonic() - started, revision))
        tracker.html(ui.tracker_html(statuses))

    if improve:
        steps = backend.iter_revision_pipeline(improve, thread_id=st.session_state.thread_id)
    else:
        steps = backend.iter_research_pipeline(topic, thread_id=st.session_state.thread_id)
    state = {}
    for index, step in enumerate(ui.STEPS):
        statuses[index] = "running"
        draw()
        status_line.html(ui.live_status_html(index, ui.REVISION_STATUS[step["key"]] if improve else step["running"]))
        try:
            _, state = next(steps)
        except Exception as error:
            statuses[index] = "failed"
            draw("failed")
            status_line.empty()
            draw_history(history_slot, st.session_state.runs)
            live.error(f"**{step['name']} failed:** {error}")
            return False

        statuses[index] = "done"
        draw()
        if step["key"] != "critic":
            label, icon = trail_label(step["key"], state)
            with live.expander(label, icon=icon):
                st.markdown(trail_body(step["key"], state))
    status_line.empty()

    run = {
        "topic": topic,
        "time": datetime.now().strftime("%b %d, %Y · %H:%M"),
        "duration": time.monotonic() - started,  # shown as "Completed · 1m 38s"
        "search_results": state["search_results"],
        "scraped_content": state["scraped_content"],
        "report": state["report"],
        "feedback": state["feedback"],
    }
    if improve:
        previous_review = ui.parse_critic(improve["feedback"])
        run["revision"] = revision
        run["previous_score"] = previous_review["score"] if previous_review else None
    st.session_state.runs.append(run)
    if not improve:  # an improvement doesn't use the topic box, so leave whatever is typed there
        st.session_state.clear_topic = True
    return True


def report_markdown(run: dict) -> str:
    return f"{run['report']}\n\n---\n\n## Critic review\n\n{run['feedback']}\n"


def report_filename(topic: str, extension: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", topic.lower()).strip("-")[:60]
    return f"{slug or 'research-report'}.{extension}"


@st.cache_data(show_spinner=False, max_entries=32)
def build_pdf(topic: str, time: str, report: str, feedback: str) -> bytes:
    """Build the report PDF once per run; Streamlit reruns reuse the cached bytes."""
    from ui.pdf import report_pdf  # imported here so the rest of the app still works without PyMuPDF

    return report_pdf({"topic": topic, "time": time, "report": report, "feedback": feedback})


def render_downloads(run: dict, key: str) -> None:
    """Download buttons for a report: PDF and Markdown, side by side on the right. Both include the critic review."""
    with st.container(horizontal=True, horizontal_alignment="right", gap="small"):
        try:
            pdf = build_pdf(run["topic"], run["time"], run["report"], run["feedback"])
        except Exception as error:  # e.g. PyMuPDF not installed
            st.button(
                "PDF unavailable", icon=":material/download:", key=f"pdf_{key}", disabled=True,
                help=f"Couldn't create the PDF: {error}",
            )
        else:
            st.download_button(
                "Download PDF",
                data=pdf,
                file_name=report_filename(run["topic"], "pdf"),
                mime="application/pdf",
                type="primary",
                icon=":material/download:",
                key=f"pdf_{key}",
            )
        st.download_button(
            "Markdown",
            data=report_markdown(run),
            file_name=report_filename(run["topic"], "md"),
            mime="text/markdown",
            icon=":material/description:",
            key=f"md_{key}",
        )


def render_report(run: dict, key: str) -> None:
    """The report as a reading card: kicker and title, summary callout, body, and a numbered sources list."""
    parts = ui.split_report(run["report"])
    sources = ui.parse_sources(parts["sources"])
    with st.container(key=f"report_card_{key}"):
        st.html(ui.report_head_html(parts["title"] or run["topic"], len(sources), ui.read_minutes(run["report"])))
        if parts["summary"]:
            with st.container(key=f"report_summary_{key}"):
                st.html(ui.summary_label_html())
                st.markdown(ui.mark_citations(parts["summary"]))
        if parts["body"]:
            st.markdown(ui.mark_citations(parts["body"]))
        if sources:
            st.html(ui.sources_html(sources))


def render_critic(run: dict, card_key: str) -> None:
    review = ui.parse_critic(run["feedback"])
    if review:
        st.html(ui.critic_html(review, ui.count_sources(run["search_results"]), run.get("previous_score")))
    else:  # the critic didn't follow the expected format; show its reply as-is
        with st.container(key=card_key):
            st.markdown(run["feedback"])


IMPROVE_BELOW = 9  # offer "Improve this report" only below this score; revising a 9-10 report rarely raises it


def render_improve(run: dict, number: int) -> None:
    """The "Improve this report" button under the critic review, for reports that scored below IMPROVE_BELOW."""
    review = ui.parse_critic(run["feedback"])
    if review and review["score"] >= IMPROVE_BELOW:
        return
    with st.container(key="improve_row", horizontal=True, vertical_alignment="center", gap="medium"):
        st.button(
            "Improve this report", icon=":material/auto_fix_high:", type="primary",
            key=f"improve_{number}", on_click=on_improve, args=(number - 1,),
        )
        st.html(ui.improve_hint_html())


def render_run(run: dict, number: int) -> None:
    """The full view of one finished run: header, agent cards, research trail, report and critic review."""
    st.html(ui.run_header_html(run["topic"], number, "done", run.get("duration", 0), run.get("revision", 0)))
    st.html(ui.tracker_html(["done"] * len(ui.STEPS)))

    st.html(ui.section_head_html("Research trail", "Steps 1 & 2"))
    for step in ("search", "reader"):
        label, icon = trail_label(step, run)
        with st.expander(label, icon=icon):
            st.markdown(trail_body(step, run))

    with st.container(key=f"report_header_{number}"):
        title_column, buttons_column = st.columns([1.3, 1], vertical_alignment="bottom")
        title_column.html(ui.section_head_html("Final report", "Step 3 · Writer"))
        with buttons_column:
            render_downloads(run, key=f"latest_{number}")
    render_report(run, key=f"latest_{number}")

    st.html(ui.section_head_html("Critic review", "Step 4 · Critic"))
    render_critic(run, card_key=f"critic_raw_{number}")
    render_improve(run, number)


def render_earlier(runs: list[dict]) -> None:
    """Earlier questions in this conversation, newest first, each collapsed into an expander."""
    st.html(ui.section_head_html("Earlier in this conversation"))
    for index in reversed(range(len(runs) - 1)):
        run = runs[index]
        revision = f" (revision {run['revision']})" if run.get("revision") else ""
        with st.expander(f"Q{index + 1} · {run['topic']}{revision}  ·  {run['time']}", icon=":material/history:"):
            report_tab, critic_tab, sources_tab, notes_tab = st.tabs([
                ":material/description: Report", ":material/rate_review: Critic review",
                ":material/search: Sources", ":material/menu_book: Notes",
            ])
            with report_tab:
                render_downloads(run, key=f"earlier_{index}")
                render_report(run, key=f"earlier_{index}")
            with critic_tab:
                render_critic(run, card_key=f"critic_raw_earlier_{index}")
            with sources_tab:
                st.markdown(run["search_results"])
            with notes_tab:
                st.markdown(run["scraped_content"])


def render_results() -> None:
    runs = st.session_state.runs
    if not runs:
        st.html(ui.section_head_html(
            "The research pipeline", "4 agents", "Each agent hands its work to the next. You can watch every step live."
        ))
        st.html(ui.tracker_html(["waiting"] * len(ui.STEPS)))
        st.html(ui.empty_state_html())
        return
    render_run(runs[-1], number=len(runs))
    if len(runs) > 1:
        render_earlier(runs)


def main() -> None:
    st.set_page_config(page_title="Researchers", page_icon=":material/biotech:", layout="wide", initial_sidebar_state="expanded")
    init_state()
    st.html(theme_css(st.session_state.theme))
    history_slot = render_sidebar()

    st.html(ui.hero_html())
    load_backend()  # check the setup on page load, so problems show before anyone clicks Start research
    start, start_slot = render_input()
    improve_index = st.session_state.pop("improve_request", None)

    if start:
        topic = st.session_state.topic.strip()
        if not topic:
            st.warning("Please enter a topic to research, or pick one of the samples.")
        else:
            start_slot.button("Researching…", icon=":material/progress_activity:", type="primary", disabled=True)
            if run_live(topic, history_slot):
                st.rerun()  # redraw with the finished run in the results view
            else:
                return  # keep the error on screen
    elif improve_index is not None and improve_index < len(st.session_state.runs):
        previous = st.session_state.runs[improve_index]
        start_slot.button("Improving report…", icon=":material/progress_activity:", type="primary", disabled=True)
        if run_live(previous["topic"], history_slot, improve=previous):
            st.rerun()
        else:
            return

    render_results()


if __name__ == "__main__":
    main()
