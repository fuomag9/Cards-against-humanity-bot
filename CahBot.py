import logging

from telegram import InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import CommandHandler, Updater, InlineQueryHandler, MessageHandler, Filters

from modules.Argparse_args import args as argparse_args
from modules.Game import Game
from modules.User import User
from modules.Utils import Utils
from modules.Packs import Packs

updater = Updater(token=argparse_args["key"], use_context=True)
dispatcher = updater.dispatcher
bot = updater.bot  # bot class instance

bot_path = argparse_args["working_folder"]
# auto_remove = Utils.str2bool(argparse_args["remove"])
# admin_pw = argparse_args["admin_password"]
logging_file = argparse_args["logging_file"]
admin_mode = Utils.str2bool(argparse_args["admin_mode"])
db_file = argparse_args["database_file"]

logging_level = logging.INFO
if not Utils.str2bool(argparse_args["enable_logging"]):
    logging_level = 99  # stupid workaround not to log -> only creates file

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging_level, filename=logging_file)

utils = Utils(db_file, bot)
questions = Packs()

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
                           f"Game started! Use /join to enter the game\nps: {admin_user.username} has already joined")
    else:
        utils.send_message(chatid, "A game is already in progress!")
        # Todo: eventually implement game timer and stopping


def start_game(update, context) -> None:
    chatid = update.message.chat_id
    username = update.message.from_user.username
    chat_type = update.message.chat.type
    if not chat_type.endswith("group"):
        utils.send_message(chatid, "You can only start a game in a group!")
        return
    if not chatid in groups_dict.keys():
        utils.send_message(chatid, "There's no game to start, create one with /new_game")
    else:
        game: Game = groups_dict[chatid]
        game.is_started = True
        groups_dict[chatid] = game
        utils.send_message(chatid, "Game started!")
        # Todo: implement game thread or whatever and start rounds with Game.new_round()
        # Todo : also remember to set game.round.is_answering_mode to true and handle it, same for game.round.is_judjing_mode


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
    string_status = ""
    for username, score in [(u.username, u.score) for u in game.scoreboard()]:
        string_status += f"{username}: {score} points\n"
    utils.send_message(chatid, f"Here's the full scoreboard:\n{string_status}")
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


def set_packs(update, context) -> None:
    pass
    # Todo: setup packs


def inline_caps(update, context):
    query = update.inline_query.query
    username = update.inline_query.from_user.username

    if not query:
        return

    # Todo: eventually implement data in DB if search becomes too slow
    for searched_game in list(groups_dict.values()):
        for searched_user in searched_game.users:
            if searched_user.username == username:
                inline_user: User = searched_user
                game: Game = searched_game

    if inline_user is None or game is None:
        return  # Todo eventually display no game in progress status
    elif game.is_started is False:
        return  # Todo eventually display game still in join mode status

    gay = ["cacca", "pene", "urina"]

    results = [InlineQueryResultArticle(
        id=f"{User.username}:{response}",
        title=response,
        input_message_content=InputTextMessageContent(response)
    ) for response in gay]  # inline_user.responses

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
    game : Game = groups_dict[chatid]
    if game.ignore_messages:
        return
    if not game.is_user_present(User(username)):
        return
    else:
        user: User = game.get_user(username)
    if game.is_started and game.is_answering_mode:
        if message_text not in user.responses:
            return
        if not user.has_answered:
            user.answer = message_text
            if game.round.call_completitions_spaces > 1:
                utils.send_message(game.chat_id, f"{user.username} answered {user.completition_answers} of {game.round.call_completitions_spaces}")
            user.completition_answers += 1
            if user.completition_answers == game.round.call_completitions_spaces:
                utils.send_message(game.chat_id, f"{user.username} has answered!")

            if game.have_all_users_answered():
                game.round.is_judging_mode = True
                game.round.is_answering_mode = False
                #Todo : send message with callback for judge and write the fucking UI and stuff -> the game.rounds -1 == 0 needs to be handled there

            index = game.users.index(user)
            game.users[index] = user
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

dispatcher.add_handler(InlineQueryHandler(inline_caps))
dispatcher.add_handler(MessageHandler(Filters.command, unknown))



logging.info("Downloading packs...")
questions.downloads_packs_data()
logging.info("Initializing packs database...")
questions.inizialize_pack_database()

logging.info('Starting telegram polling thread...')
updater.start_polling()
updater.idle()