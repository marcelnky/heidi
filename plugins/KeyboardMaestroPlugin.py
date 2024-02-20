# -*- coding: utf-8 -*-
from plugins.AbstractPlugin import *
import os

class KeyboardMaestroPlugin(AbstractPlugin):

    def __init__(self, pMainClass, pPluginID):
        super().__init__(pMainClass, pPluginID)
    
    def execute(self, params):
        count = len(params)

        if count>0 and count<3:
            makroId = params[0]
            makroParams = ""
            msg = """{"id": ["{{ID}}"],"params": ["{{PARAMETER}}"]}"""
            msg = msg.replace("{{ID}}", makroId)

            #kbm macro without arguments
            if count==1:
                msg = msg.replace("{{PARAMETER}}", "")

            #kbm macro with arguments
            else:
                makroParams = params[1]
                msg = msg.replace("{{PARAMETER}}", makroParams)

            self.ow.mqtt.client.publish("heidi/"+os.getenv("MQTT_PREFIX")+"/kbm", msg )
        else:
            print("invalid nr of arguments")
       
        return ""
    