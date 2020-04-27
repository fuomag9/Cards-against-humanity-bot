from typing import Dict, List

from multimethod import multimethod

from modules.Call import Call
from modules.User import User


class Round:
    def __init__(self, call: Call):
        self.is_answering_mode = True
        self.is_judging_mode = False
        self.call: Call = call
        self.answers: Dict[str: List[str]] = {}  # [username : List[answer]]

    def get_user_answers(self, username: str) -> List[str]:
        return self.answers[username]

    def get_all_answers(self) -> List[List[str]]:
        return [self.get_user_answers(username) for username in self.answers.keys()]

    @multimethod
    def reset_user_answers(self, username: str):
        self.answers[username] = []

    @multimethod
    def reset_user_answers(self, user: User):
        self.answers[user.username] = []

    @multimethod
    def delete_user_answers(self, username: str):
        del self.answers[username]

    @multimethod
    def delete_user_answers(self, user: User):
        self.delete_user_answers(user.username)
