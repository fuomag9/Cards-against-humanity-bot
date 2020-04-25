from datetime import datetime
from typing import List

from modules.Argparse_args import args as argparse_args
from modules.Utils import Utils

db_file = argparse_args["database_file"]
utils = Utils(db_file=db_file)


class User:
    def __init__(self, username: str):
        self.responses: (List[str], None) = None
        self.last_response_date: (datetime, None) = None
        self.username = username
        self.has_answered = False
        self.score = 0
        self.completition_answers = 0

    def __eq__(self, other):
        if not isinstance(other, User):
            # don't attempt to compare against unrelated types
            return NotImplemented

        return self.username == other.username
