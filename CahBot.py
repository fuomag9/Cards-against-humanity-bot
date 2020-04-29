import copy
import logging
from pathlib import Path
from typing import Dict

import telegram
from telegram import InlineQueryResultArticle, InputTextMessageContent, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, Updater, InlineQueryHandler, MessageHandler, Filters, CallbackQueryHandler

from modules.Argparse_args import args as argparse_args
from modules.BackupHandler import BackupHandler
from modules.Game import Game
from modules.MultiPack import MultiPack
from modules.PacksInit import PacksInit
from modules.User import User
from modules.Utils import Utils

updater = Updater(token=argparse_args["key"], use_context=True)
dispatcher = updater.dispatcher
bot = updater.bot  # bot class instance

bot_path = argparse_args["working_folder"]
# auto_remove = Utils.str2bool(argparse_args["remove"])
# admin_pw = argparse_args["admin_password"]
logging_file = argparse_args["logging_file"]
admin_mode = Utils.str2bool(argparse_args["admin_mode"])
persistence = Utils.str2bool(argparse_args["persistence"])
db_file = argparse_args["database_file"]
self_file_folder = Path(__file__).resolve().parent

#Todo: eventually research for potentially RCE in input data due to pickle
packs_file = self_file_folder / "packs.pickle"
groups_file = self_file_folder / "groups.pickle"

logging_level = logging.INFO
if not Utils.str2bool(argparse_args["enable_logging"]):
    logging_level = 99  # stupid workaround not to log -> only creates file

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging_level, filename=logging_file)

utils = Utils(db_file, bot)
packs = PacksInit(pack_json=packs_file)

groups_dict : Dict[str, Game] = {}
backup_handler = BackupHandler(groups_dict, groups_file)



def help(update, context) -> None:
    chatid = update.message.chat_id
    utils.send_message(chatid, """Hello""")


def new_game(update, context) -> None:
    chatid = update.message.chat_id
    username = update.message.from_user.username
    chat_type = update.message.chat.type
    if not chat_type.endswith("group"):
        utils.send_message(chatid, "You can only create a new game in a group!")
        return
    if chatid not in groups_dict.keys():
        admin_user = User(username)
        group_game = Game(chatid)
        group_game.initiated_by = admin_user
        group_game.add_user(admin_user)
        group_game.is_started = False
        groups_dict[chatid] = group_game
        utils.send_message(chatid,
                           f"Game started! Use /join to enter the game and /set_packs to chose your packs and /start_game to start it!")
    else:
        utils.send_message(chatid, "A game is already in progress!")
        # Todo: eventually implement game timer and stopping


def start_game(update, context) -> None:
    chatid = update.message.chat_id
    username = update.message.from_user.username
    chat_type = update.message.chat.type
    if not chat_type.endswith("group"):
        utils.send_message(chatid, "You can only start a game in a group!")
    elif not chatid in groups_dict.keys():
        utils.send_message(chatid, "There's no game to start, create one with /new_game")
    else:
        game: Game = groups_dict[chatid]
        if game.is_started:
            utils.send_message(chatid, "You can't start a game that's already started!")
        else:
            list_of_packs = [packs.get_pack_by_truncatedstr_name(pack_name=pack_name) for pack_name in
                             game.pack_selection_ui.pack_names]
            if list_of_packs == []:
                utils.send_message(chatid, "You can't start a game with no pack selected!")
                return
            elif len(game.users) == 1:
                utils.send_message(chatid, "You need at least 2 people to start a game!")
                return
            game.is_started = True
            game.multipack = MultiPack(list_of_packs)
            game.multipack_backup = copy.deepcopy(game.multipack)
            utils.send_message(chatid, "Game started!")
            game.new_round()
            utils.send_message(chatid, f"{game.judge.username} is asking:\n{game.round.call.get_formatted_call()}")
            bot.delete_message(chatid, game.pack_selection_ui.message_selection_id)


