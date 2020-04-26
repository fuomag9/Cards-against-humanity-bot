from typing import Dict, List

from modules.Call import Call
from modules.User import User


class Round:
    def __init__(self, call: Call):
        self.is_answering_mode = True
        self.is_judging_mode = False
        self.call: Call = call
        self.answers: Dict[str: List[str]] = {}

    def get_user_answers(self, username: str) -> List[str]:
        return self.answers[username]

    def get_all_answers(self) -> List[List[str]]:
        return [self.get_user_answers(username) for username in self.answers.keys()]

    def init_user_answers(self, username: str):
        self.answers[username] = []
