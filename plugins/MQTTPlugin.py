# -*- coding: utf-8 -*-
from plugins.AbstractPlugin import *
import paho.mqtt.client as mqtt
import os

class MQTTPlugin(AbstractPlugin):

    def __init__(self, pMainClass, pPluginID):
        super().__init__(pMainClass, pPluginID)

        if os.getenv("MQTT_HOST") != "" and os.getenv("MQTT_HOST") != None:
            self.client = mqtt.Client()
            self.client.on_connect = self.on_connect
            self.client.on_message = self.on_message
            
            if os.getenv("MQTT_USER") != None and os.getenv("MQTT_PASS") != None:
                self.client.username_pw_set(os.getenv("MQTT_USER"), os.getenv("MQTT_PASS"))
                
            self.client.connect(os.getenv("MQTT_HOST"), int(os.getenv("MQTT_PORT")), 60)
            self.client.loop_start()
        else:
            self.logger.error("you need to enter your MQTT data in the .env file")    

    # The callback for when the client receives a CONNACK response from the server.
    def on_connect(self, client, userdata, flags, rc):
        self.logger.debug("successfully connected to MQTT Broker: " + os.getenv("MQTT_HOST"))

        # Subscribing in on_connect() means that if we lose the connection and
        # reconnect then subscriptions will be renewed.
        self.client.subscribe("heidi/"+os.getenv("MQTT_PREFIX")+"/command")
        #self.client.subscribe("etc.......")

    # The callback for when a PUBLISH message is received from the server.
    def on_message(self, client, userdata, msg):
        if msg.topic == "heidi/"+os.getenv("MQTT_PREFIX")+"/command":
            self.ow.handleInput(msg.payload.decode("utf-8"))   
