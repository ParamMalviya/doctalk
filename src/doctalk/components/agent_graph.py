import sys

from langchain.agents import create_agent
from langchain_google_genai import ChatGoogleGenerativeAI

from doctalk.logger import logger
from doctalk.exception import CustomException


SYSTEM_PROMPT = (
    "You are DocTalk, an assistant that answers questions about a user's "
    "uploaded document. Follow these rules:\n"
    "- ALWAYS try retrieve_document FIRST for any question that could plausibly "
    "be answered by the uploaded document. Only use tavily_search if the "
    "question is clearly about something outside the document (current events, "
    "a library's latest version, general web facts).\n"
    "- For questions about the document's content, use the retrieve_document tool.\n"
    "- For questions about the document's content, use the retrieve_document tool.\n"
    "- For a summary or overview of the whole document, use summarize_document.\n"
    "- For questions about a GitHub repository or URL, use github_repo_info.\n"
    "- For current or external facts not in the document, use tavily_search.\n"
    "- When you use retrieved document content, cite the page numbers shown as [page N].\n"
    "- If a question needs no tool, answer directly and briefly.\n"
    "- You have access to this conversation's earlier turns. If the current "
    "question refers back to something discussed earlier (e.g. \"what about "
    "the second one\", \"explain that more\"), use that context to understand "
    "what's being asked."
)


def build_agent(tools: list, chat_model: str, temperature: float, checkpointer=None):
    '''
    build the DocTalk agent from a list of already-built tools.
    the caller assembles session-specific tools (retrieve, summarize)
    plus stateless ones (github, search) and passes them in.
    gemini-3.1-flash-lite honours temperature, so we pass it -- 0.0
    keeps answers focused and grounded, which is what we want for RAG.
    '''
    try:
        llm = ChatGoogleGenerativeAI(model=chat_model, temperature=temperature)

        agent = create_agent(
            model=llm,
            tools=tools,
            system_prompt=SYSTEM_PROMPT,
            checkpointer=checkpointer,  # None -> agent has no memory (unchanged old behavior)
        )

        logger.info(f"built agent with tools: {[t.name for t in tools]}")
        return agent

    except Exception as e:
        raise CustomException(e, sys) from e