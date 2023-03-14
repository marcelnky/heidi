# -*- coding: utf-8 -*-

import logging.config
from dotenv import load_dotenv
from core.PluginManager import *
import locale, coloredlogs
import _thread
from http.server import BaseHTTPRequestHandler, HTTPServer
import json, sqlite3, aiml

class Heidi:

    def __init__(self):

        # LOAD ENVIRONMENT VARS
        load_dotenv()

        # SET CORRECT LOCALE
        locale.setlocale(locale.LC_ALL, os.getenv("DEFAULT_LOCALE"))

        self.createJsFileWithMqttData()

        # LOGGER CONFIG
        logging.config.dictConfig(self.getLoggerConfig())
        self.logger = logging.getLogger("core")
        self.logger.info("heidi started")
        coloredlogs.install(level=os.getenv("LOG_LEVEL"), datefmt=os.getenv("LOG_DATE_FORMAT"), fmt=os.getenv("LOG_FORMAT"))

        # SILENCE SPECIFIC THIRD PARTY LOGGERS
        logger = logging.getLogger("apscheduler.scheduler")
        logger.setLevel(logging.ERROR)
        logger = logging.getLogger("urllib3.connectionpool")
        logger.setLevel(logging.ERROR)
        logger = logging.getLogger("phue")
        logger.setLevel(logging.ERROR)
        logger = logging.getLogger("spotipy")
        logger.setLevel(logging.ERROR)
        logger = logging.getLogger("openai")
        logger.setLevel(logging.ERROR)
        logger = logging.getLogger("urllib3.util]")
        logger.setLevel(logging.ERROR)

        # PLUGIN MANAGER
        self.pluginManager = PluginManager(self)

        # # Jobs Plugin needs to be called after plugin manager is instantiated
        # # first check if the module is defined
        jobs = self.pluginManager.getPlugin("JobsPlugin")

        #if defined, call loadJobs method
        if jobs != False:
            jobs.loadJobs()

        # AIML DICTIONARY FROM DB
        self.loadAimlFromDB()

        # AIML KERNEL
        # The Kernel object is the public interface to
        # the AIML interpreter.
        self.aiml = aiml.Kernel()

        #aktuell wird nur die heidi aiml geladen, diese wird aus eine sql lite exportiert
        #man kann im vendor ordner aber auch aiml strukturen hinterlegen
        self.aiml.learn("vendor/aiml/botdata/standard/heidi-*.aiml")
        #self.aiml.learn("vendor/aiml/botdata/standard/std-hello.aiml")
        #self.aiml.learn("vendor/aiml/botdata/standard/std-inventions.aiml")

        self.talker = self.pluginManager.getPlugin("TalkPlugin")
        self.mqtt = self.pluginManager.getPlugin("MQTTPlugin")
        self.gpt = self.pluginManager.getPlugin("ChatGptPlugin")

    def createJsFileWithMqttData(self):
        if path.exists("./tools/html_addons/"):
            f = open("./tools/html_addons/mqttData.js", "w")
            f.write("var MQTT_HOST = '"+os.getenv("MQTT_HOST")+"';")
            f.write("var MQTT_PORT = '"+os.getenv("MQTT_PORT")+"';")
            f.write("var MQTT_WEB_PORT = '"+os.getenv("MQTT_WEB_PORT")+"';")
            
            if os.getenv("MQTT_USER") != None:
                f.write("var MQTT_USER = '"+os.getenv("MQTT_USER")+"';")
            if os.getenv("MQTT_PASS") != None:
                f.write("var MQTT_PASS = '"+os.getenv("MQTT_PASS")+"';")
            
            f.write("var MQTT_PREFIX = '"+os.getenv("MQTT_PREFIX")+"';")
            f.close()


    def __command(self, pJson):
        self.logger.debug("executing command: " + pJson)
        parseSuccess = False
        ret = None

        if type(pJson) == str:
            try:
                obj = json.loads(pJson)
                parseSuccess = True

            except Exception as e:
                self.logger.error("Cant parse json for command with string" + pJson)
                self.logger.error(e)
                self.logger.error("skipped execution of command")
        else:
            obj = pJson

        if parseSuccess:
            pluginName = obj["command"]["plugin"]
            methodName = obj["command"]["method"]
            params = obj["command"]["parameters"]

            try:
                # call the plugin method with the related params
                cmd = getattr(self.pluginManager.getPlugin(pluginName), methodName)
                ret = cmd(params)
            except Exception as e:
                self.logger.error(e)
                self.logger.error("skipped execution of command")
        return ret

    def handleInput(self, pStr):
        if pStr[:5].lower()=="alexa":
            self.logger.warning("skipping alexa command " + pStr)
            return

        if pStr != "":
            arr = ['!', '"', '§', '$', '%', '&', '/', '(', ')', '=', '?', '\'', '{', '}', '[', ']', '<', '>', '\'', '\\', "."]
            for i in arr:
                pStr = pStr.replace(i, "")

            self.logger.info("input: " + pStr)
            self.mqtt.client.publish("heidi/" + os.getenv("MQTT_PREFIX") + "/ask", pStr)
            result = self.aiml.respond(pStr)

            if result == "no_result_found":
                # wenn keine passende antwort gefunden wurde, gpt plugin befragen
                # result = self.gpt.search([pStr])
                # self.talker.talk([result])
                # self.logger.info("response: " +result)
                
                # wenn keine passende antwort gefunden wurde, in sql lite abspeichern
                # con = sqlite3.connect('db/heidi.db')
                # cur = con.cursor()
                # cur.execute("INSERT INTO wordfile VALUES (NULL, '"+pStr.upper()+"', 'Ich habe zur Zeit noch keine Antwort auf diese Frage')")
                # con.commit()
                # con.close()
                
                self.logger.info("keine passende antwort gefunden"  )
            else:
                #WENN EIN KOMMANDO IM JSON FORMAT VORLIEGT
                if(result[:1] == '{'):
                    #UND DIESES KOMMANDO ETWAS AUSGIBT
                    tmp = self.__command(result)
                    if tmp != "" and tmp != None:
                        #DANN SPRECHEN
                        self.talker.talk([tmp])

                        # tmp_str = """osascript -e 'tell application "Keyboard Maestro Engine" to do script "FD2AD24E-7633-4F59-AD8E-4EC696D35247" with parameter "<<RESULT>>"'"""
                        # tmp_str = tmp_str.replace("<<RESULT>>", tmp)
                        # os.system(tmp_str)

                #WENN KEIN KOMMANDO, SONDERN NUR TEXT
                else:
                    if result != '':
                        #DANN SPRECHEN
                        self.talker.talk([result])
                        self.logger.info("response: " +result)
                        
                        # tmp_str = """osascript -e 'tell application "Keyboard Maestro Engine" to do script "FD2AD24E-7633-4F59-AD8E-4EC696D35247" with parameter "<<RESULT>>"'"""
                        # tmp_str = tmp_str.replace("<<RESULT>>", result)
                        # os.system(tmp_str)

    def getLoggerConfig(self):
        return {
            'version': 1,
            'disable_existing_loggers': False,
            'formatters': {
                'verbose': {
                    'format': os.getenv("FILE_LOG_FORMAT"),
                },
            },
            'handlers': {
                'file1': {
                    'level': 'WARNING',
                    'class': 'logging.handlers.RotatingFileHandler',
                    'filename': os.getenv("FILE_LOG_ERROR_NAME"),
                    'formatter': 'verbose',
                    'maxBytes' : int(os.getenv("FILE_LOG_MAX_BYTES")),
                    'backupCount' : 20,
                    'encoding': 'utf8',
                },
                'file2': {
                    'level': 'DEBUG',
                    'class': 'logging.handlers.RotatingFileHandler',
                    'filename': os.getenv("FILE_LOG_DEBUG_NAME"),
                    'formatter': 'verbose',
                    'maxBytes' : int(os.getenv("FILE_LOG_MAX_BYTES")),
                    'backupCount' : 20,
                    'encoding': 'utf8',
                },
            },
            'root': {
                'handlers': ['file1', 'file2'],
                'level': 'DEBUG',
            }
    }


    def loadAimlFromDB(self):
        conn = sqlite3.connect('db/heidi.db')

        cursor = conn.execute("SELECT * FROM wordfile")
        tmp = '<?xml version="1.0" encoding="utf-8"?><aiml version="1.0">'
        for row in cursor:
            pattern = row[1]
            template = row[2]
            tmp += '<category><pattern>' + pattern + '</pattern><template>' + template + '</template></category>\n'
        tmp += '</aiml>'
        conn.close()

        file = open("./vendor/aiml/botdata/standard/heidi-general.aiml", "w")
        file.write(tmp)
        file.close()


