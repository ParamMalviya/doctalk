import sys

from langchain_tavily import TavilySearch

from doctalk.logger import logger
from doctalk.exception import CustomException


def build_search_tool(max_results: int = 3):
    '''
    build the web search tool. TavilySearch is already a LangChain
    tool, so we just configure it and give it a description tuned
    for our router. reads TAVILY_API_KEY from the environment.
    '''
    try:
        search_tool = TavilySearch(max_results=max_results)

        # override the default description so the agent knows WHEN to
        # use web search: only for current/external info the uploaded
        # document would not contain
        search_tool.description = (
            "Search the web for current, real-world, or external information "
            "that would NOT be found in the user's uploaded document. Use this "
            "for recent events, current facts, or general knowledge questions. "
            "Do NOT use this for questions about the content of the uploaded document."
        )

        logger.info(f"built web search tool with max_results={max_results}")
        return search_tool

    except Exception as e:
        raise CustomException(e, sys) from e