def actually_end_game(chatid) -> None:
    game = groups_dict[chatid]
    if len(game.scoreboard()) == 0:
        utils.send_message(chatid, "Game ended! I don't know who won since everyone left :(")
        return
    if game.is_started == False:
        utils.send_message(chatid, "Game ended! I don't who won since the game never started")
        return
    winner: User = game.scoreboard()[0]
    utils.send_message(chatid, f"Game ended!\n@{winner.username} won with a score of {winner.score}")
    utils.send_message(chatid, f"Here's the full scoreboard:\n{game.get_formatted_scoreboard()}")
    del groups_dict[chatid]


def end_game(update, context) -> None:
    chatid = update.message.chat_id
    username = update.message.from_user.username
    chat_type = update.message.chat.type
    if not chat_type.endswith("group"):
        utils.send_message(chatid, "You can only end a game in a group!")
        return
    if chatid in groups_dict.keys():
        actually_end_game(chatid)
    else:
        utils.send_message(chatid, "There's no active game to end!")


def join(update, context) -> None:
    chatid = update.message.chat_id
    username = update.message.from_user.username
    chat_type: str = update.message.chat.type
    if not chat_type.endswith("group"):
        utils.send_message(chatid, "You can only join a game in a group!")
    elif chatid in groups_dict.keys():
        game: Game = groups_dict.get(chatid)
        user = User(username)
        if user.username is None:
            utils.send_message(chatid,"I'm sorry but you need to have an username to join a game")
            return
        if game.is_started:
            utils.send_message(chatid, "You cannot join a game that has already started!")

        found_game = game.find_game_from_username(user.username, groups_dict)
        if found_game is None:
            utils.send_message("You cannot join more than one game at the same time for now, sorry :(")
        elif found_game is False:
            game.add_user(user)
            utils.send_message(chatid, f"{user.username} joined the game!")
        else:
            utils.send_message(chatid, f"{user.username} has already joined the game!")
    else:
        utils.send_message(chatid, "There is no game running! Start one with /new_game")


def set_packs(update, context) -> None:
    chatid = update.message.chat_id
    username = update.message.from_user.username
    chat_type = update.message.chat.type
    if not chat_type.endswith("group"):
        utils.send_message(chatid, "You can only set game packs in a group!")
        return
    elif chatid in groups_dict.keys():
        game: Game = groups_dict[chatid]

    if game.is_started:
        utils.send_message(chatid, "You cannot chose packs after a game has started!")
        return

    if game.pack_selection_ui.message_selection_id is not None:
        utils.send_message(chatid,"You already have a pack selection interface open!")
        return

    game.pack_selection_ui.message_selection_id = 0 # so it counts as "opened"

    min_index = game.pack_selection_ui.page_index * game.pack_selection_ui.items_per_page
    max_index = min_index + game.pack_selection_ui.items_per_page
    packs_to_use_in_keyboard: List[str] = packs.get_packs_names()[min_index:max_index]
    packs_keyboard = []
    for pack_name in packs_to_use_in_keyboard:
        if pack_name in game.pack_selection_ui.pack_names:
            packs_keyboard.append([InlineKeyboardButton(f"{pack_name} ✔", callback_data=f'{pack_name[:60]}_ppp')])
        else:
            packs_keyboard.append([InlineKeyboardButton(pack_name, callback_data=f'{pack_name[:60]}_ppp')])

    packs_keyboard.append([InlineKeyboardButton(">>>", callback_data=f'>>>_next_pack_page')])
    reply_markup = InlineKeyboardMarkup(packs_keyboard)

    utils.send_message(chatid, "Click on the packs you'd like to use:", markup=reply_markup, html=True)


