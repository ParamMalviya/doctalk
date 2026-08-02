import sys

from langchain.agents import create_agent
from langchain_google_genai import ChatGoogleGenerativeAI

from doctalk.logger import logger
from doctalk.exception import CustomException


SYSTEM_PROMPT = (
    "You are DocTalk, an assistant that answers questions about a user's "
    "uploaded document. Follow these rules:\n"
    "- For questions about the document's content, use the retrieve_document tool.\n"
    "- For a summary or overview of the whole document, use summarize_document.\n"
    "- For questions about a GitHub repository or URL, use github_repo_info.\n"
    "- For current or external facts not in the document, use tavily_search.\n"
    "- When you use retrieved document content, cite the page numbers shown as [page N].\n"
    "- If a question needs no tool, answer directly and briefly."
)


def build_agent(tools: list, chat_model: str, temperature: float):
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
        )

        logger.info(f"built agent with tools: {[t.name for t in tools]}")
        return agent

    except Exception as e:
        raise CustomException(e, sys) from e