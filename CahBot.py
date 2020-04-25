import logging

from telegram import InlineQueryResultArticle, InputTextMessageContent, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, Updater, InlineQueryHandler, MessageHandler, Filters, ConversationHandler, \
    CallbackQueryHandler
import telegram

from modules.Argparse_args import args as argparse_args
from modules.Game import Game
from modules.User import User
from modules.Utils import Utils
from modules.PacksInit import PacksInit
from modules.MultiPack import MultiPack
from pathlib import Path

updater = Updater(token=argparse_args["key"], use_context=True)
dispatcher = updater.dispatcher
bot = updater.bot  # bot class instance

bot_path = argparse_args["working_folder"]
# auto_remove = Utils.str2bool(argparse_args["remove"])
# admin_pw = argparse_args["admin_password"]
logging_file = argparse_args["logging_file"]
admin_mode = Utils.str2bool(argparse_args["admin_mode"])
db_file = argparse_args["database_file"]
self_file_folder = Path(__file__).resolve().parent
packs_file = self_file_folder / "packs.pickle"

logging_level = logging.INFO
if not Utils.str2bool(argparse_args["enable_logging"]):
    logging_level = 99  # stupid workaround not to log -> only creates file

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging_level, filename=logging_file)

utils = Utils(db_file, bot)
packs = PacksInit(pack_json=packs_file)

groups_dict = {}  # group chat_id : Game                type inference  ===   dict[str:Game]


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
                           f"Game started! Use /join to enter the game and /set_packs to chose your packs")
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
        elif game.multipack is None:
            utils.send_message(chatid, "You can't start a game with no pack selected!")
        else:
            game.is_started = True
            list_of_packs = [packs.get_pack_by_truncatedstr_name(pack_name=pack_name) for pack_name in
                             game.pack_selection_ui.pack_names]
            game.multipack = MultiPack(list_of_packs)
            utils.send_message(chatid, "Game started!")
            game.new_round()
            groups_dict[chatid] = game


def actually_end_game(chatid) -> None:
    game = groups_dict[chatid]
    if len(game.scoreboard()) == 0:
        utils.send_message(chatid, "Game ended! I don't know who won since everyone left :(")
        return
    if game.is_started == False:
        utils.send_message(chatid, "Game ended! I don't who won since the game never started")
        return
    winner, score = game.scoreboard()[0]
    utils.send_message(chatid, f"Game ended!\n{winner} won with a score of {score}")
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
        group_game: Game = groups_dict.get(chatid)
        user = User(username)
        if group_game.is_user_present(user) is False:
            group_game.add_user(user)
            groups_dict[chatid] = group_game
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

    selected_pack = query.data.replace("_ppp","")
    if selected_pack not in game.pack_selection_ui.pack_names:
        game.pack_selection_ui.pack_names.append(selected_pack)
    else:
        game.pack_selection_ui.pack_names.remove(selected_pack)

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
    packs_keyboard.append([InlineKeyboardButton("Finish", callback_data=f'finished_adding_packs')])
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
    groups_dict[chatid] = game

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
        if game.is_user_present(user) is True:
            game.remove_user(user)
            groups_dict[chatid] = game
            utils.send_message(chatid, f"{user.username} left the game!")
            if len(game.users) == 0:
                actually_end_game(chatid)
        else:
            utils.send_message(chatid, f"{user.username} has already left the game!")
    else:
        utils.send_message(chatid, "There is no game running! Start one with /new_game")


def status(update, context) -> None:
    chatid = update.message.chat_id
    username = update.message.from_user.username
    chat_type = update.message.chat.type
    if not chat_type.endswith("group"):
        utils.send_message(chatid, "You can only get the game status in a group!")
    elif chatid in groups_dict.keys():
        game: Game = groups_dict[chatid]
        string_status = ""
        for username, score in [(u.username, u.score) for u in game.scoreboard()]:
            string_status += f"{username}: {score} points\n"
        utils.send_message(chatid, string_status)
    else:
        utils.send_message(chatid, "There is no game running! Start one with /new_game")


def off(update, context) -> None:
    chatid = update.message.chat_id
    username = update.message.from_user.username
    chat_type = update.message.chat.type
    if not chat_type.endswith("group"):
        utils.send_message(chatid, "You can only turn listening off in a group!")
    elif chatid in groups_dict.keys():
        game: Game = groups_dict[chatid]
        game.ignore_messages = True
        groups_dict[chatid] = group_game
    else:
        utils.send_message(chatid, "Cannot turn listening off if there are no games running!")


def on(update, context) -> None:
    chatid = update.message.chat_id
    username = update.message.from_user.username
    chat_type = update.message.chat.type
    if not chat_type.endswith("group"):
        utils.send_message(chatid, "You can only turn listening on in a group!")
    elif chatid in groups_dict.keys():
        game: Game = groups_dict[chatid]
        game.ignore_messages = False
        groups_dict[chatid] = group_game
    else:
        utils.send_message(chatid, "Cannot turn listening on if there are no games running!")


