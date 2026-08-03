from pydantic import BaseModel


class UploadResponse(BaseModel):
    '''what /upload returns after ingesting a pdf'''
    session_id: str
    filename: str
    num_chunks: int
    message: str


class ChatRequest(BaseModel):
    '''what a client must send to /chat'''
    session_id: str
    question: str


class ChatResponse(BaseModel):
    '''what /chat returns'''
    answer: str