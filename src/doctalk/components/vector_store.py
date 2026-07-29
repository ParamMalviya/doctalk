import sys
from pathlib import Path

from langchain_core.documents import Document
from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings

from doctalk.entity import VectorStoreConfig
from doctalk.logger import logger
from doctalk.exception import CustomException


class VectorStore:
    '''
    builds and loads session-scoped chroma collections.
    each session id gets its own folder under root_dir, so one
    user's chunks are fully isolated from another's.
    '''

    def __init__(self, config: VectorStoreConfig):
        self.config = config
        # one embeddings object, reused for every session.
        # the library reads GOOGLE_API_KEY from the environment itself
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model=self.config.embedding_model
        )

    def _session_path(self, session_id: str) -> str:
        '''
        build the on-disk folder path for one session's chroma data.
        returned as a string because chroma wants a str path.
        '''
        return str(self.config.root_dir / session_id)

    def build(self, chunks: list[Document], session_id: str) -> Chroma:
        '''
        embed the chunks and store them in this session's own collection.
        this is the write path: called once, when a user uploads a pdf.
        '''
        try:
            persist_path = self._session_path(session_id)

            store = Chroma.from_documents(
                documents=chunks,
                embedding=self.embeddings,
                persist_directory=persist_path,
                collection_name=session_id,
            )

            logger.info(
                f"stored {len(chunks)} chunks for session {session_id} at {persist_path}"
            )
            return store

        except Exception as e:
            raise CustomException(e, sys) from e

    def load(self, session_id: str) -> Chroma:
        '''
        open an EXISTING session collection without re-embedding.
        this is the read path: called on every question, so it must
        NOT rebuild or re-embed anything.
        '''
        try:
            persist_path = self._session_path(session_id)

            store = Chroma(
                persist_directory=persist_path,
                collection_name=session_id,
                embedding_function=self.embeddings,
            )

            logger.info(f"loaded existing collection for session {session_id}")
            return store

        except Exception as e:
            raise CustomException(e, sys) from e