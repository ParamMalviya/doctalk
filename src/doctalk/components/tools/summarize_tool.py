import sys

from langchain_core.documents import Document
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI

from doctalk.entity import SummarizeToolConfig
from doctalk.logger import logger
from doctalk.exception import CustomException


def build_summarize_tool(config: SummarizeToolConfig, chunks: list[Document]):
    '''
    build a summarize tool bound to THIS session's chunks.
    returns a @tool the agent can call with no arguments -- the
    document is already captured inside it (a closure).
    uses map-reduce so it scales past the context window.
    '''

    # one chat model, reused for every summarize call
    llm = ChatGoogleGenerativeAI(
        model=config.chat_model,
        temperature=config.temperature,
    )

    def _summarize_text(text: str, instruction: str) -> str:
        '''one generation call: prompt in, summary text out.
        gemini's .content can be a str OR a list of parts, so
        normalise it to a plain string either way.'''
        prompt = f"{instruction}\n\n{text}"
        response = llm.invoke(prompt)
        content = response.content

        # normalise: sometimes content is a list of parts, not a string
        if isinstance(content, list):
            parts = []
            for part in content:
                # a part can be a plain string or a dict with a "text" key
                if isinstance(part, str):
                    parts.append(part)
                elif isinstance(part, dict):
                    parts.append(part.get("text", ""))
            content = " ".join(parts)

        return content

    @tool
    def summarize_document() -> str:
        '''
        Summarize the entire uploaded document. Use this when the user
        asks for a summary, an overview, the main points, or "what is
        this document about" -- anything about the whole document rather
        than a specific detail.
        '''
        try:
            # MAP: summarize the document in batches of chunks
            batch_summaries = []
            for i in range(0, len(chunks), config.batch_size):
                batch = chunks[i : i + config.batch_size]
                batch_text = "\n\n".join(doc.page_content for doc in batch)

                summary = _summarize_text(
                    batch_text,
                    "Summarize the key points of this section of a document:",
                )
                batch_summaries.append(summary)
                logger.info(f"summarized batch {i // config.batch_size + 1}")

            # REDUCE: combine the batch summaries into one final summary
            combined = "\n\n".join(batch_summaries)
            final = _summarize_text(
                combined,
                "Combine these section summaries into one clear overall summary:",
            )

            logger.info("summarize tool produced final summary")
            return final

        except Exception as e:
            raise CustomException(e, sys) from e

    return summarize_document