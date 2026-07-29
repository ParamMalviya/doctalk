import sys

from langchain_core.documents import Document
from langchain_chroma import Chroma

from doctalk.entity import RetrieverConfig
from doctalk.logger import logger
from doctalk.exception import CustomException


def format_docs(docs: list[Document]) -> str:
    '''
    turn a list of retrieved Documents into one clean text block
    for the prompt. keeps the page number inline so the model can
    cite it, and separates chunks with a blank line.
    without this the prompt would get raw Document objects, not text.
    '''
    formatted = []
    for doc in docs:
        page = doc.metadata.get("page", "?")
        formatted.append(f"[page {page}] {doc.page_content}")

    return "\n\n".join(formatted)


class RetrieverBuilder:
    '''
    wraps a chroma store as a standard retriever the agent can call.
    the store itself is built/loaded by VectorStore; this just adds
    the retrieval interface on top of it.
    '''

    def __init__(self, config: RetrieverConfig):
        self.config = config

    def build(self, store: Chroma):
        '''
        turn a chroma store into a retriever that returns the
        top-k chunks for any query string.
        '''
        try:
            retriever = store.as_retriever(
                search_kwargs={"k": self.config.k},
            )

            logger.info(f"built retriever with k={self.config.k}")
            return retriever

        except Exception as e:
            raise CustomException(e, sys) from e