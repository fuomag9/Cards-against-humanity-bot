import random
from typing import List, Optional

from modules.Call import Call


class Pack:
    def __init__(self, name: Optional[str], calls: List[Call], responses: List[str], is_nsfw=False):
        self.name: str = name
        self.calls: List[Call] = calls
        self.responses: List[str] = responses
        self.is_nsfw: bool = is_nsfw

    @property
    def calls_count(self):
        return len(self.calls)

    @property
    def response_count(self):
        return len(self.responses)

    def get_random_response(self):
        return random.choice(self.responses)

    def get_random_call(self) -> Call:
        return random.choice(self.calls)
