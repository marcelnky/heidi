# -*- coding: utf-8 -*-
from plugins.AbstractPlugin import *

import urllib, sys, os
import xml.etree.ElementTree as ET
from hashlib import md5
from xml.dom.minidom import *


class WeatherPlugin(AbstractPlugin):

    def __init__(self, pMainClass, pPluginID):
        super().__init__(pMainClass, pPluginID)

    def getWeatherHelper(self):
        city = os.getenv("wettercom_city")
        citycode = os.getenv("wettercom_citycode")
        degree = chr(176)
        apikey = os.getenv("wettercom_api")
        project_name= os.getenv("wettercom_project_name")
        
        m = md5()
        m.update((project_name+apikey+citycode).encode('utf-8'))
        authstring = m.hexdigest()

        url = 'http://api.wetter.com/forecast/weather/city/'+citycode+'/project/'+project_name+'/cs/'+authstring

        #XML Objekt erstellen und in den root wechseln
        tree = ET.parse(urllib.request.urlopen(url))
        root = tree.getroot()

        #Die aktuelle Tagesvorhersage finden
        dayforecast = root.find('forecast').find('date')
        maxtemp = dayforecast.find('tx')
        mintemp = dayforecast.find('tn')
        weather_text = dayforecast.find('w_txt').text

        stdout_encoding = sys.stdout.encoding or sys.getfilesystemencoding()
        tmp = weather_text + maxtemp.text + city + mintemp.text

        tmp = 'Hier der Wetterbericht mit der aktuellen Wettervorhersage für '+ city
        tmp +=': Morgen wird es ' + weather_text + "."
        tmp +='. Die Maximaltemperatur betraegt ' + maxtemp.text
        tmp +=' Grad'+ '. Die Minimaltemperatur liegt bei ' + mintemp.text + ' ' +'Grad.'

        #kein plan warum man die anführungszeichen noch braucht, das ganze ist ja bereits ein string
        return "\""+tmp+"\""

    def getWeather(self, params):
        return self.getWeatherHelper()
