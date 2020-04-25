from typing import List

from modules.Argparse_args import args as argparse_args
from modules.Call import Call
from modules.User import User
from modules.Utils import Utils
from modules.Round import Round
from modules.Pack import Pack
from modules.PackList import PackList
from multimethod import multimethod
import random

db_file = argparse_args["database_file"]
utils = Utils(db_file=db_file)


class Game:
    def __init__(self, chat_id, packlist: PackList, initiated_by: User = None, rounds: int = 30,
                 max_responses_per_user=8):
        """

        :param chat_id: The group chat_id.
        :param initiated_by: The User who started the game
        :param rounds: The number of rounds to play.
        :param packlist: The PackList that will be used in the game.
        """
        self.is_started = None

        self.ignore_messages = False  # ignore messages sent from the group chat
        self.chat_id = chat_id
        self.users: List[User] = []
        self.initiated_by: User = initiated_by
        self.packlist: PackList = packlist
        self.rounds: int = rounds
        self.round: (Round, None) = None
        self.judge_index = 0
        self.judge: User = initiated_by
        self.max_responses_per_user: int = max_responses_per_user

    def get_random_call(self) -> Call:
        # Todo: handle when calls are 0
        chosen_call = random.choice(self.packlist.calls)
        self.packlist.calls.remove(chosen_call)
        return chosen_call

    def get_random_response(self):
        # Todo: handle when responses are 0
        chosen_response = random.choice(self.packlist.responses)
        self.packlist.responses.remove(chosen_response)
        return chosen_response

    @multimethod
    def is_user_present(self, user: User):
        if self.users is None:
            return False
        return self.get_user(user) is not None

    @multimethod
    def is_user_present(self, username: str):
        if self.users is None:
            return False
        hypotetical_user = User(username)
        return self.get_user(hypotetical_user) is not None

    def add_user(self, user: User):
        self.users.append(user)

    def remove_user(self, user: User):
        self.users.remove(user)

    @multimethod
    def get_user(self, username) -> (User, None):
        for user in self.users:
            if user.username == username:
                return user
        return None

    @get_user.register
    def get_user(self, searched_user) -> (User, None):
        for user in self.users:
            if searched_user.username == user.username:
                return user
        return None

    def fill_user_responses(self, user: User):
        number_of_responses_needed: int = self.max_responses_per_user - len(user.responses)
        for _ in range(0, number_of_responses_needed):
            user.responses.append(self.get_random_response())

    def scoreboard(self) -> List:
        """
        Return ordered list of Users by score (max -> min)
        """
        return sorted(self.users, key=lambda x: x.score, reverse=True)

    def new_round(self) -> bool:
        if self.rounds == 0:
            return False
        else:
            chosen_call: Call = self.get_random_call()
            # assumo chosen_call.replacements < self.max_responses_per_user
            for user in self.users:
                self.fill_user_responses(user)
            self.round = Round(chosen_call)
            self.rounds -= 1
            return True

    def have_all_users_answered(self):
        return all(user.has_answered is True for user in self.users)

    def next_judge(self):
        if self.judge_index + 1 > len(self.users) - 1:
            self.judge_index = 0
        else:
            self.judge_index += 1

        self.judge = self.users[self.judge_index]
