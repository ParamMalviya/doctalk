import logging

from tenacity import retry, retry_if_exception, wait_exponential, stop_after_attempt, before_sleep_log
from google.genai.errors import ClientError

import sys

from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver

from doctalk.config.configuration import ConfigurationManager
from doctalk.components.vector_store import VectorStore
from doctalk.components.retriever import RetrieverBuilder
from doctalk.components.tools.retrieve_tool import build_retrieve_tool
from doctalk.components.tools.summarize_tool import build_summarize_tool
from doctalk.components.tools.search_tool import build_search_tool
from doctalk.components.tools.github_tool import github_repo_info
from doctalk.components.agent_graph import build_agent
from doctalk.utils.common import normalise_content
from doctalk.logger import logger
from doctalk.exception import CustomException

def _is_rate_limited(exc: BaseException) -> bool:
    '''
    True only for a genuine 429. langchain wraps Google's real ClientError
    into ChatGoogleGenerativeAIError (a plain message, no status code) --
    but it does so with "from e", same as our own CustomException, so the
    ORIGINAL ClientError (which DOES carry .code) is still reachable via
    __cause__. We check THAT, not the wrapper, so we only retry actual
    rate limits -- not auth errors, bad requests, etc.
    '''
    cause = exc.__cause__
    return isinstance(cause, ClientError) and cause.code == 429

STAGE_NAME = "Chat"


class ChatPipeline:
    '''
    stage 2: answer a question about an already-ingested session.
    builds the agent (retriever + 4 tools) for a session, then answers
    questions through it. chunks are needed for the summarize tool, so
    they are passed in from ingestion.
    '''

    def __init__(self, session_id: str, chunks: list):
        try:
            self.session_id = session_id  # kept for ask() -- doubles as the checkpointer's thread_id
            cm = ConfigurationManager()
            self.params = cm.params

            # load the session's existing vector store (no re-embedding)
            vector_store = VectorStore(cm.get_vector_store_config())
            store = vector_store.load(session_id=session_id)

            # build retriever from it
            retriever = RetrieverBuilder(cm.get_retriever_config()).build(store)

            # assemble all four tools
            tools = [
                build_retrieve_tool(retriever),
                build_summarize_tool(cm.get_summarize_tool_config(), chunks),
                build_search_tool(max_results=3),
                github_repo_info,
            ]

            # build the agent once, reuse for every question. MemorySaver holds
            # this session's conversation history IN MEMORY, for this pipeline's
            # lifetime -- which, since Stage 11's caching change, is the session's
            # whole life. one checkpointer per session, never shared across sessions.
            checkpointer = MemorySaver()
            self.agent = build_agent(
                tools=tools,
                chat_model=self.params["chat_model"],
                temperature=self.params["temperature"],
                checkpointer=checkpointer,
            )

            logger.info(f"chat pipeline ready for session {session_id}")

        except Exception as e:
            raise CustomException(e, sys) from e

    @retry(
        retry=retry_if_exception(_is_rate_limited),
        wait=wait_exponential(multiplier=1, min=1, max=10),  # 1s, 2s, 4s... capped at 10s
        stop=stop_after_attempt(4),                          # up to 4 tries total
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,  # if every retry still fails, raise the ORIGINAL error, not tenacity's own
    )
    def ask(self, question: str, thread_id: str | None = None) -> str:
        '''
        ask the agent a question, return a clean text answer.
        thread_id lets a caller route this SAME cached pipeline to a
        DIFFERENT conversation thread -- used by eval to keep its 15
        questions independent, even though they share one built pipeline.
        defaults to this session's own id (normal production behavior:
        routes.py never passes this, so nothing there changes).
        '''
        try:
            result = self.agent.invoke(
                {"messages": [HumanMessage(question)]},
                config={"configurable": {"thread_id": thread_id or self.session_id}},
            )

            # the last message is the agent's final answer
            answer = normalise_content(result["messages"][-1].content)
            logger.info("chat pipeline produced an answer")
            return answer

        except Exception as e:
            raise CustomException(e, sys) from e