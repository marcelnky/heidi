# -*- coding: utf-8 -*-
from plugins.AbstractPlugin import *
import _thread
import os

class TalkPlugin(AbstractPlugin):

    def __init__(self, pMainClass, pPluginID):
        super().__init__(pMainClass, pPluginID)

    def talk(self, pParams):
        self.logger.debug("say: " + str(pParams))
        pStr = pParams[0]
        pStr = pStr.replace("_", "")
        pStr = pStr.replace("(", "")
        pStr = pStr.replace(")", "")
        pStr = pStr.replace(".", " ")
        pStr = pStr.replace(",", " ")

        #anstatt die systemausgabe zu nutzen, wird die sprache an einen
        #client geleitet der sich darum kümmert
        self.ow.mqtt.client.publish("heidi/"+os.getenv("MQTT_PREFIX")+"/speechOutput", pStr)
        #_thread.start_new_thread(os.system, ('say ' + pStr,))