def inline_caps(update, context):
    query = update.inline_query.query
    username = update.inline_query.from_user.username

    if not query:
        return

    # Todo: eventually implement this in another way if search becomes too slow
    for searched_game in list(groups_dict.values()):
        inline_user: User = searched_game.get_user(username)
        if inline_user is not None:
            game: Game = searched_game
            break

    if inline_user is None or game is None or game.is_ended:
        return  # Todo eventually display no game in progress status or user not in game or something similar
    elif game.is_started is False:
        return  # Todo eventually display game still in join mode status
    elif game.judge == inline_user:
        return  # Todo handle judge who should not answer

    results = [InlineQueryResultArticle(
        id=f"{User.username}:{response}",
        title=response,
        input_message_content=InputTextMessageContent(response)
    ) for response in inline_user.responses]

    context.bot.answer_inline_query(update.inline_query.id, results)


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
    if game.ignore_messages:
        return
    if not game.is_user_present(
            username):  # Todo: this could technically be coupled with the statement below to save time
        return
    else:
        user: User = game.get_user(username)
    if game.is_started and game.is_answering_mode:
        if message_text not in user.responses:
            return
        if not user.has_answered:
            if game.round.call.replacements > 1:
                utils.send_message(game.chat_id,
                                   f"{user.username} answered {user.completition_answers + 1} of {game.round.call.replacements}")
            user.completition_answers += 1
            if user.completition_answers == game.round.call.replacements:
                utils.send_message(game.chat_id, f"{user.username} has finished answering!")
                user.has_answered = True

            if game.have_all_users_answered():
                # todo: handle if an user quitted
                game.round.is_judging_mode = True
                game.round.is_answering_mode = False

                buttons_list = []
                for user in game.users:
                    user_answer_formatted = f"{user.username}: {','.join(game.round.get_user_answers(user))}"
                    buttons_list.append(
                        [InlineKeyboardButton(user_answer_formatted, callback_data=f'{user.username}_rcw')])

                message_markup = InlineKeyboardMarkup(buttons_list)
                utils.send_message(game.chat_id,
                                   f"Everyone has answered!\n{game.judge.username} you need to chose the best answer",
                                   markup=message_markup)  # Todo: implement @ at user

            game.replace_user(user=user)
            groups_dict[chatid] = game


def handle_response_chose_winner_callback(update, context):
    query: str = update.callback_query
    chat_type = query.message.chat.type
    chatid = query.message.chat.id

    if not chat_type.endswith("group"):
        return
    if not chatid in groups_dict.keys():
        return
    game: Game = groups_dict[chatid]
    who_submitted_the_response: User = game.get_user(query.split("_rcw")[0])
    if not game.is_user_present(judge):
        return  # todo: handle if judge quitted
    # Todo: handle if callback refers to current game and not an old one (dumb users being dumb)

    query.edit_message_text(text=f"<b>{who_submitted_the_response}</b> won!")
    utils.send_message(chatid, f"{who_submitted_the_response} won!")  # Todo: superfluo?

    if not game.new_round():
        actually_end_game(chatid)
    else:
        groups_dict[chatid] = game


def unknown(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Sorry, I didn't understand that command.")
    # Todo: fix this to not always happen (Do I even need this handler? lol)


dispatcher.add_handler(CommandHandler(('start', 'help'), help))
dispatcher.add_handler(CommandHandler(('new_game'), new_game))
dispatcher.add_handler(CommandHandler(('start_game'), start_game))
dispatcher.add_handler(CommandHandler(('join'), join))
dispatcher.add_handler(CommandHandler(('leave'), leave))
dispatcher.add_handler(CommandHandler(('status'), status))
dispatcher.add_handler(CommandHandler(('off'), off))
dispatcher.add_handler(CommandHandler(('on'), on))
dispatcher.add_handler(CommandHandler(('set_packs'), set_packs))

dispatcher.add_handler(CallbackQueryHandler(handle_response_chose_winner_callback, pattern='_rcw'))
dispatcher.add_handler(CallbackQueryHandler(update_set_packs_keyboard_callback, pattern='>>>_next_pack_page'))
dispatcher.add_handler(CallbackQueryHandler(set_packs_callback, pattern='_ppp'))

dispatcher.add_handler(InlineQueryHandler(inline_caps))
dispatcher.add_handler(MessageHandler(Filters.command, unknown))

if packs.is_packs_file_empty():
    logging.info(f"Downloading {50 * 12} packs, this may take a while...")
    packs.downloads_packs_data(50)
    logging.info(f"Saving packs to {packs_file}...")
    packs.dump_to_pickle()
else:
    logging.info("Packs found, loading them...")
    packs.load_from_pickle()

logging.info('Starting telegram polling thread...')
updater.start_polling()
updater.idle()
