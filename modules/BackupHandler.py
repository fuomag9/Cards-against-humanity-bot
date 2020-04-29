import time
from pathlib import Path
from typing import Dict, Union
import pickle
import threading


class BackupHandler:
    def __init__(self, groups_dict: Dict, backup_file: Path):
        self.thread: Union[threading.Thread, None] = None
        self.__should_thread_run = True
        self.client = None
        self.backup_file = backup_file
        self.groups_dict = groups_dict

    def __backup_thread(self, interval: int):
        while self.__should_thread_run:
            time.sleep(interval)
            with open(self.backup_file, "wb") as file:
                data = pickle.dumps(self.groups_dict)
                file.write(data)

    def start_backup_thread(self, interval: int):
        """
        Starts a background thread to backup games_dict every interval

        :param interval: the interval in seconds between backups
        """

        self.__should_thread_run = True
        self.thread = threading.Thread(target=self.__backup_thread, args=(interval,),
                                       daemon=True)
        self.thread.start()

    def stop_background_thread(self):
        """
        Stops the background thread if running
        """
        if self.thread is not None:
            if self.thread.is_alive():
                self.__should_thread_run = False

    def get_groups(self) -> Dict:
        """
        Returns games_dict from backup_file
        """
        with open(self.backup_file, "rb") as file:
            data = file.read()
            return pickle.loads(data)
