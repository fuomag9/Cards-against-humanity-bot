from datetime import datetime
from typing import List, Optional


class User:
    def __init__(self, username: str, user_id: str):
        self.responses: List[str] = []
        self.last_response_date: Optional[datetime] = None
        self.username = str(username)
        self.user_id = str(user_id)
        self.has_answered = False
        self.score = 0
        self.completition_answers = 0

    def __eq__(self, other):
        if not isinstance(other, User):
            # don't attempt to compare against unrelated types
            return NotImplemented

        return self.user_id == other.user_id
