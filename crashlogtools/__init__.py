import os
import site
from typing import *

site.addsitedir(os.path.join(os.path.dirname(__file__), "lib"))

from mobase import IPlugin
from .crashloglabeler import CrashLogLabeler
from .crashlogviewer import CrashLogViewer

def createPlugins() -> List["IPlugin"]:
    return [CrashLogLabeler(), CrashLogViewer()]
