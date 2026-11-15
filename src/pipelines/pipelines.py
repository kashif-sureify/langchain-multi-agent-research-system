from collections.abc import Iterator

from src.agents.agents import (
    build_search_agent,
    build_reader_agent,
    writer_chain,
    reviser_chain,
    critic_chain,
    topic_ideas_chain,
)
from src.topics.categories import Category
from src.utils.markdown import normalize_markdown
from datetime import date
import re
import uuid


def _failed_urls(scraped_content: str) -> set[str]:
    """URLs the Reader agent listed under "Failed Sources" (pages it couldn't open), across every round of reading."""
    urls, in_failed_list = set(), False
    for line in scraped_content.splitlines():
        line = line.strip()
        if re.match(r"Failed Sources\s*:?", line, flags=re.IGNORECASE):
            in_failed_list = True
        elif re.match(r"(?:Source\s*:|Additional notes)", line, flags=re.IGNORECASE):
            in_failed_list = False
        elif in_failed_list:
            urls.update(url.rstrip(".:,;") for url in re.findall(r"https?://[^\s)\]]+", line))
    return urls


def _research_text(search_results: str, scraped_content: str) -> str:
    """
    The research the Writer, Reviser and Critic see: the search results without the sources the Reader
    couldn't open, plus the Reader's notes. Those sources can't be checked, so the Writer is told never
    to cite them; leaving them out here makes sure it can't, which otherwise costs the report points.
    """
    failed = _failed_urls(scraped_content)
    if failed:
        # Search results are numbered blocks ("1. Title / URL: ... / Summary: ..."), then "Coverage Gaps"
        sources, gaps_heading, gaps = search_results.partition("Coverage Gaps")
        blocks = re.split(r"(?m)^(?=\s*\d+\.\s)", sources)
        sources = "".join(block for block in blocks if not any(url in block for url in failed))
        search_results = sources + gaps_heading + gaps
    return f"Search results:\n{search_results}\n\nScraped content:\n{scraped_content}"


def iter_research_pipeline(topic: str, thread_id: str | None = None) -> Iterator[tuple[str, dict]]:
    """
    Run the research pipeline one step at a time, yielding (step, state) after each step finishes.

    step is "search", "reader", "writer" or "critic". state holds every output produced so far:
    thread_id, search_results, scraped_content, report and feedback.
    The Streamlit UI uses this to show live progress; run_research_pipeline() uses it for the CLI.

    Pass the same thread_id on later calls to continue the same conversation,
    so the agents remember earlier topics and can handle follow-up questions.
    """
    thread_id = thread_id or str(uuid.uuid4())
    state = {"thread_id": thread_id}

    # Both agents share one checkpointer, so each gets its own thread inside the
    # conversation. Otherwise the reader would load the search agent's history.
    search_config = {"configurable": {"thread_id": f"{thread_id}-search"}}
    reader_config = {"configurable": {"thread_id": f"{thread_id}-reader"}}

    # Step 1: Search agent
    # Agents take {"messages": [...]}. The fixed instructions are already in the agent's system_prompt.
    search_agent = build_search_agent()

    search_response = search_agent.invoke(
        {"messages": [{"role": "user", "content": f"Topic: {topic}"}]},
        config=search_config,
    )

    # .text gives the plain string; with Gemini, .content is a list of content blocks
    state["search_results"] = search_response["messages"][-1].text
    yield "search", state

    # Step 2: Reader agent
    # Pass the full search results; truncating them cuts off the URLs the reader needs.
    reader_agent = build_reader_agent()

    reader_response = reader_agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": f"Topic: {topic}\n\nSearch Results:\n{state['search_results']}",
                }
            ]
        },
        config=reader_config,
    )

    state["scraped_content"] = reader_response["messages"][-1].text
    yield "reader", state

    # Step 3: Writer chain
    # Chains take a dict whose keys match the prompt's placeholders: {topic} and {research}
    research_combined = _research_text(state["search_results"], state["scraped_content"])

    # normalize_markdown fixes doubled heading markers ("### ### Title") the model sometimes writes,
    # so the Critic doesn't lower the score for a formatting slip
    state["report"] = normalize_markdown(writer_chain.invoke(
        {
            "topic": topic,
            "research": research_combined,
        }
    ))
    yield "writer", state

    # Step 4: Critic chain
    # The critic prompt has three placeholders: {current_date}, {research} and {report}.
    # It gets the research too, so it can check the report's claims against the sources.
    state["feedback"] = critic_chain.invoke(
        {
            "current_date": date.today().isoformat(),
            "research": research_combined,
            "report": state["report"],
        }
    )
    yield "critic", state


