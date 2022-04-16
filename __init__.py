import os
import site

site.addsitedir(os.path.join(os.path.dirname(__file__), "lib"))

from mobase import IPlugin
from .crashloglabeler import CrashLogLabeler

def createPlugin() -> IPlugin:
    return CrashLogLabeler()
