from modules.Argparse_args import args as argparse_args
from modules.Utils import Utils
import re

db_file = argparse_args["database_file"]
utils = Utils(db_file=db_file)


class Packs:
    def __init__(self):
        self.packs: dict(dict(dict())) = {}  # packs(pack_name:{calls: [], responses:[]})

    def delete_all_question_tables(self) -> None:
        packs = self.get_pack_table_names()
        for pack in packs:
            utils.drop_table(pack)

    def get_pack_table_names(self):
        tables_names = utils.get_all_table_names()
        packs = []
        for table in tables_names:
            if re.search("(_calls)|(_responses)",
                         table) is not None:  # Todo: check if packs can have _calls or _responses in their name
                packs.append(table)

    def get_pack_names(self) -> list:
        return [pack.replace("_calls", "").replace("_responses", "") for pack in self.get_pack_table_names()]

    def create_pack_calls_table(self, pack_name) -> None:
        utils.exec_query(f"""
        create table {pack_name}_calls
(
	call text not null
);

create unique index pack_name_calls_call_uindex
	on {pack_name}_calls (call);
	
	""")

    def create_pack_responses_table(self, pack_name) -> None:
        utils.exec_query(f"""
                create table {pack_name}_responses
        (
        	response text not null
        );

        create unique index pack_name_calls_call_uindex
        	on {pack_name}_responses (response);

        	""")

    def fill_pack_calls_data(self, pack_name, data) -> None:
        for string in data:
            utils.exec_query(f"""INSERT INTO {pack_name}_calls VALUES ({string})""")

    def fill_pack_responses_data(self, pack_name, data) -> None:
        for string in data:
            utils.exec_query(f"""INSERT INTO {pack_name}_responses VALUES ({string})""")

    def inizialize_pack_database(self):
        """
        Initialize packs DB and downloads data in it
        """
        self.downloads_packs_data()
        for pack in self.packs:
            self.create_pack_calls_table(pack)
            self.fill_pack_calls_data(pack, pack["calls"])
            self.create_pack_responses_table(pack)
            self.fill_pack_calls_data(pack, pack["responses"])
        self.packs = {}

    def get_pack_responses(self, pack_name) -> list:
        utils.retrieve_query_results(f"SELECT * FROM {pack_name}_responses")

    def get_pack_calls(self, pack_name) -> list:
        utils.retrieve_query_results(f"SELECT * FROM {pack_name}_calls")

    def downloads_packs_data(self) -> None:
        pass  # Todo:implement data downloading
