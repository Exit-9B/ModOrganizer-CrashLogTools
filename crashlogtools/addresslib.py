from typing import *

class AddressDatabase(object):

    def __init__(self, remote : str, branch : str, database_file : str):
        self.remote = remote
        self.branch = bytes(branch, "utf-8")
        self.database_file = database_file

DATABASES = {
    "Skyrim Special Edition": AddressDatabase(
        "https://github.com/meh321/AddressLibraryDatabase",
        "main",
        "skyrimae.rename"
    ),
}

def supported_games() -> Set[str]:
    return set(DATABASES.keys())

def get_database(game : str) -> "AddressDatabase":
    return DATABASES.get(game)
