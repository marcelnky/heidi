# -*- coding: utf-8 -*-
from plugins.AbstractPlugin import *
import time

class DateTimePlugin(AbstractPlugin):
    def __init__(self, pMainClass, pPluginID):
        super().__init__(pMainClass, pPluginID)

    # UHRZEIT AUSGEBEN
    def getTime(self, params):
        self.datetime = time.localtime()
        std = time.strftime("%H", self.datetime)
        min = time.strftime("%M", self.datetime)
        tmp = "Es ist " + std + " Uhr und " + min + " Minuten"
        return tmp

    # DATUM AUSGEBEN
    def getDate(self, params):
        self.datetime = time.localtime()
        wochentag = time.strftime("%A", self.datetime)
        tag = time.strftime("%d", self.datetime)
        monat = time.strftime("%B", self.datetime)
        tmp = "Es ist " + wochentag + " der " + tag + ". " + monat
        return tmp


