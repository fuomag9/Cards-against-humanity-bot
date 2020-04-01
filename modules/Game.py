from typing import List

from modules.Argparse_args import args as argparse_args
from modules.User import User
from modules.Utils import Utils
from modules.Round import Round
import random

db_file = argparse_args["database_file"]
utils = Utils(db_file=db_file)


class Game:
    def __init__(self, chat_id, initiated_by: User = None, rounds: int = 30, packs: List[str] = None):
        """

        :param chat_id: The group chat_id.
        :param initiated_by: The User who started the game
        :param rounds: The number of rounds to play.
        :param packs: The list of packs that will be used in the game.
        """
        self.is_started = None

        self.ignore_messages = False  # ignore messages sent from the group chat
        self.chat_id = chat_id
        self.users: List[User] = []
        self.initiated_by: User = initiated_by
        self.packs = packs
        self.calls = []
        self.rounds: int = rounds
        self.round: (Round, None) = None
        self.judge_index = 0
        self.judge = initiated_by

    def loads_calls(self):
        for pack in self.packs:
            self.calls.append(utils.retrieve_query_results(f"SELECT * from {pack}_calls"))

    def count_call_completitions_spaces(self, call: str) -> int:
        pass

    def is_user_present(self, user: User):
        if self.users is None:
            return False
        for u in self.users:
            if user == u:
                return True
        return False

    def add_user(self, user: User):
        self.users.append(user)

    def remove_user(self, user: User):
        self.users.remove(user)

    def get_user(self, username):
        for user in self.users:
            if user.username == username:
                return user

    def scoreboard(self) -> List:
        """
        Return ordered list of Users by score (max -> min)
        """
        return sorted(self.users, key=lambda x: x.score, reverse=True)

    def new_round(self) -> bool:
        if self.rounds == 0:
            return False
        else:
            chosen_call = random.choice(self.calls)
            completitions = self.count_call_completitions_spaces(chosen_call)
            self.calls.remove(chosen_call)
            self.round = Round(chosen_call, completitions)
            self.rounds -= 1
            return True

    def have_all_users_answered(self):
        return all(user.answer is not None for user in self.users)

    def next_judge(self):
        if self.judge_index + 1 > len(self.users) - 1:
            self.judge_index = 0
        else:
            self.judge_index += 1

        self.judge = self.users[self.judge_index]
