import logging
import sqlite3
from functools import wraps
from pathlib import Path

import telegram
from telegram.error import Unauthorized


class Utils:
    def __init__(self, db_file=str(Path.cwd()), bot_updater=None):
        """
        :param db_file: database file
        :type bot_updater: updater.bot of python-telegram-bot
        """
        self.db_file = db_file
        self.bot_updater = bot_updater

    @staticmethod
    def handle_exception(e: Exception) -> None:
        """

        :param Exception e: The exception to handle
        """
        logging.error(e, exc_info=True)

    @staticmethod
    def str2bool(v):
        if isinstance(v, bool):
            return v
        if v.lower() in ('yes', 'true', 't', 'y', '1', 'enable', 'enabled'):
            return True
        elif v.lower() in ('no', 'false', 'f', 'n', '0', 'disable', 'disabled'):
            return False
        else:
            raise ValueError('Boolean value expected.')

    def exec_query(self, query: str) -> None:
        """Executes a SQL query

        :param query: The SQL query to execute

        """

        # Open database connection
        db = sqlite3.connect(self.db_file)
        # prepare a cursor object using cursor() method
        cursor = db.cursor()
        # Prepare SQL query to INSERT a record into the database.
        try:
            # Execute the SQL command
            cursor.execute(query)
            # Commit your changes in the database
            db.commit()
        except Exception as e:
            # Rollback in case there is any error
            self.handle_exception(e)
            db.rollback()
        # disconnect from server
        db.close()

    def retrieve_query_results(self, query: str) -> list:
        """
        Returns a list containing the SQL query results

        :param query: The SQL query to execute
        :rtype: list
        :return: A list containing the query results
        """
        db = sqlite3.connect(self.db_file)
        cursor = db.cursor()
        try:
            cursor.execute(query)
            results = cursor.fetchall()
            return results
        except Exception as e:
            self.handle_exception(e)
            return []  # return empty list
        finally:
            db.close()

    def get_all_table_names(self) -> list:
        return self.retrieve_query_results("""SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;""")

    def drop_table(self, table_name : str) -> None:
        self.exec_query(f"""DROP TABLE IF EXISTS {table_name};""")

    def send_message(self, chatid: str, messaggio: str, html: bool = False, markup=None) -> None:
        """
        Sends a message to a telegram user and sends "typing" action


        :param chatid: The chatid of the user who will receive the message
        :param messaggio: The message who the user will receive
        :param html: Enable html markdown parsing in the message
        :param markup: The reply_markup to use when sending the message
        """

        bot = self.bot_updater

        try:
            bot.send_chat_action(chat_id=chatid, action="typing")
            if html and markup is not None:
                bot.send_message(chat_id=chatid, text=messaggio,
                                 parse_mode=telegram.ParseMode.HTML,
                                 reply_markup=markup)
            elif html:
                bot.send_message(chat_id=chatid, text=messaggio,
                                 parse_mode=telegram.ParseMode.HTML)
            elif markup is not None:
                bot.send_message(chat_id=chatid, text=messaggio,
                                 reply_markup=markup)
            else:
                bot.send_message(chat_id=chatid, text=messaggio)
        except Unauthorized:  # user blocked the bot
            pass
        except Exception as e:
            Utils.handle_exception(e)

    def send_image(self, chatid: str, image, html: bool = False, markup=None, caption=None) -> None:
        """
        Sends an image to a telegram user and sends "sending image" action

        :param chatid: The chatid of the user who will receive the message
        :param image: The image to send
        :param html: Enable html markdown parsing in the message
        :param markup: The reply_markup to use when sending the message
        :param caption: image caption
        """
        bot = self.bot_updater

        try:
            bot.send_chat_action(chatid, action="upload_photo")
            if html and markup is not None and caption is not None:
                bot.send_photo(chat_id=chatid, photo=image, parse_mode=telegram.ParseMode.HTML, reply_markup=markup,
                               caption=caption)
            elif html and markup is not None:
                bot.send_photo(chat_id=chatid, photo=image, parse_mode=telegram.ParseMode.HTML, reply_markup=markup
                               )
            elif markup is not None and caption is not None:
                bot.send_photo(chat_id=chatid, photo=image, reply_markup=markup,
                               caption=caption)
            elif html and caption is not None:
                bot.send_photo(chat_id=chatid, photo=image, parse_mode=telegram.ParseMode.HTML, caption=caption)
            elif html:
                bot.send_photo(chat_id=chatid, photo=image, parse_mode=telegram.ParseMode.HTML)
            elif markup is not None:
                bot.send_photo(chat_id=chatid, photo=image, reply_markup=markup)
            elif caption is not None:
                bot.send_photo(chat_id=chatid, photo=image, caption=caption)
            else:
                bot.send_photo(chat_id=chatid, photo=image)
        except Unauthorized:  # user blocked the bot
            pass
        except Exception as e:
            Utils.handle_exception(e)
