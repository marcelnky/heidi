# -*- coding: utf-8 -*-
from plugins.AbstractPlugin import *
import wikipedia

class WikipediaPlugin(AbstractPlugin):

    def __init__(self, pMainClass, pPluginID):
        super().__init__(pMainClass, pPluginID)

    def search(self, params):
        pSearchStr = params[0]
        self.logger.info("wiki: search " + pSearchStr)
        wikipedia.set_lang("de")
        tmp = ""
        try:
            tmp = wikipedia.summary(pSearchStr, sentences=2)
        except wikipedia.exceptions.DisambiguationError as e:
            tmp = wikipedia.summary(e.options[0], sentences=2)
            self.logger.debug("got too many results, fetching first result " + tmp[:20] + "...")

        return self.trimString(tmp)

    
    def trimString(self, str):
        str = str.replace('\n', '')
        str = str.replace('(', '')
        str = str.replace(')', '')
        str = str.replace(';', '')
        str = str.replace(',', '')
        str = str.replace('*', '')
        str = str.replace('==', '')
        return str
