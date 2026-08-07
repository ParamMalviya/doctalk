import uuid


class SessionStore:
    '''
    holds per-session data in memory, keyed by session_id.
    Option A: simplest approach -- lives in RAM, lost on restart.
    kept behind this small class so it can later be swapped for a
    disk-backed version without touching the routes.
    '''

    def __init__(self):
        # session_id -> {"chunks": [...], "filename": str}
        self._sessions = {}

    def create_session(self, chunks: list, filename: str) -> str:
        '''store a session's data, return a new unique session_id'''
        session_id = uuid.uuid4().hex
        self._sessions[session_id] = {
            "chunks": chunks,
            "filename": filename,
            "pipeline": None,  # filled in once the caller builds it (see set_pipeline)
            "questions_asked": 0,  # bumped by increment_questions on every /chat call
        }
        return session_id

    def increment_questions(self, session_id: str) -> int:
        '''bump this session's question count by one, return the NEW count.
        returns 0 for an unknown session (caller already 404s on that case).'''
        session = self._sessions.get(session_id)
        if session is None:
            return 0
        session["questions_asked"] += 1
        return session["questions_asked"]

    def set_pipeline(self, session_id: str, pipeline) -> None:
        '''cache an already-built pipeline object for this session.
        we don't care WHAT it is (ChatPipeline, or anything else) --
        that's the caller's business, not the store's.'''
        if session_id in self._sessions:
            self._sessions[session_id]["pipeline"] = pipeline

    def get_pipeline(self, session_id: str):
        '''fetch the cached pipeline for a session, or None if not built yet'''
        session = self._sessions.get(session_id)
        return session["pipeline"] if session else None

    def get(self, session_id: str) -> dict:
        '''fetch a session's data, or None if it doesn't exist'''
        return self._sessions.get(session_id)

    def exists(self, session_id: str) -> bool:
        '''check whether a session_id is known'''
        return session_id in self._sessions