def set_packs_callback(update, context) -> None:
    query: str = update.callback_query
    chatid = query.message.chat.id
    chat_type = query.message.chat.type

    if not chat_type.endswith("group"):
        return
    if not chatid in groups_dict.keys():
        return
    game: Game = groups_dict[chatid]

    selected_pack = query.data.replace("_ppp", "")
    if selected_pack not in game.pack_selection_ui.pack_names:
        game.pack_selection_ui.pack_names.append(selected_pack)
    else:
        game.pack_selection_ui.pack_names.remove(selected_pack)

    game.pack_selection_ui.message_selection_id = query.message.message_id

    min_index = game.pack_selection_ui.page_index * game.pack_selection_ui.items_per_page
    max_index = min_index + game.pack_selection_ui.items_per_page
    packs_to_use_in_keyboard: List[str] = packs.get_packs_names()[min_index:max_index]
    packs_keyboard = []
    for pack_name in packs_to_use_in_keyboard:
        if pack_name in game.pack_selection_ui.pack_names:
            packs_keyboard.append([InlineKeyboardButton(f"{pack_name} ✔", callback_data=f'{pack_name[:60]}_ppp')])
        else:
            packs_keyboard.append([InlineKeyboardButton(pack_name, callback_data=f'{pack_name[:60]}_ppp')])

    packs_keyboard.append([InlineKeyboardButton(">>>", callback_data=f'>>>_next_pack_page')])
    reply_markup = InlineKeyboardMarkup(packs_keyboard)
    query.edit_message_text(text=query.message.text, reply_markup=reply_markup)


def update_set_packs_keyboard_callback(update, context) -> None:
    query: str = update.callback_query
    chatid = query.message.chat.id
    chat_type = query.message.chat.type

    if not chat_type.endswith("group"):
        return
    if not chatid in groups_dict.keys():
        return
    game: Game = groups_dict[chatid]
    game.pack_selection_ui.page_index += 1

    min_index = game.pack_selection_ui.page_index * game.pack_selection_ui.items_per_page
    max_index = min_index + game.pack_selection_ui.items_per_page
    packs_to_use_in_keyboard: List[str] = packs.get_packs_names()[min_index:max_index]
    packs_keyboard = []
    for pack_name in packs_to_use_in_keyboard:
        if pack_name in game.pack_selection_ui.pack_names:
            packs_keyboard.append([InlineKeyboardButton(f"<b>{pack_name}</b>", callback_data=f'{pack_name[:60]}_ppp')])
        else:
            packs_keyboard.append([InlineKeyboardButton(pack_name, callback_data=f'{pack_name[:60]}_ppp')])

    packs_keyboard.append([InlineKeyboardButton(">>>", callback_data=f'>>>_next_pack_page')])
    reply_markup = InlineKeyboardMarkup(packs_keyboard)
    query.edit_message_text(text=query.message.text, reply_markup=reply_markup)


def leave(update, context) -> None:
    chatid = update.message.chat_id
    username = update.message.from_user.username
    chat_type = update.message.chat.type
    if not chat_type.endswith("group"):
        utils.send_message(chatid, "You can only leave a game in a group!")
    elif chatid in groups_dict.keys():
        game: Game = groups_dict.get(chatid)
        user = User(username)
        actually_leave(game, user, left_group=False)
    else:
        utils.send_message(chatid, "There is no game running! Start one with /new_game")


def handle_user_who_quitted_group(update, context) -> None:
    chatid = update.message.chat_id
    username = update.message.from_user.username
    chat_type = update.message.chat.type
    if not chat_type.endswith("group"):
        return
    user : User = User(username)
    if chatid in groups_dict.keys():
        game: Game = groups_dict.get(chatid)
        actually_leave(game, user, left_group= True)


def actually_leave(game: Game, user : User, left_group : bool):
    if game.is_user_present(user):
        judge_copy = copy.deepcopy(game.judge)
        game.remove_user(user)

        utils.send_message(game.chat_id, f"{user.username} left the game!")
        if len(game.users) == 1:
            actually_end_game(game.chat_id)
        else:
            if game.round:
                game.round.delete_user_answers(user)
            #Todo: eventually check if the deep copy is actually needed or python doesn't make a reference when asigning self.judge (it probably does)
            if judge_copy == user:
                utils.send_message(f"Since the judge quitted a new round will start!")
    elif left_group:
        utils.send_message(game.chat_id, f"@{user.username} you have already left the game!")

def status(update, context) -> None:
    chatid = update.message.chat_id
    username = update.message.from_user.username
    chat_type = update.message.chat.type
    if not chat_type.endswith("group"):
        utils.send_message(chatid, "You can only get the game status in a group!")
    elif chatid in groups_dict.keys():
        game: Game = groups_dict[chatid]
        utils.send_message(chatid, game.get_formatted_scoreboard())
    else:
        utils.send_message(chatid, "There is no game running! Start one with /new_game")


