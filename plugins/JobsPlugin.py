# -*- coding: utf-8 -*-
from plugins.AbstractPlugin import *
from apscheduler.schedulers.background import BackgroundScheduler
import logging
import json
import sqlite3
import tzlocal

class JobsPlugin(AbstractPlugin):

    def __init__(self, pMainClass, pPluginID):
        super().__init__(pMainClass, pPluginID)

        # BACKGROUND SCHEDULER
        self.ow.scheduler = BackgroundScheduler(timezone=str(tzlocal.get_localzone()))

    def loadJobs(self):
        self.loadJobsFromDB()
        self.ow.scheduler.start()

    def loadJobsFromDB(self):
        self.logger.debug("selecting jobs from database")

        conn = sqlite3.connect('db/heidi.db')
        cursor = conn.execute("SELECT * FROM jobs")

        # JOBS AUS DB AUSLESEN
        for row in cursor:
            row_time    = row[1].split(" ")
            row_cmd     = row[2]
            row_method  = row[3]
            row_params  = row[4]
            row_active  = row[5]

            if not row_active:
                self.logger.debug("skipped job " + row_cmd)
            else:
                params = []
                cmd = ()
                if row_params != "":
                    #PARAMETER ALS JSON LADEN
                    tmp = json.loads(row_params)

                    #IN ZUSATZ ARRAY PACKEN, WICHTIG
                    params = [tmp["parameters"]] 
                
                    #ENTSPRECHENDE METHODE AUS DEM PLUGIN REFERENZIEREN
                    cmd = getattr(self.ow.pluginManager.getPlugin(row_cmd), row_method)

                #FALLS INTERVALL
                if 'INTERVAL' in row[1]:
                    if row_time[3].lower() == 'seconds':
                        self.ow.scheduler.add_job(cmd, 'interval', params, seconds=int(row_time[2]))

                    elif row_time[3].lower() == 'minutes':
                        self.ow.scheduler.add_job(cmd, 'interval', params, minutes=int(row_time[2]))

                    elif row_time[3].lower() == 'hours':
                        self.ow.scheduler.add_job(cmd, 'interval', params, hours=int(row_time[2]))

                # FALLS KONKRETE UHRZEIT (CRON)
                else:
                    hour = row_time[1].split(':')[0]
                    minute =  row_time[1].split(':')[1]
                    second =  row_time[1].split(':')[2]

                    if row_cmd != '':
                        self.ow.scheduler.add_job(cmd, 'cron', params, day_of_week=row_time[0], hour=hour, minute=minute)

                self.logger.info("creating job " + row_cmd + "." + row_method + " - params:" +  str(params))

        conn.close()
