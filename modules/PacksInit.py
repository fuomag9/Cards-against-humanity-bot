import json
import pickle
from pathlib import Path
from typing import List

import requests

from modules.Call import Call
from modules.Pack import Pack


class PacksInit():
    def __init__(self, pack_json: Path):
        self.packs: List[Pack] = []
        self.pack_json: Path = pack_json

    def check_for_packs_file(self) -> bool:
        return not self.pack_json.is_file()

    def delete_all_packs(self) -> bool:
        if self.pack_json.is_file():
            try:
                self.pack_json.unlink()
            except Exception:
                return False
            return True
        else:
            return False

    def dump_to_pickle(self):
        with open(self.pack_json, "wb") as file:
            data = pickle.dumps(self.packs)
            file.write(data)

    def load_from_pickle(self):
        with open(self.pack_json, "rb") as file:
            data = file.read()
            self.packs = pickle.loads(data)

    def get_packs_names(self) -> list:
        return [pack.name for pack in self.packs]

    def get_pack_by_name(self, pack_name: str) -> Pack:
        for pack in self.packs:
            if pack.name == pack_name:
                return pack

    def get_pack_by_truncatedstr_name(self, pack_name: str, truncated_length: int = 60) -> Pack:
        for pack in self.packs:
            if pack.name[:truncated_length] == pack_name:
                return pack  # Todo: eventually check for duplicates pack, but may not be an issue

    def downloads_packs_data(self, pages) -> None:
        if pages > 101:
            raise ValueError("The page number is too high")  # packs after 100*12 might get boring/useless
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:76.0) Gecko/20100101 Firefox/76.0',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'it-IT,it;q=0.8,en-US;q=0.5,en;q=0.3',
            'Origin': 'https://www.cardcastgame.com',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Cache-Control': 'max-age=0',
            'TE': 'Trailers',
        }
        enumerated_packs = []
        for x in range(1, pages):
            params = (
                ('category', ''),
                ('direction', 'desc'),
                ('limit', '12'),
                ('nsfw', 'true'),
                ('offset', str(x * 12)),
                ('sort', 'rating'),
            )
            response = requests.get('https://api.cardcastgame.com/v1/decks', headers=headers, params=params)
            data = json.loads(response.content)['results']['data']
            del response
            for d in data:
                enumerated_packs.append({'code': d['code'], 'name': d['name'], 'is_nsfw': d['has_nsfw_cards']})

        for pack in enumerated_packs:
            calls_json = json.loads(
                requests.get(f'https://api.cardcastgame.com/v1/decks/{pack["code"]}/calls', headers=headers).content)
            responses_json = json.loads(requests.get(f'https://api.cardcastgame.com/v1/decks/{pack["code"]}/responses',
                                                     headers=headers).content)

            calls_list: List[Call] = [Call(call_list=x['text']) for x in calls_json]
            responses_list = [x['text'][0] for x in responses_json]
            del calls_json, responses_json
            p: Pack = Pack(name=pack['name'], calls=calls_list, responses=responses_list, is_nsfw=pack['is_nsfw'])
            self.packs.append(p)
