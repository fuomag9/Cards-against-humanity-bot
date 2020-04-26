class Call:
    def __init__(self, call: [], replacements: int):
        self.call = call
        self.replacements = replacements

    def get_formatted_call(self) -> str:
        return "_".join(self.call)