def iter_revision_pipeline(previous: dict, thread_id: str | None = None) -> Iterator[tuple[str, dict]]:
    """
    Improve a finished report using the Critic's feedback, one step at a time, like iter_research_pipeline().

    previous is the earlier result: topic, search_results, scraped_content, report and feedback.
    1. The Search agent looks for sources with the information the Critic said was missing.
    2. The Reader agent reads them.
    3. The Reviser rewrites the previous report with all the research (old and new) and the feedback.
    4. The Critic scores the revised report.

    The yielded state has the same keys as iter_research_pipeline(). Its search_results and scraped_content
    hold the earlier research plus the new, so a revised report can itself be improved again.
    """
    thread_id = thread_id or str(uuid.uuid4())
    topic = previous["topic"]
    state = {"thread_id": thread_id}
    search_config = {"configurable": {"thread_id": f"{thread_id}-search"}}
    reader_config = {"configurable": {"thread_id": f"{thread_id}-reader"}}

    # Step 1: search for what the Critic found missing. The agent remembers this conversation,
    # so it looks for new sources rather than repeating its earlier results.
    search_response = build_search_agent().invoke(
        {"messages": [{"role": "user", "content": (
            f"Topic: {topic}\n\n"
            f"A reviewer found these problems in the report on this topic:\n{previous['feedback']}\n\n"
            "Search for sources with the specific information needed to fix them."
        )}]},
        config=search_config,
    )
    new_search = search_response["messages"][-1].text
    state["search_results"] = f"{previous['search_results']}\n\nAdditional sources found for the revision:\n{new_search}"
    yield "search", state

    # Step 2: read the new sources
    reader_response = build_reader_agent().invoke(
        {"messages": [{"role": "user", "content": f"Topic: {topic}\n\nSearch Results:\n{new_search}"}]},
        config=reader_config,
    )
    new_notes = reader_response["messages"][-1].text
    state["scraped_content"] = f"{previous['scraped_content']}\n\nAdditional notes for the revision:\n{new_notes}"
    yield "reader", state

    # Step 3: revise the previous report (not a fresh one) with all the research and the feedback
    research_combined = _research_text(state["search_results"], state["scraped_content"])
    state["report"] = normalize_markdown(reviser_chain.invoke(
        {
            "topic": topic,
            "research": research_combined,
            "report": previous["report"],
            "feedback": previous["feedback"],
        }
    ))
    yield "writer", state

    # Step 4: score the revised report against the same, larger body of research
    state["feedback"] = critic_chain.invoke(
        {
            "current_date": date.today().isoformat(),
            "research": research_combined,
            "report": state["report"],
        }
    )
    yield "critic", state


# ──────────────────────────────────────────────────
# Topic ideas for the UI
# ──────────────────────────────────────────────────

def suggest_topics(category: Category, avoid: list[str], count: int = 6) -> list[str]:
    """
    Ask the model for fresh research topics in a category, skipping any topic in avoid.

    Raises an error if the model call fails or returns nothing usable;
    the UI then falls back to the category's saved examples.
    """
    reply = topic_ideas_chain.invoke(
        {
            "current_date": date.today().isoformat(),
            "category": category.name,
            "focus": category.focus,
            "count": count,
            "avoid": "\n".join(f"- {topic}" for topic in avoid) or "None",
        }
    )

    ideas = []
    for line in reply.splitlines():
        # Strip any numbering, bullets or quotes the model added despite the instructions
        idea = re.sub(r"^\s*(?:[-*•]|\d+[.)])\s*", "", line).strip().strip("\"*").strip()
        if idea and len(idea) <= 90 and idea not in avoid and idea not in ideas:
            ideas.append(idea)

    if not ideas:
        raise ValueError(f"The model returned no usable topic ideas: {reply!r}")
    return ideas[:count]


# ──────────────────────────────────────────────────
# Command-line version
# ──────────────────────────────────────────────────

# step -> (label for its output, state key holding the output, title of the next step)
CLI_STEPS = {
    "search": ("Search results", "search_results", "Step 2: Running reader agent..."),
    "reader": ("Reader results", "scraped_content", "Step 3: Running writer chain..."),
    "writer": ("Writer results", "report", "Step 4: Running critic chain..."),
    "critic": ("Critic results", "feedback", None),
}


def print_step(title: str) -> None:
    print("\n" + "=" * 50)
    print(title)
    print("=" * 50)


def run_research_pipeline(topic: str, thread_id: str | None = None) -> dict:
    """
    Run the whole research pipeline on a topic, printing each step's output.
    Returns the final state: thread_id, search_results, scraped_content, report and feedback.
    Pass the same thread_id on later calls to continue the same conversation.
    """
    print_step("Step 1: Running search agent...")

    for step, state in iter_research_pipeline(topic, thread_id):
        label, key, next_title = CLI_STEPS[step]
        print(f"\n{label}:\n")
        print(state[key])
        if next_title:
            print_step(next_title)

    return state
