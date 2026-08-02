import sys

from langchain_core.tools import tool

from doctalk.components.retriever import format_docs
from doctalk.logger import logger
from doctalk.exception import CustomException


def build_retrieve_tool(retriever):
    '''
    wrap a retriever as a @tool the agent can call.
    the retriever is captured in a closure, so the agent calls
    retrieve_document(query) with just a query string.
    returns clean [page N] text via format_docs.
    '''

    @tool
    def retrieve_document(query: str) -> str:
        '''
        Search the user's uploaded document for information relevant to
        the query. Use this for ANY question about the content, topic,
        details, or specifics of the uploaded document. This is the
        primary tool for answering questions grounded in the document.
        '''
        try:
            docs = retriever.invoke(query)
            if not docs:
                return "No relevant content found in the document."

            formatted = format_docs(docs)
            logger.info(f"retrieve tool returned {len(docs)} chunks for query")
            return formatted

        except Exception as e:
            raise CustomException(e, sys) from e

    return retrieve_document