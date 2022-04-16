from typing import (Any, Dict, List, Union)
from mobase import (
    IOrganizer,
    IPlugin,
    IPluginRequirement,
    PluginRequirementFactory,
    PluginSetting,
    ReleaseType,
    VersionInfo,
)
from PyQt5.QtWidgets import QMainWindow

from .crashlogutil import *

class CrashLogLabeler(IPlugin):

    def __init__(self):
        super().__init__()

    def author(self) -> str:
        return "Parapets"

    def description(self) -> str:
        return "Labels known addresses in Skyrim crash logs"

    def init(self, organizer: "IOrganizer") -> bool:
        self.organizer = organizer
        organizer.onAboutToRun(self.onAboutToRunCallback)
        organizer.onFinishedRun(self.onFinishedRunCallback)
        organizer.onPluginSettingChanged(self.onPluginSettingChangedCallback)
        organizer.onUserInterfaceInitialized(self.onUserInterfaceInitializedCallback)

        self.processor = CrashLogProcessor(
            self.organizer.pluginSetting(self.name(), "git_repository"),
            self.organizer.pluginSetting(self.name(), "git_branch"),
            self.organizer.pluginSetting(self.name(), "database_file")
        )

        return True

    def name(self) -> str:
        return "Crash Log Labeler"

    def requirements(self) -> List["IPluginRequirement"]:
        return [
            PluginRequirementFactory.gameDependency({
                "Skyrim Special Edition",
            })
        ]

    def settings(self) -> List["PluginSetting"]:
        return [
            PluginSetting(
                "git_repository",
                "Git repository for the address library database",
                "https://github.com/meh321/AddressLibraryDatabase"
            ),
            PluginSetting(
                "git_branch",
                "Git branch to check out",
                "main"
            ),
            PluginSetting(
                "database_file",
                "Path to the database file",
                "skyrimae.rename"
            )
        ]

    def version(self) -> "VersionInfo":
        return VersionInfo(1, 0, 0, 0, ReleaseType.BETA)

    def onAboutToRunCallback(self, path : str) -> bool:
        self.crash_logs = get_crash_logs()
        return True

    def onFinishedRunCallback(self, path : str, exit_code : int):
        if exit_code == 0:
            return

        for log in get_crash_logs():
            if log not in self.crash_logs:
                self.processor.update_database()
                self.processor.process_log(log)

    def onPluginSettingChangedCallback(
        self,
        plugin_name : str,
        setting_name : str,
        old_value : Union[None, bool, int, str, List[Any], Dict[str, Any]],
        new_value : Union[None, bool, int, str, List[Any], Dict[str, Any]]
    ) -> None:
        self.processor.update_settings(
            self.organizer.pluginSetting(self.name(), "git_repository"),
            self.organizer.pluginSetting(self.name(), "git_branch"),
            self.organizer.pluginSetting(self.name(), "database_file")
        )

    def onUserInterfaceInitializedCallback(self, main_window : QMainWindow):
        self.processor.update_database()

        for log in get_crash_logs():
            self.processor.process_log(log)