#optionaler webserver
# class S(BaseHTTPRequestHandler):

#     def _set_response(self):
#         self.send_response(200)
#         self.send_header('Content-type', 'text/html')
#         self.end_headers()

#     def do_GET(self):
#         #logging.info("GET request,\nPath: %s\nHeaders:\n%s\n", str(self.path), str(self.headers))
#         if(self.path != '/favicon.ico'):
#             logging.info(self.path)
#             self._set_response()
#             self.wfile.write("GET request for {}".format(self.path).encode('utf-8'))

#             print("webserver aktuell noch deaktiviert, zeigt nur die request an, löst aber nichts aus")


#     def do_POST(self):
#         content_length = int(self.headers['Content-Length']) # <--- Gets the size of data
#         post_data = self.rfile.read(content_length) # <--- Gets the data itself
#         logging.info("POST request,\nPath: %s\nHeaders:\n%s\n\nBody:\n%s\n",
#                 str(self.path), str(self.headers), post_data.decode('utf-8'))

#         self._set_response()
#         self.wfile.write("POST request for {}".format(self.path).encode('utf-8'))

# def run(handler_class=S):
#     logging.basicConfig(level=logging.INFO)
    
#     server_address = ('', 8080)
#     httpd = HTTPServer(server_address, handler_class)
#     logging.info('Starting httpd...\n')
#     try:
#         httpd.serve_forever()
#     except KeyboardInterrupt:
#         pass
#     httpd.server_close()
#     logging.info('Stopping httpd...\n')

#webserver starten
#_thread.start_new_thread(run, ())


################################################################################
############################### S E R V E R  ###################################
################################################################################
heidy_instance = Heidi()
while True:
    heidy_instance.handleInput(input("> "))
