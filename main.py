from contextlib import asynccontextmanager

from fastapi import FastAPI
from dotenv import load_dotenv

from doctalk.logger import setup_logging, logger
from doctalk.api.routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # everything ABOVE the yield runs ONCE at startup, before any request is served.
    # load .env so GOOGLE_API_KEY (and the other keys) are in the environment,
    # then configure logging.
    load_dotenv()
    setup_logging()
    logger.info("DocTalk API starting up")

    yield  # <-- app runs here for its whole life; nothing below since we have no teardown


app = FastAPI(
    title="DocTalk",
    description="RAG + agentic assistant. Upload a PDF and chat with it.",
    version="0.1.0",
    lifespan=lifespan,  # <-- wires our startup logic in, replacing @app.on_event
)

app.include_router(router)


@app.get("/")
def health():
    '''a simple health check so you can confirm the server is alive'''
    return {"status": "ok", "message": "DocTalk API is running"}