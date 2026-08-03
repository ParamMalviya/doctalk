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
        }
        return session_id

    def get(self, session_id: str) -> dict:
        '''fetch a session's data, or None if it doesn't exist'''
        return self._sessions.get(session_id)

    def exists(self, session_id: str) -> bool:
        '''check whether a session_id is known'''
        return session_id in self._sessions