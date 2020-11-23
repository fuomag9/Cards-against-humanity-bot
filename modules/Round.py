from typing import Dict, List, Optional

import telegram
from multimethod import multimethod

from modules.Call import Call
from modules.User import User


class Round:
    def __init__(self, call: Call):
        self.is_answering_mode = True
        self.is_judging_mode = False
        self.call: Call = call
        self.answers: Dict[str: List[str]] = {}  # [username : List[answer]]
        self.choose_winner_message: Optional[telegram.Message] = None

    @multimethod
    def get_user_answers(self, user_id: str) -> List[str]:
        return self.answers[user_id]

    @multimethod
    def get_user_answers(self, user: User) -> List[str]:
        return self.answers[user.user_id]

    def get_all_answers(self) -> List[List[str]]:
        return [self.get_user_answers(user_id) for user_id in self.answers.keys()]

    @multimethod
    def reset_user_answers(self, user_id: str):
        self.answers[user_id] = []

    @multimethod
    def reset_user_answers(self, user: User):
        self.answers[user.user_id] = []

    @multimethod
    def delete_user_answers(self, user_id: str):
        del self.answers[user_id]

    @multimethod
    def delete_user_answers(self, user: User):
        self.delete_user_answers(user.user_id)

    @multimethod
    def get_answers(self, user: User):
        return self.answers[user.user_id]

    @multimethod
    def get_answers(self, user_id: str):
        return self.answers[user_id]
