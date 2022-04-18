import os
import glob
from typing import *

import ctypes.wintypes
CSIDL_PERSONAL = 5
SHGFP_TYPE_CURRENT = 0

class CrashLogFinder(object):

    def __init__(self, log_directory : str, filter : str):
        self.log_directory = log_directory
        self.filter = filter

    def get_crash_logs(self) -> Set[str]:
        return set(glob.glob(os.path.join(self.log_directory, self.filter)))

def get_documents_path() -> str:
    buf = ctypes.create_unicode_buffer(ctypes.wintypes.MAX_PATH)
    ctypes.windll.shell32.SHGetFolderPathW(
        None, CSIDL_PERSONAL, None, SHGFP_TYPE_CURRENT, buf)
    return buf.value

MY_DOCUMENTS = get_documents_path()

FINDERS = {
    "Skyrim Special Edition": CrashLogFinder(
        os.path.join(MY_DOCUMENTS, "My Games", "Skyrim Special Edition", "SKSE"),
        "crash-*.log"
    ),
    "Skyrim VR": CrashLogFinder(
        os.path.join(MY_DOCUMENTS, "My Games", "Skyrim VR", "SKSE"),
        "crash-*.log"
    ),
}

def supported_games() -> Set[str]:
    return set(FINDERS.keys())

def get_finder(game : str) -> "CrashLogFinder":
    return FINDERS.get(game)
