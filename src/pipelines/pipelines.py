from src.agents.agents import (
    build_search_agent,
    build_reader_agent,
    writer_chain,
    critic_chain,
)
from datetime import date
import uuid


def print_step(title: str) -> None:
    print("\n" + "=" * 50)
    print(title)
    print("=" * 50)


def run_research_pipeline(topic: str, thread_id: str | None = None) -> dict:
    """
    Run the research pipeline on a topic.
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
    print_step("Step 1: Running search agent...")

    search_agent = build_search_agent()

    search_response = search_agent.invoke(
        {"messages": [{"role": "user", "content": f"Topic: {topic}"}]},
        config=search_config,
    )

    # .text gives the plain string; with Gemini, .content is a list of content blocks
    state["search_results"] = search_response["messages"][-1].text

    print("\nSearch results:\n")
    print(state["search_results"])

    # Step 2: Reader agent
    # Pass the full search results; truncating them cuts off the URLs the reader needs.
    print_step("Step 2: Running reader agent...")

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

    print("\nReader results:\n")
    print(state["scraped_content"])

    # Step 3: Writer chain
    # Chains take a dict whose keys match the prompt's placeholders: {topic} and {research}
    print_step("Step 3: Running writer chain...")

    research_combined = (
        f"Search results:\n{state['search_results']}\n\n"
        f"Scraped content:\n{state['scraped_content']}"
    )

    state["report"] = writer_chain.invoke(
        {
            "topic": topic,
            "research": research_combined,
        }
    )

    print("\nWriter results:\n")
    print(state["report"])

    # Step 4: Critic chain
    # The critic prompt has three placeholders: {current_date}, {research} and {report}.
    # It gets the research too, so it can check the report's claims against the sources.
    print_step("Step 4: Running critic chain...")

    state["feedback"] = critic_chain.invoke(
        {
            "current_date": date.today().isoformat(),
            "research": research_combined,
            "report": state["report"],
        }
    )

    print("\nCritic results:\n")
    print(state["feedback"])

    return state
