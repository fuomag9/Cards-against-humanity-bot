from typing import List


class PackSelectionUI:
    def __init__(self, items_per_page: int = 8):
        self.page_index: int = 0
        self.items_per_page: int = items_per_page
        self.pack_names: List[str] = []
