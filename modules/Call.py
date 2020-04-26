class Call:
    def __init__(self, call: [], replacements: int):
        self.call = call
        self.replacements = replacements

    def get_formatted_call(self) -> str:
        return "_".join(self.call)

    def __eq__(self, other):
        if not isinstance(other, Call):
            # don't attempt to compare against unrelated types
            return NotImplemented

        return self.call == other

    def __hash__(self):
        return hash(self.get_formatted_call())
