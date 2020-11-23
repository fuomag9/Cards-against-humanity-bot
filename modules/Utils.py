import logging
from typing import Optional

import telegram
from telegram.error import Unauthorized


class Utils:
    def __init__(self, bot_updater=None):
        """
        :type bot_updater: updater.bot of python-telegram-bot
        """

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

    def send_message(self, chatid: str, messaggio: str, html: bool = False, markup=None,
                     disable_notification: bool = None) -> Optional[telegram.Message]:
        """
        Sends a message to a telegram user and sends "typing" action


        :param chatid: The chatid of the user who will receive the message
        :param messaggio: The message who the user will receive
        :param html: Enable html markdown parsing in the message
        :param markup: The reply_markup to use when sending the message
        :param disable_notification: Disable message notification
        """

        bot = self.bot_updater

        try:
            bot.send_chat_action(chat_id=chatid, action="typing")
            return bot.send_message(chat_id=chatid, text=messaggio,
                                    parse_mode=telegram.ParseMode.HTML if html else None,
                                    reply_markup=markup, disable_notification=disable_notification)
        except Unauthorized:  # user blocked the bot
            pass
        except Exception as e:
            Utils.handle_exception(e)

    def send_image(self, chatid: str, image, html: bool = False, markup=None, caption=None) -> Optional[
        telegram.Message]:
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
                return bot.send_photo(chat_id=chatid, photo=image, parse_mode=telegram.ParseMode.HTML,
                                      reply_markup=markup,
                                      caption=caption)
            elif html and markup is not None:
                return bot.send_photo(chat_id=chatid, photo=image, parse_mode=telegram.ParseMode.HTML,
                                      reply_markup=markup
                                      )
            elif markup is not None and caption is not None:
                return bot.send_photo(chat_id=chatid, photo=image, reply_markup=markup,
                                      caption=caption)
            elif html and caption is not None:
                return bot.send_photo(chat_id=chatid, photo=image, parse_mode=telegram.ParseMode.HTML, caption=caption)
            elif html:
                return bot.send_photo(chat_id=chatid, photo=image, parse_mode=telegram.ParseMode.HTML)
            elif markup is not None:
                return bot.send_photo(chat_id=chatid, photo=image, reply_markup=markup)
            elif caption is not None:
                return bot.send_photo(chat_id=chatid, photo=image, caption=caption)
            else:
                return bot.send_photo(chat_id=chatid, photo=image)
        except Unauthorized:  # user blocked the bot
            pass
        except Exception as e:
            Utils.handle_exception(e)

    def warning_if_not_group(self, chat_type, chatid, insert_string) -> bool:
        """
        :param chat_type:
        :param chatid:
        :param insert_string:
        :return: True if not group warning was sent, else False
        """
        if not chat_type.endswith("group"):
            self.send_message(chatid, f"You can only {insert_string} in a group!")
            return True
        else:
            return False
