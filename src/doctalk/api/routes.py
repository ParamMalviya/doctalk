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

# cap on CHUNKS, not megabytes -- a 2MB file can be 15 pages or 224 pages,
# and it's the CHUNK count that maps 1:1 to embedding API calls. Gemini's
# free tier allows 100 embeddings/min (proven by a real 429), so we stay
# safely under that. this makes DocTalk a small-document demo, on purpose.
MAX_CHUNKS = 80
MAX_QUESTIONS_PER_SESSION = 30  # caps one session's share of the DAILY quota

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
        # save the uploaded bytes to a temp file so pypdf can read a path
        contents = await file.read()

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(contents)
            tmp_path = Path(tmp.name)

        # ingest -> chunks
        chunks = ingestion_pipeline.run(Path(tmp_path))

        # reject too-large docs AFTER we know the chunk count but BEFORE embedding --
        # this is the real guard: it stops the 429 that killed the 224-page upload
        if len(chunks) > MAX_CHUNKS:
            raise HTTPException(
                status_code=413,
                detail=(
                    f"Document too large ({len(chunks)} chunks). "
                    f"DocTalk's free tier supports up to {MAX_CHUNKS} chunks "
                    f"(roughly 20-25 pages). Try a shorter document."
                ),
            )
        # register the session (this makes the unique session_id)
        session_id = session_store.create_session(chunks=chunks,          filename=file.filename)

        # build the session's vector store on disk
        cm = ConfigurationManager()


        VectorStore(cm.get_vector_store_config()).build(chunks=chunks, session_id=session_id)

        # build the chat pipeline ONCE, right here, and cache it (Option 2: eager).
        # must happen AFTER the vector store build above -- ChatPipeline loads the
        # store from disk, so the store has to exist before this runs.
        chat_pipeline = ChatPipeline(session_id=session_id, chunks=chunks)
        session_store.set_pipeline(session_id, chat_pipeline)

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

        # fetch the ALREADY-BUILT pipeline instead of building a new one --
        # this is the whole point of today's change: build once at upload,
        # reuse for every question in the session.
        chat_pipeline = session_store.get_pipeline(request.session_id)
        if chat_pipeline is None:
            raise HTTPException(
                status_code=500,
                detail="Chat pipeline was not initialized for this session.",
            )

        # per-session cap -- protects the SHARED daily quota (Azure CPU-min,
        # Gemini rate limits) from one session using more than its fair share
        questions_so_far = session_store.increment_questions(request.session_id)
        if questions_so_far > MAX_QUESTIONS_PER_SESSION:
            raise HTTPException(
                status_code=429,
                detail=(
                    f"This session has reached its {MAX_QUESTIONS_PER_SESSION}-question "
                    "limit. Upload a document again to start a fresh session."
                ),
            )

        answer = chat_pipeline.ask(request.question)

        return ChatResponse(answer=answer)

    except HTTPException:
        raise
    except Exception as e:
        raise CustomException(e, sys) from e