def set_rounds(update, context) -> None:
    chatid = update.message.chat_id
    username = update.message.from_user.username
    chat_type = update.message.chat.type
    args = context.args
    if len(args) != 1:
        utils.send_message(chatid, "You used the command in the wrong way, use it like /set_rounds 41")
    elif not chat_type.endswith("group"):
        utils.send_message(chatid, "You can only get set the number of rounds in a group!")
    elif chatid in groups_dict.keys():
        game: Game = groups_dict[chatid]
        if game.is_started:
            utils.send_message(chatid, "You cannot change the number of rounds while in a game!")
        else:
            try:
                number_of_rounds: int = int(args[0])
            except ValueError:
                utils.send_message(chatid, "You used the command in the wrong way, use it like /set_rounds 41")
                return
            game.rounds = number_of_rounds
        utils.send_message(chatid, f"The number of rounds has been changed to {number_of_rounds}")
    else:
        utils.send_message(chatid, "There is no game running! Start one with /new_game")


def inline_caps(update, context):
    query = update.inline_query.query
    username = update.inline_query.from_user.username

    # Todo: eventually implement this in another way if search becomes too slow
    game = Game.find_game_from_username(username, groups_dict)
    if isinstance(game, Game):
        inline_user = game.get_user(username)
    else:
        return

    if game is None:
        return  # Todo eventually display no game in progress status or user not in game or something similar
    elif game.is_started is False:
        return  # Todo eventually display game still in join mode status
    elif game.judge.username == username:
        return  # Todo eventually display that judge should not answer

    # results = [InlineQueryResultArticle(
    #     id=f"{inline_user.username}:{response}"[:60],
    #     title=response,
    #     input_message_content=InputTextMessageContent(response)
    # ) for response in inline_user.responses]

    results = []
    for index, response in enumerate(inline_user.responses):
        results.append(
            InlineQueryResultArticle(
                id=str(index),
                title=response,
                input_message_content=InputTextMessageContent(response)
            ))

    context.bot.answer_inline_query(update.inline_query.id, results=results, cache_time=2, is_personal=True)


def handle_response_by_user(update, context):
    chatid = update.message.chat_id
    username = update.message.from_user.username
    chat_type = update.message.chat.type
    message_text = update.message.text
    if not chat_type.endswith("group"):
        return
    if not chatid in groups_dict.keys():
        return
    game: Game = groups_dict[chatid]
    user: User = game.get_user(username)
    if user is None:
        return

    if game.is_started:
        if message_text not in user.responses:
            return
        if not game.round.is_answering_mode:
            return
        if not user.has_answered:
            if game.can_remove_people_message:
                try:
                    bot.delete_message(chatid, update.message.message_id)
                except telegram.error.BadRequest:
                    utils.send_message(chatid,
                                       "You need to set this bot as an admin to delete messages. You won't see this message anymore during this game and the change will be effective in the next one")
                    game.can_remove_people_message = False

            if game.round.call.replacements > 1:
                utils.send_message(game.chat_id,
                                   f"{user.username} answered {user.completition_answers + 1} of {game.round.call.replacements}")
            user.completition_answers += 1
            user.responses.remove(message_text)
            game.round.answers[user.username].append(message_text)
            if user.completition_answers == game.round.call.replacements:
                utils.send_message(game.chat_id, f"{user.username} has finished answering!")
                user.has_answered = True

            if game.have_all_users_answered():
                game.round.is_judging_mode = True
                game.round.is_answering_mode = False

                buttons_list = []
                for user in list(filter(lambda x: x != game.judge, game.users)):
                    user_answer_formatted = f"{', '.join(game.round.get_user_answers(user.username))}"
                    buttons_list.append(
                        [InlineKeyboardButton(user_answer_formatted, callback_data=f'{user.username}_rcw')])

                message_markup = InlineKeyboardMarkup(buttons_list)
                utils.send_message(game.chat_id,
                                   f"Everyone has answered!\n@{game.judge.username} you need to chose the best answer.\n{game.round.call.get_formatted_call()}",
                                   markup=message_markup)


