# Researchers: LangChain Multi-Agent Research System

A research assistant built with LangChain and Google Gemini, with a Streamlit web app and a command-line interface. Give it a topic and four specialized steps work in sequence: one searches the web, one reads the best sources, one writes a cited report, and one reviews that report against the research. It remembers the conversation, so you can ask follow-up questions in the same session.

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
| 4. Critic | Chain | none | Checks the report against the research and returns a score out of 10 (on a fixed scale), strengths, areas to improve and a one-line verdict |

### Improving a report

If a report scores below 9, **Improve this report** runs a revision instead of starting over (`iter_revision_pipeline()`):

```
 critic review ─▶ 1. Search Agent ─▶ 2. Reader Agent ─▶ 3. Reviser ─▶ 4. Critic ─▶ revised report + new score
                  (searches for the     (reads the new     (rewrites the
                   information the       sources)           previous report
                   Critic found missing)                    using the review)
```

The Reviser sees the previous report, the Critic's review and all the research, old and new, so it fixes the specific problems instead of writing a different report. The new score is shown next to the old one ("+2 from 6/10").

Asking the same question again, or pasting the Critic's points into the topic box, doesn't do this: it starts a fresh report, because the Writer never sees the earlier report.

Two things keep scores fair: the pipeline tidies heading markers before the Critic reads a report, and sources the Reader couldn't open are left out of the research the Writer sees, so it can't cite pages nobody could check.

### Agents vs. chains

- **Agents** (`create_agent`) put the model in a loop with tools. The model decides which tool to call, with what input, and when it has enough to answer. Search and reading need this, because the next action depends on what the last one returned.
- **Chains** (`prompt | model | parser`) are a fixed sequence with a single model call. Writing and reviewing only transform text they are given, so a chain is simpler, faster and cheaper.

### Web scraping with a fallback

`scrape_url` first fetches the page directly and tries three extraction methods in turn: trafilatura, then readability, then the page's full visible text. If the site blocks the request (401/403, timeouts or bot protection), it falls back to Tavily's extract API. If both fail, the tool returns a clear error message, and the Reader Agent is instructed to skip that page and move on. A few sites, such as Reuters, block both methods.

### Conversation memory

The two agents share a LangGraph `InMemorySaver` checkpointer. Each session (a run of `main.py`, or a browser tab in the web app) gets one `thread_id`, so later questions can refer to earlier ones:

```
Enter a research topic: Small language models in 2026
...
Enter a research topic: Which of those models is cheapest to run?
```

On the second question, the Search Agent understands that "those models" means the small language models from the first question. Each agent keeps its own thread (`<id>-search`, `<id>-reader`), so their histories don't mix.

## Project structure

```
.
├── app.py                   # Web app entry point (Streamlit): page layout, session state, live runs
├── main.py                  # Command-line entry point: interactive loop with conversation memory
├── ui/                      # Frontend only, no research logic
│   ├── theme.py             # Light, dark and system themes (CSS variables)
│   ├── components.py        # HTML building blocks: hero, agent cards, report and critic review
│   ├── icons.py             # Line icons for the HTML parts of the page
│   └── pdf.py               # PDF export of a report and its critic review
├── .streamlit/config.toml   # Streamlit settings (accent color, toolbar, no usage stats)
├── requirements.txt
├── .env                     # API keys (not committed)
└── src/                     # Backend
    ├── tools/tools.py       # web_search and scrape_url tools
    ├── prompts/prompts.py   # Prompts for the agents, the Writer, Reviser and Critic, and topic ideas
    ├── agents/agents.py     # Gemini model, the two agents, the chains, the checkpointer
    ├── topics/categories.py # Categories for the sample-topic picker
    ├── utils/markdown.py    # Heading clean-up shared by the pipeline and the UI
    └── pipelines/pipelines.py  # iter_research_pipeline(), iter_revision_pipeline() and run_research_pipeline() (CLI)
```

The frontend and backend are separate: `app.py` and `ui/` only display things, and they reach the backend through `iter_research_pipeline()`, `iter_revision_pipeline()` and `suggest_topics()`.

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

### Web app

