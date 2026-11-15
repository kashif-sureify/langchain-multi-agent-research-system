from langchain.agents import create_agent
import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.output_parsers import StrOutputParser
from langgraph.checkpoint.memory import InMemorySaver
from src.tools.tools import web_search, scrape_url
from src.prompts.prompts import (
    search_agent_prompt, reader_agent_prompt, writer_prompt, reviser_prompt, critic_prompt, topic_ideas_prompt,
)
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())
gemini_api_key = os.environ["GEMINI_API_KEY"]
gemini_model = os.environ["GEMINI_MODEL"]

# Model Initialization
# (no temperature: gemini-3.5-flash-lite uses fixed sampling and ignores it)
model = ChatGoogleGenerativeAI(model=gemini_model, api_key=gemini_api_key)

# Memory for the agents. Created once and shared, so conversations are remembered
# across pipeline runs for as long as the Python process is running (lost on restart).
# Each conversation is stored under the thread_id passed in the config at invoke time.
checkpointer = InMemorySaver()

# 1st Step: Search Agent
def build_search_agent():
    return create_agent(
        name="search_agent",
        model=model,
        tools=[web_search],
        system_prompt=search_agent_prompt,
        checkpointer=checkpointer,
    )

# 2nd Step: Reader Agent
def build_reader_agent():
    return create_agent(
        name="reader_agent",
        model=model,
        tools=[scrape_url],
        system_prompt=reader_agent_prompt,
        checkpointer=checkpointer,
    )

# 3rd Step: Writer Chain

writer_chain = writer_prompt | model | StrOutputParser()

# 3rd Step when improving a report: rewrites the previous report to address the Critic's feedback
reviser_chain = reviser_prompt | model | StrOutputParser()

# 4th Step: Critic Chain
critic_chain = critic_prompt | model | StrOutputParser()

# UI helper (not a pipeline step): suggests sample research topics for a category
topic_ideas_chain = topic_ideas_prompt | model | StrOutputParser()
