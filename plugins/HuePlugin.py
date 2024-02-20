# -*- coding: utf-8 -*-
from plugins.AbstractPlugin import *
import requests
from phue import Bridge
import json
import os

class HuePlugin(AbstractPlugin):

    def __init__(self, pMainClass, pPluginID):
        super().__init__(pMainClass, pPluginID)

        self.ip = os.getenv("HUE_BRIDGE_IP")
        self.lights = []
        self.logger.debug("connecting HUE Bridge")
        if self.ip != None and self.ip != '':
            self.logger.debug("HUE Bridge found. ip: " + str(self.ip))

            try:
                self.bridge = Bridge(self.ip)
                self.bridge.connect()
                self.lights = self.bridge.get_light_objects()

                tmpArr = []
                for i in self.lights:
                    tmpArr.append(i.name)
                self.logger.debug("found lights: " + str(tmpArr))

                tmpArr = []
                for i in self.bridge.get_group():
                    tmpArr.append(self.bridge.get_group(int(i), 'name'))
                self.logger.debug("found groups: " + str(tmpArr))

                self.logger.info("successfully connected to HUE Bridge: " + str(self.ip))
            except:
                self.logger.error("could not connect to HUE Bridge. please press the button on the bridge")
                self.logger.error("you can get rid of this message by simply moving or deleting the hue plugin out of the plugins folder")
        else:
            self.logger.error("you need to enter your HUE data in the .env file")
    
    def getLightByName(self, pLightname):
        self.logger.debug("looking for light " + pLightname)
        found = False
        for l in self.lights:
            if pLightname.lower() == l.name.lower():
                self.logger.debug("found light " + pLightname)
                found = l

        if found == False:
            self.logger.debug("could not found light " + pLightname + " looking for lightgroup now")

        return found

    def getGroupByName(self, pGroupname):
        self.groups = self.bridge.get_group()
        found = False
        for i in self.groups:
            if pGroupname.lower() == self.bridge.get_group(int(i), 'name').lower():
                found =self.bridge.get_group(int(i), 'lights')
                tmp = []
                for k in found:
                    lightName = self.bridge.get_light(int(k))["name"]
                    if lightName != "Steckdose Stereoanlage":
                        tmp.append(lightName)
                found = tmp
        return found

    def turnOffGroup(self, params):
        pName = params[0]
        self.logger.info("turn off group: " + pName)
        # lichter einer gruppe ausschalten
        arr = self.getGroupByName(pName)

        command = {'transitiontime': 10, 'on': False}
        self.bridge.set_light(arr, command)

    def turnOnGroup(self, params):
        pName = params[0]
        self.logger.info("turn on group: " + pName)
        # lichter einer gruppe anschalten
        arr = self.getGroupByName(pName)

        command = {'transitiontime': 10, 'on': True, 'bri': 254}
        self.bridge.set_light(arr, command)

    def allLightsOff(self, params):
        self.logger.info("turning all lights off")
        for l in self.lights:
            l.on = False

    def allLightsOn(self, params):
        self.logger.info("turning all lights on")
        for l in self.lights:
            l.on = True

    def turnOffLightOrGroupByName(self, params):
        pName = params[0]
        l = self.getLightByName(pName)
        if l != False:
            l.on = False
            self.logger.info("turning off light: " + pName)
        else:
            g = self.getGroupByName(pName)
            if g != False:
                self.logger.debug("found group: " + pName)
                self.turnOffGroup([pName])

    def turnOnLightOrGroupByName(self, params):
        pName = params[0]
        l = self.getLightByName(pName)
        if l != False:
            l.on = True
            self.logger.info("turning on light: " + pName)
        else:
            g = self.getGroupByName(pName)
            if g != False:
                self.logger.debug("found group: " + pName)
                self.turnOnGroup([pName])


    ################################################################
    ################################################################
    ################################################################

    # def createSnapshotForGroup(self, params):
    #     ()
    #     pGroup = params[0]
    #     pSnapshotName = params[1]

    #     bulbs = self.getGroupByName(pGroup)

    #     if bulbs != False:
    #         self.key = 'RoXGsDLlH1oPgqURO3jKyi7i8ukYmrviDMhREoqy'
    #         myurl = 'http://' + self.ip + '/api/' + self.key + '/lights/'
    #         r = requests.get(url=myurl)
    #         arr = r.json()

    #         ###
    #         myArr = []
    #         for i, value in arr.items():
    #             if value["name"] in bulbs:
    #                 myArr.append(value)

    #         ###
    #         bulbs = []
    #         for i in myArr:
    #             bulbs.append(i["name"])

    #         ###SQL
    #         db = DBConnection()
    #         con = db.connectDB()
    #         txt = con.escape_string(str(myArr))
    #         res = db.executeDB(con,"INSERT INTO `lightProfiles` (`id`, `profileName`, `jstring`, `groupname`) VALUES (NULL, '" + pSnapshotName + "', '" + txt + "', '" + pGroup + "');")

    #         self.logger.info("created snapshoot: "+ pSnapshotName + " for group: " + pGroup + " - bulbs: " + str(bulbs))

    #     return myArr
    #     else:
    #        return False

    # def applySnapshot(self, params):
    #     ()
    #     pName = params[0]
    #     db = DBConnection()
    #     res = db.queryDB(db.connectDB(), "SELECT jstring FROM lightProfiles WHERE profileName = '" + pName+"'")

    #     #string aus db in array konvertieren
    #     pArr = ast.literal_eval(res[0][0])

    #     for i in pArr:
    #         self.logger.info("apply snapshoot for light: " + i["name"])
    #         self.logger.debug(i["state"])
    #         i["state"]["alert"]='None'
    #         self.bridge.set_light(i["name"], i["state"])

    # def getGroupNames(self, params):
    #     self.groups = self.bridge.get_group()

    #     tmp = ''
    #     for i in self.groups:
    #         name = self.bridge.get_group(int(i), 'name')
    #         if name != "Entertainment-Bereich 1":
    #             tmp += "\n" + name + ", "

    #     self.callback(tmp)

    # def getLightsInGroup(self, params):
    #     pGroupname = params[0]
    #     self.groups = self.bridge.get_group()

    #     for i in self.groups:
    #         if pGroupname.lower() == self.bridge.get_group(int(i), 'name').lower():
    #             found =self.bridge.get_group(int(i), 'lights')
    #             self.logger.debug("found group: " + pGroupname)

    #             tmp = "Folgende Lampen wurden in der Gruppe " + pGroupname + " gefunden: "
    #             for k in found:
    #                 lightName = self.bridge.get_light(int(k))["name"]
    #                 if lightName != "Steckdose Stereoanlage":
    #                     tmp += lightName + ", "

    #     self.callback(tmp[:-2])


    # def turnOnLightByName(self, params):
    #     pName = params[0]
    #     l = self.getLightByName(pName)
    #     if l != False:
    #         l.on = True
    #         self.logger.info("turning on light: " + pName)

    
    # DIESER BLOCK FUNKTIONIERT, WIRD ABER NICHT BENÖTIGT
    # def dimLightByName(self, pName):
    #     l = self.getLightByName(pName)
    #     if l != False:
    #         if l.on == True:
    #             self.logger.info("dimming light: " + pName)
    #             self.logger.debug("current brightness is: " + str(l.brightness))

    #             currentBrightness = l.brightness
    #             currentBrightness -= 20
    #             if currentBrightness <=0:
    #                 currentBrightness = 0
    #             self.logger.debug("new brightness is: " + str(currentBrightness))

    #             l.transitiontime = 20
    #             l.brightness = currentBrightness
    #         else:
    #             self.logger.info("cannot dim light: " + pName + ". Light is turned off")

    # def brightUpLightByName(self, pName):
    #     self.logger.info("bright up light: " + pName)
    #     l = self.getLightByName(pName)
    #     if l != False:
    #         if l.on == True:
    #             self.logger.debug("current brightness is: " + str(l.brightness))

    #             currentBrightness = l.brightness
    #             currentBrightness += 20
    #             if currentBrightness >250:
    #                 currentBrightness = 250
    #             self.logger.debug("new brightness is: " + str(currentBrightness))

    #             l.transitiontime = 20
    #             l.brightness = currentBrightness
    #         else:
    #             self.logger.info("cannot bright up light: " + pName + ". Light is turned off")

    # def setupLightBrightnessByName(self, pName, pNr):

    #     if pNr<0:
    #         pNr = 0

    #     if pNr>250:
    #         pNr = 250

    #     l = self.getLightByName(pName)
    #     if l != False:
    #         self.logger.info("set brightness of light: " + pName + " to " + str(pNr))
    #         l.transitiontime = 1
    #         l.brightness = pNr


    # def setupLightColorByName(self, pName, pColor):

    #     l = self.getLightByName(pName)
    #     if l != False:
    #         self.logger.info("coloring light: " + pName)
    #         #l.transitiontime = 1
    #         #l.xy = pColor
    #         l.xy = [0.2061, 0.6728]
    

