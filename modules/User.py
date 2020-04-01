from datetime import datetime
from itertools import islice

from modules.Argparse_args import args as argparse_args
from modules.Utils import Utils

db_file = argparse_args["database_file"]
utils = Utils(db_file=db_file)


class User:
    def __init__(self, username: str):
        self.answer: (str, None) = None
        self.responses_dict: dict = {str: int}  # set name with _questions tables -> response line number in db table
        self.last_response_date: (datetime, None) = None
        self.username = username
        self.has_answered = False
        self.score = 0
        self.completition_answers = 0

    def __eq__(self, other):
        if not isinstance(other, User):
            # don't attempt to compare against unrelated types
            return NotImplemented

        return self.username == other.username

    # Per ricavare l'indice della risposta selezionata semplicemente utilizzare l'indice della risposta scelta da quelle
    # ricavate e utilizzare lo stesso indice in responses_dict, facendo attenzione col del (verranno shiftati dopo l'elimin!)

    @property
    def responses(self):
        output = []
        for table_name, question_id in list(self.responses_dict.items()):
            output.append(utils.retrieve_query_results(f"SELECT * from {table_name} WHERE ROWID = {question_id};"))
        return output

    def remove_response(self, response: str, index_p: int = None) -> None:
        """

        :param response: The response to remove
        :param index_p: The response index to remove. If this is used the response parameter is ignored
        """
        if index_p is not None:
            index = index_p
        else:
            index = self.responses.index(response)
        del self.responses_dict[next(islice(self.responses_dict, index, None))]