```bash
streamlit run app.py
```

Then open http://localhost:8501. In the app you can:

- **Pick a topic:** type your own, or click one of the sample topics to fill in the box.
- **Start research:** a tracker shows each of the four steps as *Waiting*, *Running* and *Done* while it works. Each step's output appears as soon as it's ready.
- **Read the results:**
  - the sources found (step 1) and the Reader's notes (step 2), in expandable sections
  - the final report (step 3), with buttons to download it as a **PDF** or as Markdown. Both include the Critic's review, and source links in the PDF are clickable
  - the Critic's review (step 4) at the end, with its score, verdict, strengths and areas to improve
- **Improve a report:** below a score of 9, **Improve this report** revises the report to fix the Critic's points and scores it again. The earlier version stays available further down the page.
- **Ask follow-ups:** questions in the same tab remember earlier ones, and earlier results stay available further down the page. **New conversation** in the sidebar starts fresh.
- **Switch the theme:** choose Light, Dark or System in the sidebar. System follows your operating system's setting, and the choice is saved in the page URL (`?theme=dark`), so a refresh keeps it.

### Command line

```bash
python main.py
```

Enter a topic and the four steps run in order, printing each step's output. Then ask follow-up questions in the same session. Type `exit`, or press Enter on an empty line, to quit.

### From your own code

To get the final result:

```python
from src.pipelines.pipelines import run_research_pipeline

state = run_research_pipeline("Small language models in 2026")
print(state["report"])    # the written report
print(state["feedback"])  # the critic's review

# Pass the same thread_id to continue the conversation
follow_up = run_research_pipeline("Which of those is cheapest to run?", thread_id=state["thread_id"])
```

`run_research_pipeline` returns a dict with `thread_id`, `search_results`, `scraped_content`, `report` and `feedback`.

To show progress while it runs, as the web app does, use `iter_research_pipeline`. It yields after each step finishes:

```python
from src.pipelines.pipelines import iter_research_pipeline

for step, state in iter_research_pipeline("Small language models in 2026"):
    print(f"{step} finished")   # "search", "reader", "writer", then "critic"
print(state["report"])
```

To improve a finished report using its critic review, pass the earlier result (with its `topic`) to `iter_revision_pipeline`. It yields the same steps and state keys:

```python
from src.pipelines.pipelines import iter_revision_pipeline

previous = {"topic": "Small language models in 2026", **state}
for step, revised in iter_revision_pipeline(previous, thread_id=state["thread_id"]):
    print(f"{step} finished")
print(revised["feedback"])  # the new review and score
```

## Limitations

- **Memory only lasts while the program runs.** `InMemorySaver` keeps conversations in memory, so they are lost when the program or the Streamlit server stops. Reloading the web page also starts a new conversation. A database-backed checkpointer, such as SQLite, would keep them across restarts.
- **Only the agents remember.** The Writer and Critic are chains and keep no history. On a follow-up question, they see only that question and the new research. (Improve this report is the exception: the Reviser is given the previous report and its review.)
- **Scores vary a little.** The Critic is a language model, so the same report can score a point apart on different runs, and revising a report that already scores 9 or 10 rarely raises it.
- **Costs grow with conversation length.** Each follow-up resends the agent's full history to the model, including scraped page text (up to 5,000 characters per page).
- **Some sites can't be scraped.** Sites with strong bot protection (for example Reuters) block both the direct fetch and the Tavily fallback.

## Troubleshooting

**`ModuleNotFoundError: No module named 'readability'`** (or the web app saying a package is missing) means you are running a Python that isn't this project's virtual environment. Run `which python` and `which streamlit`; both should point into `.venv/bin/` inside this project. If they don't, run `source .venv/bin/activate`. In VS Code, select `./.venv` with **Python: Select Interpreter** and open a new terminal, because terminals that are already open keep their old environment.

To start the web app with this project's environment no matter which one is active, run it directly:

```bash
.venv/bin/streamlit run app.py
```

## Roadmap

- Conversation memory for the Writer and Critic
- Persistent memory across restarts

## License

Apache License 2.0. See [LICENSE](LICENSE).
