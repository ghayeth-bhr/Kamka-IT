"""
Agent executor: wires the LLM, tools, and system prompt together.
"""

from __future__ import annotations

from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI

from app.config import settings
from app.core.agent.tools import ALL_TOOLS


AGENT_SYSTEM_PROMPT = """\
You are a document-grounded AI assistant.
Answer the user's question using ONLY the tools available to you.
Always call `retrieve_context` first unless the user is explicitly asking for
a document summary (use `summarize_document`) or arithmetic (use `calculate`).

After calling tools, compose a final answer that:
- Is grounded in the retrieved content
- Cites which document/chunk the information came from
- Explicitly states if the answer is NOT found in the documents

{history}
"""


def build_agent_executor() -> AgentExecutor:
    llm = ChatOpenAI(
        model=settings.llm_model,
        api_key=settings.openrouter_api_key,
        base_url=settings.llm_base_url,
    )

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", AGENT_SYSTEM_PROMPT),
            MessagesPlaceholder("chat_history", optional=True),
            ("human", "{input}"),
            MessagesPlaceholder("agent_scratchpad"),
        ]
    )

    agent = create_tool_calling_agent(llm, ALL_TOOLS, prompt)
    return AgentExecutor(
        agent=agent,
        tools=ALL_TOOLS,
        verbose=True,
        return_intermediate_steps=True,
        max_iterations=6,
        handle_parsing_errors=True,
    )
