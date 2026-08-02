import sys

from langchain_core.messages import HumanMessage

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

            # build the agent once, reuse for every question
            self.agent = build_agent(
                tools=tools,
                chat_model=self.params["chat_model"],
                temperature=self.params["temperature"],
            )

            logger.info(f"chat pipeline ready for session {session_id}")

        except Exception as e:
            raise CustomException(e, sys) from e

    def ask(self, question: str) -> str:
        '''
        ask the agent a question, return a clean text answer.
        '''
        try:
            result = self.agent.invoke({
                "messages": [HumanMessage(question)]
            })

            # the last message is the agent's final answer
            answer = normalise_content(result["messages"][-1].content)
            logger.info("chat pipeline produced an answer")
            return answer

        except Exception as e:
            raise CustomException(e, sys) from e