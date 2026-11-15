import uuid

from src.pipelines.pipelines import run_research_pipeline

# ── Quick tool tests (uncomment to try the tools on their own) ──
# from src.tools.tools import web_search, scrape_url
# print(web_search.invoke("Latest research in AI"))
# Reuters blocks all automated access (direct requests AND Tavily extract), so it can't be scraped:
# print(scrape_url.invoke("https://www.investopedia.com/terms/a/artificial-intelligence-ai.asp"))


if __name__ == "__main__":
    # One thread_id for the whole session, so follow-up questions remember earlier topics
    thread_id = str(uuid.uuid4())
    print("Enter a research topic, then follow-up questions. Type 'exit' or press Enter on an empty line to quit.")

    while True:
        topic = input("\nEnter a research topic: ").strip()
        if not topic or topic.lower() in ("exit", "quit"):
            break
        run_research_pipeline(topic, thread_id=thread_id)
