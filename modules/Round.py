from modules.Call import Call


class Round:
    def __init__(self, call: Call):
        self.is_answering_mode = False
        self.is_judging_mode = False
        self.call: Call = call
