import os
import re
from typing import (Callable, Dict, List)
from PyQt5.QtCore import QFile

from dulwich import porcelain as git

GIT_REPO = os.path.join(os.path.dirname(__file__), "AddressLibraryDatabase")
STACK_PATTERN = re.compile(
    r"(\t\[ *\d+\] 0x[0-9A-F]+ .*\+[0-9A-F]+) -> (?P<id>\d+)\+0x[0-9A-F]+")

class CrashLogProcessor():
    def __init__(self, git_remote : str, git_branch : str, database : str):
        self.git_remote = git_remote
        self.git_branch = bytes(git_branch, "utf-8")
        self.database = database

    def update_settings(self, git_remote : str, git_branch : str, database : str):
        self.git_remote = git_remote
        self.git_branch = git_branch
        self.database = database

        self.update_database()

    def clone_database(self) -> None:
        if not os.path.exists(GIT_REPO):
            try:
                git.clone(self.git_remote, GIT_REPO, branch=self.git_branch)
            except git.Error:
                pass

    def update_database(self) -> None:
        self.clone_database()
        try:
            git.pull(GIT_REPO)
            if git.active_branch(GIT_REPO) != self.git_branch:
                git.checkout(GIT_REPO, self.git_branch)
        except git.Error:
            pass

    def get_database_path(self) -> str:
        return os.path.join(GIT_REPO, self.database)

    def process_log(self, log : str) -> None:
        crash_log = CrashLog(log)

        addr_ids = set()
        width = 0
        for line in crash_log.call_stack:
            match = STACK_PATTERN.match(line)
            if not match:
                continue
            addr_ids.add(int(match.group("id")))
            width = max(width, len(match.group(0)) + 1)

        if not addr_ids:
            return
        id_list = sorted(addr_ids)

        id_lookup = self.lookup_ids(id_list)
        if not id_lookup:
            return

        crash_log.rewrite_call_stack(lambda line : self.add_name(line, id_lookup, width))
        crash_log.write_file()

    def add_name(self, line : str, id_lookup : Dict[int, str], width : int) -> str:
        match = STACK_PATTERN.match(line)
        if not match:
            return line

        stack_frame = match.group(0)
        name = id_lookup.get(int(match.group("id")))
        if not name:
            return stack_frame + "\n"

        name = name.rstrip("_*")
        return stack_frame.ljust(width) + name + "\n"

    def lookup_ids(self, id_list : List[int]) -> Dict[int, str]:
        database = self.get_database_path()
        if not os.path.exists(database):
            return {}

        lookup = {}
        with IdScanner(database) as scanner:
            for addr_id in id_list:
                name = scanner.find(addr_id)
                if name:
                    lookup[addr_id] = name
        return lookup

class CrashLog():
    def __init__(self, path : str):
        self.path = path
        self.pre_call_stack = []
        self.call_stack = []
        self.post_call_stack = []
        self.changed = False

        self.read_file()

    def visit_call_stack(self, callback : Callable[[str], None]) -> None:
        for line in self.call_stack:
            callback(line)

    def rewrite_call_stack(self, callback : Callable[[str], str]) -> None:
        new_call_stack = [callback(line) for line in self.call_stack]
        if new_call_stack != self.call_stack:
            self.changed = True
            self.call_stack = new_call_stack

    def write_file(self) -> None:
        if not self.changed:
            return
        QFile(self.path).moveToTrash()
        with open(self.path, "w") as f:
            f.writelines(self.pre_call_stack)
            f.writelines(self.call_stack)
            f.writelines(self.post_call_stack)

    def read_file(self) -> None:
        with open(self.path, "r") as f:
            while True:
                line = f.readline()
                if not line:
                    return

                self.pre_call_stack.append(line)
                if line == "PROBABLE CALL STACK:\n":
                    break

            while True:
                line = f.readline()
                if not line:
                    return

                if line == "\n":
                    break

                self.call_stack.append(line)

            while True:
                line = f.readline()
                if not line:
                    return

                self.post_call_stack.append(line)

class IdScanner():
    def __init__(self, database : str):
        self.database = database
        self.f = None
        self.nextLine = ""

    def __enter__(self):
        if os.path.exists(self.database):
            self.f = open(self.database, "r")
            self.f.readline()
            self.nextLine = self.f.readline()
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        if self.f:
            self.f.close()

    def find(self, addr_id : int) -> str:
        while self.nextLine:
            line_id, name = tuple(self.nextLine.split())
            parsed_id = int(line_id)

            if parsed_id == addr_id:
                return name
            elif parsed_id > addr_id:
                return ""

            self.nextLine = self.f.readline()
