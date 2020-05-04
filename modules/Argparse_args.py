import argparse
import os
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument(
    "-k", "--key", required=True, type=str, help="Telegram bot api key. It's required in order to run this bot")
ap.add_argument(
    "-f",
    "--working-folder",
    required=False,
    type=str,
    default=os.getcwd(),
    help=f"Set the bot's working-folder. Default = {Path.cwd()}")
ap.add_argument(
    "--admin-password",
    required=False,
    type=str,
    default="",
    help="The password to authorize yourself as an admin, Default = False")
ap.add_argument(
    "--admin-mode",
    required=False,
    default=False,
    help="Should the bot commands be available only for admins?, Default = False")
ap.add_argument(
    "--enable-logging",
    required=False,
    default=True,
    help="Enable or disable logging, Default = True")
ap.add_argument(
    "--persistence",
    required=False,
    default=True,
    help="Enable or disable persistence, Default = True")
ap.add_argument(
    "--logging-file",
    required=False,
    type=str,
    default=str(Path.cwd() / "program_log.log"),
    help=f"Logging file location, Default={Path.cwd() / 'program_log.log'}")
args = vars(ap.parse_args())
