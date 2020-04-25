from typing import Dict, List

from modules.Call import Call
from modules.User import User


class Round:
    def __init__(self, call: Call):
        self.is_answering_mode = False
        self.is_judging_mode = False
        self.call: Call = call
        self.answers: Dict[User: List[str]] = {}

    def get_user_answers(self, user: User) -> List[str]:
        return self.answers[user]

    def get_all_answers(self) -> List[List[str]]:
        return [self.get_user_answers(user) for user in self.answers.keys()]
