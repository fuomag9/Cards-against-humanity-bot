from datetime import datetime
from typing import List, Union


class User:
    def __init__(self, username: str):
        self.responses: List[str] = []
        self.last_response_date: Union[datetime, None] = None
        self.username = username
        self.has_answered = False
        self.score = 0
        self.completition_answers = 0

    def __eq__(self, other):
        if not isinstance(other, User):
            # don't attempt to compare against unrelated types
            return NotImplemented

        return self.username == other.username
