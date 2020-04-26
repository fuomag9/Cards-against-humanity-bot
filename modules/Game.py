from __future__ import annotations

import random
from typing import List, Union

from multimethod import multimethod

from modules.Call import Call
from modules.MultiPack import MultiPack
from modules.PackSelectionUI import PackSelectionUI
from modules.Round import Round
from modules.User import User
import copy


class Game:
    def __init__(self, chat_id, packlist: MultiPack = None, initiated_by: User = None, rounds: int = 30,
                 max_responses_per_user=8):
        """

        :param chat_id: The group chat_id.
        :param initiated_by: The User who started the game
        :param rounds: The number of rounds to play.
        :param packlist: The PackList that will be used in the game.
        """
        self.is_started = None

        self.chat_id = chat_id
        self.users: List[User] = []
        self.initiated_by: User = initiated_by
        self.multipack: (MultiPack, None) = packlist
        self.multipack_backup: (MultiPack, None) = packlist
        self.rounds: int = rounds
        self.round: (Round, None) = None
        self.judge_index = 0
        self.judge: User = initiated_by
        self.max_responses_per_user: int = max_responses_per_user
        self.pack_selection_ui = PackSelectionUI()
        self.can_remove_people_message = True

    def get_random_call(self) -> Union[Call, None]:
        try:
            chosen_call = random.choice(self.multipack.calls)
            self.multipack.calls.remove(chosen_call)
            return chosen_call
        except IndexError:
            return None

    def get_random_response(self) -> Union[str, None]:
        try:
            chosen_response = random.choice(self.multipack.responses)
            self.multipack.responses.remove(chosen_response)
            return chosen_response
        except IndexError:
            return None

    @multimethod
    def is_user_present(self, user: User) -> bool:
        if self.users is None:
            return False

        return self.get_user(user.username) is not None

    @multimethod
    def is_user_present(self, username: str) -> bool:
        if self.users is None:
            return False

        return self.get_user(username) is not None

    def add_user(self, user: User):
        self.users.append(user)

    def remove_user(self, user: User):
        self.users.remove(user)

    @multimethod
    def get_user(self, username) -> Union[User, None]:
        for user in self.users:
            if user.username == username:
                return user
        return None

    @get_user.register
    def get_user(self, searched_user: str) -> Union[User, None]:
        for user in self.users:
            if searched_user == user.username:
                return user
        return None

    def fill_user_responses(self, user: User):
        number_of_responses_needed: int = self.max_responses_per_user - len(user.responses)
        for _ in range(0, number_of_responses_needed):
            random_response = self.get_random_response()
            if random_response is None:
                self.multipack.responses = self.multipack_backup.responses.copy()
                # Todo: notify that responses have been refilled
                random_response = self.get_random_response()
            user.responses.append(random_response)

    def scoreboard(self) -> List[User]:
        """
        Return ordered list of Users by score (max -> min)
        """
        return sorted(self.users, key=lambda x: x.score, reverse=True)

    def get_formatted_scoreboard(self) -> str:
        string_status = ""
        for username, score in [(u.username, u.score) for u in self.scoreboard()]:
            string_status += f"{username}: {score} points\n"
        return string_status

    def new_round(self) -> bool:
        if self.rounds == 0:
            return False
        else:
            chosen_call: Call = self.get_random_call()
            if chosen_call is None:
                # Todo: eventually print that calls have been reloaded
                self.multipack.calls = self.multipack_backup.calls.copy()
                chosen_call: Call = self.get_random_call()

            self.next_judge()
            self.round = Round(chosen_call)
            for user in self.users:
                self.fill_user_responses(user)
                user.has_answered = False
                user.completition_answers = 0
                self.round.reset_user_answers(user.username)
            self.rounds -= 1
            return True

    def have_all_users_answered(self):
        return all(user.has_answered is True for user in list(filter(lambda x: x != self.judge, self.users)))

    def next_judge(self):
        if self.judge_index + 1 > len(self.users) - 1:
            self.judge_index = 0
        else:
            self.judge_index += 1

        self.judge = self.users[self.judge_index]

    @staticmethod
    def find_game_from_username(username, groups_dict: {}) -> Union[Game, False, None]:
        inline_user: Union[User, None] = None
        game: Union[Game, None] = None
        game_count: int = 0

        for searched_game in list(groups_dict.values()):
            inline_user: User = searched_game.get_user(username)
            if inline_user is not None:
                game: Game = searched_game
                game_count += 1
                if game_count > 1:
                    return None
        if game_count == 0:
            return False
        return game
