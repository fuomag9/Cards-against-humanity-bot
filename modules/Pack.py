import random


class Pack:
    def __init__(self, name, calls, responses, is_nsfw=False):
        self.name: str = name
        self.calls: [] = calls
        self.responses: [] = responses
        self.is_nsfw: bool = is_nsfw

    @property
    def calls_count(self):
        return len(self.calls)

    @property
    def answers_count(self):
        return len(self.responses)

    def get_random_response(self):
        return random.choice(self.responses)

    def get_random_call(self) -> dict:
        chosen_call = random.choice(self.calls)
        return {"call": chosen_call, "replacements": len(chosen_call) - 1}
