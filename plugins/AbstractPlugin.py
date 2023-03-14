# -*- coding: utf-8 -*-
import logging

class AbstractPlugin:

    def __init__(self, pMainClass, pPluginID):
        self.ow = pMainClass
        self.id = pPluginID
        self.logger = logging.getLogger("plugin."+pPluginID)

    def callback(self, pStr):
        print("callback deprecated. use normal return insted " + pStr)
        # return self.ow.callback(pStr, self.id)
        #return self.ow.handleInput(pStr)
        #print("callback schicken " + pStr)