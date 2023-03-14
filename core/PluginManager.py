import os, sys
import logging
import importlib
import os.path
from os import path

class PluginManager:

    def __init__(self, pMainClass):
        self.ow = pMainClass
        self.logger = logging.getLogger("pluginmanager")

        #create array with all available plugins
        self.plugins = []
        for pluginName in self.listFilesInPluginDirectory("./plugins"):
            self.plugins.append({"id": pluginName, "instance": self.importModule(pluginName, 'plugins.')})

        if path.isdir('./plugins_dev'):
            for pluginName in self.listFilesInPluginDirectory("./plugins_dev"):
                self.plugins.append({"id": pluginName, "instance": self.importModule(pluginName, 'plugins_dev.')})


        self.logger.info("created " + str(len(self.plugins)) + " plugins " + self.getPluginListPrintable())

    def listFilesInPluginDirectory(self, pPath):
        self.logger.debug("scanning " +pPath+ " folder")
        dirs = os.listdir(pPath)
        tmp = []

        # This would print all the files and directories
        for file in dirs:
            if file[-3:] == '.py' and file!='__init__.py' and file!='AbstractPlugin.py':
                tmp.append(file.replace(".py", ""))
        self.logger.debug("found " + str(len(tmp)) + " plugins")
        return tmp


    #importiert ein plugin dynamisch anhand des namens
    def importModule(self, plugin, pluginfolder):
        self.logger.debug("importing " + plugin)
        return getattr(importlib.import_module(pluginfolder+plugin), plugin)(self.ow, plugin)

    def getPluginListPrintable(self):
        plugin_str = '['
        for i in self.plugins:
            plugin_str += i["id"] + ", "
        plugin_str = plugin_str[:-2] + "]"

        return plugin_str

    def getPlugin(self, pPluginID):
        found = False
        for i in self.plugins:
            if i["id"] == pPluginID:
                found = i["instance"]
        return found