def handle_response_chose_winner_callback(update, context):
    query: str = update.callback_query
    chat_type = query.message.chat.type
    chatid = query.message.chat.id

    if not chat_type.endswith("group"):
        return
    if not chatid in groups_dict.keys():
        return
    game: Game = groups_dict[chatid]
    winner_user: User = game.get_user(query.data.split("_rcw")[0])
    if query.from_user.username != game.judge.username:
        return

    buttons_list = []
    for user in list(filter(lambda x: x != game.judge, game.users)):
        user_answer_formatted = f"{user.username}: {', '.join(game.round.get_user_answers(user.username))}"
        buttons_list.append(
            [InlineKeyboardButton(user_answer_formatted, callback_data=f'none')])

    message_markup = InlineKeyboardMarkup(buttons_list)

    formatted_game_call: str = game.round.call.get_formatted_call()

    winning_answer = game.round.answers[winner_user.username]
    for answer in winning_answer:
        formatted_game_call = formatted_game_call.replace("_", f"<b>{answer}</b>", 1)


    if not game.is_user_present(winner_user):
        query.edit_message_reply_markup(reply_markup=message_markup)
        utils.send_message(chatid, f"I'm sorry, but since {winner_user} has left the game you'll have to chose another winner")
        return
    else:
        query.edit_message_text(text=f"@{winner_user.username} won!\n{formatted_game_call}",
                            reply_markup=message_markup, parse_mode=telegram.ParseMode.HTML)

    winner_user.score += 1
    utils.send_message(chatid, f"Here's the current scoreboard:\n{game.get_formatted_scoreboard()}")

    if not game.new_round():
        actually_end_game(chatid)
    else:
        utils.send_message(chatid, f"@{game.judge.username} is asking:\n{game.round.call.get_formatted_call()}")


def unknown(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Sorry, I didn't understand that command.")
    # Todo: fix this to not always happen (Do I even need this handler? lol)


dispatcher.add_handler(CommandHandler(('start', 'help'), help))
dispatcher.add_handler(CommandHandler(('new_game'), new_game))
dispatcher.add_handler(CommandHandler(('start_game'), start_game))
dispatcher.add_handler(CommandHandler(('end_game'), end_game))
dispatcher.add_handler(CommandHandler(('join'), join))
dispatcher.add_handler(CommandHandler(('leave'), leave))
dispatcher.add_handler(CommandHandler(('status'), status))
dispatcher.add_handler(CommandHandler(('set_rounds'), set_rounds))
dispatcher.add_handler(CommandHandler(('set_packs'), set_packs))

dispatcher.add_handler(CallbackQueryHandler(handle_response_chose_winner_callback, pattern='_rcw'))
dispatcher.add_handler(CallbackQueryHandler(update_set_packs_keyboard_callback, pattern='>>>_next_pack_page'))
dispatcher.add_handler(CallbackQueryHandler(set_packs_callback, pattern='_ppp'))

dispatcher.add_handler(MessageHandler(Filters.status_update.left_chat_member, handle_user_who_quitted_group))
dispatcher.add_handler(MessageHandler(Filters.text, handle_response_by_user))



dispatcher.add_handler(InlineQueryHandler(inline_caps))
dispatcher.add_handler(MessageHandler(Filters.command, unknown))

if packs.check_for_packs_file():
    logging.info(f"Downloading {50 * 12} packs, this may take a while...")
    packs.downloads_packs_data(50)
    logging.info(f"Saving packs to {packs_file}...")
    packs.dump_to_pickle()
else:
    logging.info("Packs found, loading them...")
    packs.load_from_pickle()

if groups_file.is_file():
    logging.info(f"Groups found from previous run, loading them...")
    groups_dict = backup_handler.get_groups()
    logging.info("Groups loaded!")
else:
    logging.info("No previous groups found, continuing...")

if persistence:
    logging.info("Enabled persistence betweeen runs! Backups will happen every 60 seconds")
    backup_handler.start_backup_thread(60)


logging.info('Starting telegram polling thread...')
updater.start_polling()
updater.idle()
