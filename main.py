from fastapi import FastAPI
from dotenv import load_dotenv

from doctalk.logger import setup_logging, logger
from doctalk.api.routes import router


app = FastAPI(
    title="DocTalk",
    description="RAG + agentic assistant. Upload a PDF and chat with it.",
    version="0.1.0",
)

app.include_router(router)


@app.on_event("startup")
def on_startup():
    # load .env so GOOGLE_API_KEY (and the other keys) are in the environment,
    # then configure logging. both run once when the server boots.
    load_dotenv()
    setup_logging()
    logger.info("DocTalk API starting up")


@app.get("/")
def health():
    '''a simple health check so you can confirm the server is alive'''
    return {"status": "ok", "message": "DocTalk API is running"}