from typing import List

from modules.User import User


class Round:
    def __init__(self, call: str, call_completitions_spaces: int):
        self.is_answering_mode = False
        self.is_judging_mode = False
        self.call = call
        self.call_completitions_spaces = call_completitions_spaces
