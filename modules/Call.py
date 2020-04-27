class Call:
    def __init__(self, call_list: []):
        self.call_list = call_list

    def get_formatted_call(self) -> str:
        return "_".join(self.call_list)

    @property
    def replacements(self):
        return len(self.call_list) - 1

    def __eq__(self, other):
        if not isinstance(other, Call):
            # don't attempt to compare against unrelated types
            return NotImplemented

        return self.call_list == other

    def __hash__(self):
        return hash(self.get_formatted_call())
