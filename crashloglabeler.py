from typing import *
from mobase import *
if TYPE_CHECKING:
    from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtCore import *

from .crashlogutil import CrashLogProcessor
from . import crashlogs
from . import addresslib

class CrashLogLabeler(IPlugin):

    def __init__(self):
        super().__init__()

    def name(self) -> str:
        return "Crash Log Labeler"

    def version(self) -> "VersionInfo":
        return VersionInfo(1, 0, 0, 0, ReleaseType.BETA)

    def description(self) -> str:
        return "Labels known addresses in Skyrim crash logs"

    def author(self) -> str:
        return "Parapets"

    def requirements(self) -> List["IPluginRequirement"]:
        games = set.intersection(
            addresslib.supported_games(),
            crashlogs.supported_games()
        )

        return [
            PluginRequirementFactory.gameDependency(games)
        ]

    def settings(self) -> List["PluginSetting"]:
        return [
            PluginSetting(
                "offline_mode",
                "Disable update from remote database",
                False
            ),
        ]

    def init(self, organizer : "IOrganizer") -> bool:
        self.organizer = organizer
        organizer.onFinishedRun(self.onFinishedRunCallback)
        organizer.onUserInterfaceInitialized(self.onUserInterfaceInitializedCallback)

        self.processed_logs = set()

        return True

    def onFinishedRunCallback(self, path : str, exit_code : int):
        new_logs = self.finder.get_crash_logs().difference(self.processed_logs)
        if not new_logs:
            return

        if not self.organizer.pluginSetting(self.name(), "offline_mode"):
            self.processor.update_database()

        for log in new_logs:
            self.processor.process_log(log)

        self.processed_logs.update(new_logs)

    def onUserInterfaceInitializedCallback(self, main_window : "QMainWindow"):
        game = self.organizer.managedGame().gameName()
        self.finder = crashlogs.get_finder(game)
        self.processor = CrashLogProcessor(game, lambda file : QFile(file).moveToTrash())

        if not self.organizer.pluginSetting(self.name(), "offline_mode"):
            self.processor.update_database()

        logs = self.finder.get_crash_logs()
        for log in logs:
            self.processor.process_log(log)
        self.processed_logs.update(logs)
