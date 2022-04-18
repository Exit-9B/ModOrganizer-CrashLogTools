from typing import *
from mobase import *
from PyQt5.QtWidgets import QMainWindow

from .crashlogutil import CrashLogProcessor

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

    def init(self, organizer : "IOrganizer") -> bool:
        self.organizer = organizer
        organizer.onFinishedRun(self.onFinishedRunCallback)
        organizer.onPluginSettingChanged(self.onPluginSettingChangedCallback)
        organizer.onUserInterfaceInitialized(self.onUserInterfaceInitializedCallback)

        self.processor = CrashLogProcessor(
            self.organizer.pluginSetting(self.name(), "git_repository"),
            self.organizer.pluginSetting(self.name(), "git_branch"),
            self.organizer.pluginSetting(self.name(), "database_file")
        )

        self.processed_logs = set()

        return True

    def get_crash_logs(self) -> Set[str]:
        directory = self.organizer.managedGame().documentsDirectory()
        directory.cd("SKSE")
        directory.setNameFilters(["crash-*.log"])
        return set((file.absoluteFilePath() for file in directory.entryInfoList()))

    def onFinishedRunCallback(self, path : str, exit_code : int):
        new_logs = self.get_crash_logs().difference(self.processed_logs)
        for log in new_logs:
            self.processor.update_database()
            self.processor.process_log(log)
        self.processed_logs.update(new_logs)

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

    def onUserInterfaceInitializedCallback(self, main_window : "QMainWindow"):
        self.processor.update_database()

        logs = self.get_crash_logs()
        for log in logs:
            self.processor.process_log(log)
        self.processed_logs.update(logs)
