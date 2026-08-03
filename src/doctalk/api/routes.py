import sys
import tempfile
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, HTTPException

from doctalk.pipelines.stage_01_ingestion import IngestionPipeline
from doctalk.pipelines.stage_02_chat import ChatPipeline
from doctalk.components.vector_store import VectorStore
from doctalk.config.configuration import ConfigurationManager
from doctalk.components.session_store import SessionStore
from doctalk.api.schemas import UploadResponse, ChatRequest, ChatResponse
from doctalk.logger import logger
from doctalk.exception import CustomException


# the router that main.py will plug into the app
router = APIRouter()

# Option A: one in-memory session store for the whole app.
# built once here, shared by all requests.
session_store = SessionStore()

# ingestion pipeline built once, reused for every upload
ingestion_pipeline = IngestionPipeline()


@router.post("/upload", response_model=UploadResponse)
async def upload(file: UploadFile = File(...)):
    '''
    receive a pdf, ingest it, build its session vector store,
    and return a session_id the client uses for /chat.
    '''
    try:
        # only accept pdfs
        if not file.filename.lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Only PDF files are supported.")

        # save the uploaded bytes to a temp file so pypdf can read a path
        contents = await file.read()
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(contents)
            tmp_path = Path(tmp.name)

        # ingest -> chunks
        chunks = ingestion_pipeline.run(tmp_path)

        # register the session (this makes the unique session_id)
        session_id = session_store.create_session(chunks=chunks, filename=file.filename)

        # build the session's vector store on disk
        cm = ConfigurationManager()
        VectorStore(cm.get_vector_store_config()).build(chunks=chunks, session_id=session_id)

        logger.info(f"uploaded and ingested {file.filename} as session {session_id}")

        return UploadResponse(
            session_id=session_id,
            filename=file.filename,
            num_chunks=len(chunks),
            message="Document ingested. Use the session_id to chat.",
        )

    except HTTPException:
        raise  # let FastAPI handle the ones we raised on purpose
    except Exception as e:
        raise CustomException(e, sys) from e


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    '''
    answer a question about an already-uploaded document,
    identified by session_id.
    '''
    try:
        # is this a known session?
        session = session_store.get(request.session_id)
        if session is None:
            raise HTTPException(
                status_code=404,
                detail="Session not found. Upload a document first.",
            )

        # build the chat pipeline for this session and ask
        chat_pipeline = ChatPipeline(
            session_id=request.session_id,
            chunks=session["chunks"],
        )
        answer = chat_pipeline.ask(request.question)

        return ChatResponse(answer=answer)

    except HTTPException:
        raise
    except Exception as e:
        raise CustomException(e, sys) from e