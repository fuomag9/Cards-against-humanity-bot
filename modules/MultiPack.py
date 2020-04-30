from typing import List

from modules.Pack import Pack


class MultiPack(Pack):
    def __init__(self, packs_list: List[Pack]):
        c_p = []
        r_p = []
        for pack in packs_list:
            for call in pack.calls:
                c_p.append(call)
            for response in pack.responses:
                r_p.append(response)

        super().__init__(None, list(set(c_p)), list(set(r_p)))
        del self.name
