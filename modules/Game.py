from __future__ import annotations

import random
from typing import List, Union, Dict, Optional

from multimethod import multimethod
from telegram import InlineKeyboardMarkup, InlineKeyboardButton

from modules.Call import Call
from modules.MultiPack import MultiPack
from modules.PackSelectionUI import PackSelectionUI
from modules.PacksInit import PacksInit
from modules.Round import Round
from modules.User import User


class Game:
    def __init__(self, chat_id, packlist: MultiPack = None, started_by: User = None, rounds: int = 30,
                 max_responses_per_user=8):
        """

        :param chat_id: The group chat_id.
        :param started_by: The User who started the game
        :param rounds: The number of rounds to play.
        :param packlist: The PackList that will be used in the game.
        """
        self.is_started = None

        self.chat_id = chat_id
        self.users: List[User] = []
        self.started_by: User = started_by
        self.multipack: Optional[MultiPack] = packlist
        self.multipack_backup: Optional[MultiPack] = packlist
        self.rounds = rounds
        self.remaining_rounds: int = rounds
        self.round: Optional[Round] = None
        self.judge_index = 0
        self.judge: User = started_by
        self.max_responses_per_user: int = max_responses_per_user
        self.pack_selection_ui = PackSelectionUI()
        self.cannot_delete_message_sent = False

    @staticmethod
    def create_game(started_by: User, chatid) -> Game:
        group_game = Game(chatid, started_by=started_by)
        group_game.add_user(started_by)
        group_game.is_started = False
        return group_game

    def get_random_call(self) -> Optional[Call]:
        try:
            chosen_call = random.choice(self.multipack.calls)
            self.multipack.calls.remove(chosen_call)
            return chosen_call
        except IndexError:
            return None

    def get_random_response(self) -> Optional[str]:
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

        return self.get_user(user.user_id) is not None

    @multimethod
    def is_user_present(self, user_id: str) -> bool:
        if self.users is None:
            return False

        return self.get_user(user_id) is not None

    def add_user(self, user: User):
        self.users.append(user)

    def remove_user(self, user: User):
        self.users.remove(user)

    def get_user(self, user_id) -> Optional[User]:
        for user in self.users:
            if user.user_id == user_id:
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
        return string_status[:-1]

    def new_round(self) -> bool:
        if self.remaining_rounds == 0:
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
                self.round.reset_user_answers(user)
            self.remaining_rounds -= 1
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
    def find_game_from_userid(user_id, groups_dict: {}) -> Union[Game, False, None]:
        """

        :param user_id: The user_id to search for
        :param groups_dict: The groups_dict to search into
        :return: Game if a game is found, False if a game is not found or None if there are multiple games
        """
        game: Optional[Game] = None
        game_count: int = 0

        # Todo: this could be optimized since joining multiple games should not be allowed
        for searched_game in list(groups_dict.values()):
            inline_user: User = searched_game.get_user(user_id)
            if inline_user is not None:
                game: Game = searched_game
                game_count += 1
                if game_count > 1:
                    return None
        if game_count == 0:
            return False
        return game

    @staticmethod
    def find_game_from_chatid(chatid, groups_dict: Dict) -> Optional[Game]:
        """
        :param chatid:
        :param groups_dict:
        :return: Game if found else False
        """
        return groups_dict.get(chatid) if chatid in groups_dict.keys() else False

    def generate_packs_markup(self, p: PacksInit) -> InlineKeyboardMarkup:
        """
        Generates inline keyboard markup from a PacksInit instance
        :param p: PacksInit
        :return: InlineKeyboardMarkup
        """
        min_index = self.pack_selection_ui.page_index * self.pack_selection_ui.items_per_page
        max_index = min_index + self.pack_selection_ui.items_per_page
        packs_to_use_in_keyboard: List[str] = p.get_packs_names()[min_index:max_index]
        packs_keyboard = []
        for pack_name in packs_to_use_in_keyboard:
            if pack_name in self.pack_selection_ui.pack_names:
                packs_keyboard.append([InlineKeyboardButton(f"{pack_name} ✔", callback_data=f'{pack_name[:60]}_ppp')])
            else:
                packs_keyboard.append([InlineKeyboardButton(pack_name, callback_data=f'{pack_name[:60]}_ppp')])
        packs_keyboard.append([InlineKeyboardButton(">>>", callback_data='>>>_next_pack_page')])
        reply_markup = InlineKeyboardMarkup(packs_keyboard)
        return reply_markup
