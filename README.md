# LangChain Multi-Agent Research System

A command-line research assistant built with LangChain and Google Gemini. Give it a topic and four specialized steps work in sequence: one searches the web, one reads the best sources, one writes a cited report, and one reviews that report against the research. It remembers the conversation, so you can ask follow-up questions in the same session.

## How it works

```
 topic ─▶ 1. Search Agent ─▶ 2. Reader Agent ─▶ 3. Writer ─▶ 4. Critic ─▶ report + review
          (web_search)       (scrape_url)        (chain)      (chain)
```

| Step | Type | Tool | What it does |
|---|---|---|---|
| 1. Search Agent | Agent | `web_search` (Tavily) | Runs several focused searches and returns a list of reliable sources, each with a URL and a summary |
| 2. Reader Agent | Agent | `scrape_url` | Reads 3-5 of those pages and extracts the key facts, figures and quotes, skipping pages that fail to load |
| 3. Writer | Chain | none | Writes a structured report (introduction, key findings, conclusion, sources) using only the research gathered |
| 4. Critic | Chain | none | Checks the report against the research and returns a score out of 10, strengths, areas to improve and a one-line verdict |

### Agents vs. chains

- **Agents** (`create_agent`) put the model in a loop with tools. The model decides which tool to call, with what input, and when it has enough to answer. Search and reading need this, because the next action depends on what the last one returned.
- **Chains** (`prompt | model | parser`) are a fixed sequence with a single model call. Writing and reviewing only transform text they are given, so a chain is simpler, faster and cheaper.

### Web scraping with a fallback

`scrape_url` first fetches the page directly and tries three extraction methods in turn: trafilatura, then readability, then the page's full visible text. If the site blocks the request (401/403, timeouts or bot protection), it falls back to Tavily's extract API. If both fail, the tool returns a clear error message, and the Reader Agent is instructed to skip that page and move on. A few sites, such as Reuters, block both methods.

### Conversation memory

The two agents share a LangGraph `InMemorySaver` checkpointer. Each session in `main.py` gets one `thread_id`, so later questions can refer to earlier ones:

```
Enter a research topic: Small language models in 2026
...
Enter a research topic: Which of those models is cheapest to run?
```

On the second question, the Search Agent understands that "those models" means the small language models from the first question. Each agent keeps its own thread (`<id>-search`, `<id>-reader`), so their histories don't mix.

## Project structure

```
.
├── main.py                  # Entry point: interactive loop with conversation memory
├── app.py                   # Streamlit UI (not built yet)
├── requirements.txt
├── .env                     # API keys (not committed)
└── src/
    ├── tools/tools.py       # web_search and scrape_url tools
    ├── prompts/prompts.py   # System prompts for all four steps
    ├── agents/agents.py     # Gemini model, the two agents, the two chains, the checkpointer
    └── pipelines/pipelines.py  # run_research_pipeline(): runs the four steps in order
```

## Setup

**Requirements:** Python 3.11, a [Google Gemini API key](https://aistudio.google.com/apikey) and a [Tavily API key](https://app.tavily.com/).

1. Clone the repository:

   ```bash
   git clone https://github.com/kashif-sureify/langchain-multi-agent-research-system.git
   cd langchain-multi-agent-research-system
   ```

2. Create a virtual environment and install the dependencies, using either uv:

   ```bash
   uv venv --python 3.11
   source .venv/bin/activate
   uv pip install -r requirements.txt
   ```

   or pip:

   ```bash
   python3.11 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the project root:

   ```env
   GEMINI_API_KEY=your-gemini-api-key
   GEMINI_MODEL=gemini-3.5-flash-lite
   TAVILY_API_KEY=your-tavily-api-key
   GROQ_API_KEY=your-groq-api-key
   ```

   `GROQ_API_KEY` must be set because `src/tools/tools.py` reads it at startup, even though no Groq model is used yet.

## Usage

Run the interactive research loop:

```bash
python main.py
```

Enter a topic and the four steps run in order, printing each step's output. Then ask follow-up questions in the same session. Type `exit`, or press Enter on an empty line, to quit.

To use the pipeline from your own code:

```python
from src.pipelines.pipelines import run_research_pipeline

state = run_research_pipeline("Small language models in 2026")
print(state["report"])    # the written report
print(state["feedback"])  # the critic's review

# Pass the same thread_id to continue the conversation
follow_up = run_research_pipeline("Which of those is cheapest to run?", thread_id=state["thread_id"])
```

`run_research_pipeline` returns a dict with `thread_id`, `search_results`, `scraped_content`, `report` and `feedback`.

## Limitations

- **Memory only lasts while the program runs.** `InMemorySaver` keeps conversations in memory, so they are lost when the program exits. A database-backed checkpointer, such as SQLite, would keep them across restarts.
- **Only the agents remember.** The Writer and Critic are chains and keep no history. On a follow-up question, they see only that question and the new research.
- **Costs grow with conversation length.** Each follow-up resends the agent's full history to the model, including scraped page text (up to 5,000 characters per page).
- **Some sites can't be scraped.** Sites with strong bot protection (for example Reuters) block both the direct fetch and the Tavily fallback.

## Troubleshooting

**`ModuleNotFoundError: No module named 'readability'`** means you are running a Python that isn't this project's virtual environment. Run `which python`, which should point to `.venv/bin/python` inside this project. If it doesn't, run `source .venv/bin/activate`. In VS Code, select `./.venv` with **Python: Select Interpreter** and open a new terminal, because terminals that are already open keep their old environment.

## Roadmap

- Streamlit web interface (`app.py`)
- Conversation memory for the Writer and Critic
- Persistent memory across restarts

## License

Apache License 2.0. See [LICENSE](LICENSE).
