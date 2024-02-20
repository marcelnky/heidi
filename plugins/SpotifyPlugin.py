# -*- coding: utf-8 -*-
from plugins.AbstractPlugin import *
import sys
import spotipy.util as util
import spotipy
from random import randint
from spotipy import oauth2
from _thread import start_new_thread
import time, re
import math
from datetime import datetime
from datetime import datetime, timedelta
import os

# from core.db import *


class SpotifyPlugin(AbstractPlugin):

    def __init__(self, pMainClass, pPluginID):
        super().__init__(pMainClass, pPluginID)
        
        #check env file for debug flag and convert string into boolean
        self.prefetchOwnPlaylists = True if os.getenv("SPOTIFY_PREFETCH_OWN_PLAYLISTS").lower() == 'true' else False
        self.sptfy_playlists = []
        self.sptfy_newReleases = []
        self.devices = []
        self.connectionErrors = 0
        self.maxRetries = 3
        self.lastPlayedUri = ''

        if self.reconnect():
            self.sptfy_playlists = self.prefetchPlaylists()


    def setActiveDevice(self):
        bb = self.sptfy.current_playback()
        if bb == None:
            self.logger.warning("no active playing device found. using default device id from env file")
            self.deviceID = os.getenv("SPOTIPY_DEFAULT_DEVICE_ID")  # macbook
        else:
            self.logger.debug("active spotify device " + bb["device"]["name"])
            self.deviceID = bb["device"]["id"]

        return self.deviceID


    def reconnect(self):
        self.logger.debug("connecting spotify")
        SPOTIPY_CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")
        SPOTIPY_CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")
        SPOTIPY_REDIRECT_URI = os.getenv("SPOTIPY_REDIRECT_URI")
        SCOPE = os.getenv("SPOTIPY_SCOPE")
        CACHE = '.spotipyoauthcache'
        
        if SPOTIPY_CLIENT_ID == "" or SPOTIPY_CLIENT_ID == None: 
            self.logger.error("you need to enter your spotify data in the .env file")
        else:
            sp_oauth = oauth2.SpotifyOAuth(SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET, SPOTIPY_REDIRECT_URI, scope=SCOPE,
                                        cache_path=CACHE)
            access_token = util.prompt_for_user_token(os.getenv("SPOTIPY_SPOTIFY_ID"), SCOPE)

            try:
                self.sptfy = spotipy.Spotify(access_token)
                self.logger.info("successfully logged into spotify")
                results = self.sptfy.current_user()
                self.token = access_token
                self.connectionErrors = 0
                bb = self.sptfy.current_playback()

                if bb != None:
                    self.deviceID = bb["device"]["id"]

            except spotipy.client.SpotifyException as e:
                self.logger.error(e)
                self.logger.error("error - you may check your internet connection or your login data")
                self.logger.error(e)

            self.setActiveDevice()

            return True

    ####################################################
    ### Lädt die eigenen Playlists vor
    ####################################################
    def prefetchPlaylists(self):
        try:
            self.logger.debug("prefetching public playlists from spotify account")
            if self.token:
                sp = spotipy.Spotify(auth=self.token)
                arr = []
                results = sp.user_playlists(os.getenv("SPOTIPY_USER_ID"), limit=50, offset=0)
                total_available = results['total']
                self.logger.debug(str(total_available) + " playlists found")
                times_to_offset = int((total_available / 50) + 1)

                if self.prefetchOwnPlaylists == False:
                    self.logger.debug("fetching only the first 10 playlists from spotify because devmode is turned on")
                else:
                    self.logger.debug("fetching data for " + str(total_available) + " public playlists from spotify")

                for i in range(times_to_offset):
                    results = sp.user_playlists(os.getenv("SPOTIPY_USER_ID"), limit=50, offset=((i) * 50))
                    num_results = len(results['items'])
                    for i in range(num_results):
                        itemName = results['items'][i]['name']
                        arr.append(itemName)
                        my_dict = {'name': results['items'][i]['name'], 'uri': results['items'][i]['uri']}
                        self.sptfy_playlists.append(my_dict)

                    if self.prefetchOwnPlaylists == False:
                        break

                z = 0
                for i in arr:
                    z += 1

                    if self.prefetchOwnPlaylists == False:
                        if z < 10:
                            self.logger.debug(str(z) + " " + i)
                    else:
                        self.logger.debug(str(z) + " " + i)

                if self.prefetchOwnPlaylists == False:
                    self.logger.debug("10.. and many more. (set SPOTIFY_PREFETCH_OWN_PLAYLISTS='True' in the env file)")

            return self.sptfy_playlists


        except spotipy.client.SpotifyException as e:
            self.logger.error(e)
            self.connectionErrors+=1
            if self.connectionErrors < self.maxRetries:
                self.reconnect()
                self.prefetchPlaylists()

    ####################################################
    ### Ermittelt neue Alben von Künstlern auf der followed list
    ####################################################
    # def discoverNewAlbumsFromFollowedArtists(self, params):
    #     try:
    #         self.reconnect()
    #         self.logger.info("Checken ob neue Alben von den Künstlern die Du folgst erschienen sind")

    #         # sp = spotipy.Spotify(auth=self.token)
    #         sp = spotipy.Spotify(auth=self.token)
    #         results = sp.current_user_followed_artists(limit=50)

    #         # liste mit uris von allen followed artists erstellen
    #         self.logger.debug("aktuell folgst du " + str(results['artists']['total']) + " künstlern")
    #         followedArtists = []
    #         anzDurchlaufe = math.ceil(results['artists']['total'] / 50)
    #         z = 0
    #         while z < anzDurchlaufe:
    #             if z > 0:
    #                 results = sp.current_user_followed_artists(limit=50, after=id)
    #             else:
    #                 results = sp.current_user_followed_artists(limit=50)

    #             for i in results['artists']["items"]:
    #                 followedArtists.append({'name': i["name"], 'uri': i["uri"]})
    #             id = i["id"]
    #             z += 1

    #         # nun die followed artists durchlaufen und schauen obs was neues gibt
    #         count = 0
    #         self.logger.debug("checking followed artists")
    #         artists = []
    #         retString = ''
    #         for i in followedArtists:
    #             count = count + 1
    #             results = sp.artist_albums(i["uri"])

    #             for k in results["items"]:
    #                 datetime_str = k["release_date"]

    #                 if len(datetime_str) == 4:
    #                     datetime_str += "-01-01"
    #                 '''
    #                 try:
    #                     datetime_object = datetime.strptime(datetime_str, '%Y-%m-%d')
    #                     ##album muss innerhalb der letzten 6 tage rausgekommen sein
    #                     past = datetime.now() - timedelta(days=6)
    #                     present = datetime_object

    #                     if (present > past):
    #                         self.logger.debug("found album from artist: " + i["name"])
    #                         retString +=  "neues album von:" + " " + i["name"]
    #                         retString += "titel: " + k["name"]
    #                         retString += "released: " + str(present)[:-9]
    #                         retString += "trackanzahl: " + str(k["total_tracks"])
    #                         retString += "uri: " + k["uri"]

    #                 except Exception as e:
    #                     self.logger.warning("Problem beim checken von interpret: " + i["name"])
    #                     self.logger.warning(e)
    #                 '''


    #                 try:
    #                     datetime_object = datetime.strptime(datetime_str, '%Y-%m-%d')
    #                     ##album muss innerhalb der letzten 6 tage rausgekommen sein
    #                     past = datetime.now() - timedelta(days=6)
    #                     present = datetime_object

    #                     if (present > past):
    #                         artist = i["name"]
    #                         if artist not in artists:
    #                             artists.append(artist)

    #                 except Exception as e:
    #                     self.logger.warning("Problem beim checken von interpret: " + i["name"])
    #                     self.logger.warning(e)

    #         feedback = "Folgende Artists haben neue Alben released: "
    #         for a in artists:
    #             feedback += a + ", "
    #         feedback = feedback[:-2]

    #     except spotipy.client.SpotifyException as e:
    #         self.logger.error(e)
    #         self.connectionErrors += 1
    #         if self.connectionErrors < self.maxRetries:
    #             self.reconnect()
    #             self.discoverNewAlbumsFromFollowedArtists(params)

    ####################################################
    ### Ermittelt welche Ausgabegeräte zur Verfügung stehen
    ####################################################
    def checkAvailableDevices(self, params):
        try:
            self.reconnect()
            self.logger.debug("scanning all available spotify devices")
            self.devices = []

            ignoreArr = os.getenv("SPOTIPY_IGNORE_DEVICES").split(',')
            arr = self.sptfy.devices()["devices"]
            names = ''
            count = 0

            for i in arr:
                self.logger.debug(i)
                if i["name"] not in ignoreArr:
                    count += 1
                    names += str(count) + ". " + i["name"] + ", "
                    self.devices.append({'name': i["name"], 'id': i["id"]})
            names = names[:-2]

            self.logger.debug("found: " + str(self.devices))
            return "Aktuell sind folgende Spotify Geräte verfügbar: " + names


        except spotipy.client.SpotifyException as e:
            self.logger.error(e)
            self.connectionErrors += 1
            if self.connectionErrors < self.maxRetries:
                self.reconnect()
                self.checkAvailableDevices(params)

    ####################################################
    ### Wechselt das aktuelle Ausgabe Device.
    ### Als Parameter wird eine Zahl übergeben
    ####################################################
    def switchActiveAudioDevice(self, params):
        self.reconnect()
        self.logger.debug(self.devices)
        tmp = ""
        if int(params[0]) < len(self.devices) + 1:
            item = self.devices[int(params[0]) - 1]
            tmp = "Spotify wird nun auf " + item["name"] + " abgespielt "
            self.deviceID = item["id"]
            self.sptfy.transfer_playback(self.deviceID, True)
        else:
            tmp = "Kein Gerät mit dieser Nummer vorhanden"
            self.logger.warning("Kein Gerät mit dieser Nummer vorhanden")
        
        return tmp

    ####################################################
    ### Gibt das derzeit aktive Device aus
    ####################################################
    def getActiveDeviceName(self):
        try:
            self.reconnect()
            self.logger.debug("looking for active spotify device")
            arr = self.sptfy.devices()["devices"]
            found = False
            for i in arr:
                self.logger.debug(i)

                if i["is_active"] == True:
                    found = i["name"]

            if found == False:
                self.logger.warning("no active spotify device fond")
            else:
                self.logger.info("found device " + found)

            return found


        except spotipy.client.SpotifyException as e:
            self.logger.error(e)
            self.connectionErrors += 1
            if self.connectionErrors < self.maxRetries:
                self.reconnect()
                self.getActiveDeviceName()

    ####################################################
    ### Releases für 1 Land abfragen
    ####################################################
    # def getReleases(self, pLan):
    #     try:
    #         self.reconnect()
    #         sp = spotipy.Spotify(auth=self.token)
    #         ##DE RELEASES
    #         results = sp.new_releases(country=pLan, limit=50, offset=0)

    #         self.logger.info("#############################################")
    #         self.logger.info("checking new spotify releases for country: " + pLan)
    #         self.logger.info("#############################################")

    #         for i in results["albums"]["items"]:
    #             name = i["artists"][0]["name"]
    #             try:
    #                 self.logger.debug("checking genre:" + name + " - " + i["name"])
    #                 res = sp.search(q='artist:' + name, type='artist')
    #                 # genre = "No genre found"
    #                 genre = res["artists"]["items"][0]["genres"][0]
    #             except:
    #                 None

    #             skip = False
    #             if genre == "classical" or genre == 'trap' or genre == "jazz" or genre == 'k-pop' or genre == 'trap espanol' or genre == "cabaret" or genre == "alternative emo" or genre == "dance pop" or genre == "dwn trap" or genre == "deep german pop rock" or genre == "dance pop" or genre == "No genre found" or genre == "deep melodic euro house" or genre == "dirty south rap" or genre == "deep disco house" or genre == "dance pop" or genre == "contemporary country" or genre == "crunk" or genre == "deep underground hip hop" or genre == "dance pop" or genre == "latin" or genre == "neo mellow" or genre == "alternative metal" or genre == "big room" or genre == "hollywood" or genre == "alternative hip hop" or genre == "deep indie r&b" or genre == "big room" or genre == "disco house" or genre == "italian arena pop" or genre == "italian pop" or genre == "epicore" or genre == "deep groove house" or genre == "flamenco" or genre == "trap latino" or genre == "boy band" or genre == "cantautor" or genre == "post-teen pop" or genre == "destroy techno" or genre == "french indietronica" or genre == "francoto" or genre == "vocal jazz" or genre == "funk" or genre == "belgian rock" or genre == "indie christmas" or genre == "italian hip hop" or genre == "chanson" or genre == "francoton" or genre == "french pop" or genre == "french indie pop" or genre == "deep australian indie" or genre == "italian indie pop" or genre == "alternative dance" or genre == "deep latin hip hop" or genre == "pop rap" or genre == "trap francais" or genre == "chillwave" or genre == "indie poptimism" or genre == "irish rock" or genre == "detroit hip hop" or genre == "reggaeton" or genre == "chillstep" or genre == "grime" or genre == "death core" or genre == "latin pop" or genre == "spanish pop" or genre == "australian dance" or genre == "latin arena pop" or genre == "spanish indie pop" or genre == "deep euro house" or genre == "alternative country" or genre == "french hip hop" or genre == "deep german hip hop" or genre == "german hip hop" or genre == "canadian hip hop":
    #                 skip = True
    #                 self.logger.warning(
    #                     "skipped album " + i["artists"][0]["name"] + " - " + i["name"] + " genre[" + genre + "]")
    #             else:
    #                 self.logger.info("found: " + i["artists"][0]["name"] + " - " + i["name"] + " genre[" + genre + "]")
    #                 skip = False

    #             my_dict = {'name': i["artists"][0]["name"], 'uri': i["uri"], 'genre': genre, 'albumname': i["name"]}
    #             if my_dict not in self.sptfy_newReleases and not skip:
    #                 self.sptfy_newReleases.append(my_dict)

    #     except spotipy.client.SpotifyException as e:
    #         self.logger.error(e)
    #         self.connectionErrors += 1
    #         if self.connectionErrors < self.maxRetries:
    #             self.reconnect()
    #             self.getReleases(pLan)

    ####################################################
    ### Neue Releases der jeweiligen Länder abfragen
    ####################################################
    # def showNewReleases(self, params):
    #     try:
    #         self.reconnect()
    #         tmp = ""
    #         if self.token:
    #             self.logger.info("logged in")
    #             sp = spotipy.Spotify(auth=self.token)
    #             self.logger.info("fetching results")

    #             try:
    #                 self.getReleases("DE")
    #                 #self.getReleases("US")
    #                 #self.getReleases("FR")
    #                 #self.getReleases("IT")
    #                 #self.getReleases("ES")

    #                 tmp = "Diese Woche erschienen " + str(len(
    #                     self.sptfy_newReleases)) + " neue Alben bei Spotify."

    #                 kk = 0
    #                 for i in self.sptfy_newReleases:
    #                     kk += 1
    #                     #tmp += '<b>' + i['name'] + '</b> - ' + i['albumname'] + ' ' + '<a href="' + i[
    #                     #    'uri'] + '">open</a><br />'

    #                     tmp += i['name'] + " - " + i['albumname'] + " (" + i['genre'] + ")" + ""

    #                     #self.logger.info("[" + str(kk) + "] " + str(i))

    #                 self.callback(tmp)

    #             except Exception as e:
    #                 self.logger.error("error in spotify plugin")
    #                 self.logger.error(e.message)

    #             return tmp, tmp

    #         else:
    #             self.logger.error(
    #                 "cannot log into spotify - check if credentials are exported right and read the docs here: http://spotipy.readthedocs.io/en/latest/#features")


    #     except spotipy.client.SpotifyException as e:
    #         self.logger.error(e)
    #         self.connectionErrors += 1
    #         if self.connectionErrors < self.maxRetries:
    #             self.reconnect()
    #             self.showNewReleases(params)

    ####################################################
    ### spielt eine bestimmte eigene Playlist ab
    ####################################################
    def playSpecificPlaylist(self, params):
        try:
            self.reconnect()
            pName = params[0]
            self.logger.info("looking for playlist " + pName + " in Spotify")

            found = False
            for i in self.sptfy_playlists:
                playlistname = i['name'].lower()

                if pName.lower() in playlistname:
                    self.logger.debug("found " + i['name'])
                    found = i['uri']
                    nam = i['name']
                    break
            ret = ""
            if found is False:
                self.logger.warning("playlist: " + pName + " not found")
                ret = "ich konnte die playlist " + pName + " nicht finden"
            else:
                ret = "spiele playlist " + nam
                self.playSpotifyItem(found, self.deviceID)
            return ret

        except spotipy.client.SpotifyException as e:
            self.logger.error(e)
            self.connectionErrors += 1
            if self.connectionErrors < self.maxRetries:
                self.reconnect()
                self.playSpecificPlaylist(params)

    ####################################################
    ### spielt eine zufällige eigene Playlist ab
    ####################################################
    def playRandomPlaylist(self, params):
        try:
            self.reconnect()
            l = len(self.sptfy_playlists)  # länge aller alben
            z = randint(0, l)  # zufallszahl
            playlistItem = self.sptfy_playlists[z]
            self.playSpotifyItem(playlistItem['uri'], self.deviceID)
            return "spiele playlist " + playlistItem['name']

        except spotipy.client.SpotifyException as e:
            self.logger.error(e)
            self.connectionErrors += 1
            if self.connectionErrors < self.maxRetries:
                self.reconnect()
                self.playRandomPlaylist(params)


    def getCurrentTrackHelper(self):
        try:
            found = False
            self.reconnect()
            self.logger.debug("looking for current spotify track")
            a = self.sptfy.current_playback()

            if a is not None:
                self.logger.info("found track: " + a["item"]["name"])
                device = self.getActiveDeviceName()
                found =[a["item"]["name"], a["item"]["album"]["artists"][0]["name"], device]
            return found

        except spotipy.client.SpotifyException as e:
            self.logger.error(e)
            self.connectionErrors += 1
            if self.connectionErrors < self.maxRetries:
                self.reconnect()
                self.getCurrentTrackHelper()

    ####################################################
    ### gibt den aktuell gespielten track zurück
    ####################################################
    def getCurrentTrack(self, params):
        tmp = self.getCurrentTrackHelper()
        if tmp != False:
            return "aktuell läuft " + tmp[0] + " von " + tmp[1]
        else:
            return "aktuell wird kein lied abgespielt"

    ####################################################
    ### gibt einen artist anhand des namens zurück
    ####################################################
    def get_artist(self, name):
        try:
            results = self.sptfy.search(q='artist:' + name, type='artist')
            items = results['artists']['items']
            if len(items) > 0:
                return items[0]
            else:
                return None

        except spotipy.client.SpotifyException as e:
            self.logger.error(e)
            self.connectionErrors += 1
            if self.connectionErrors < self.maxRetries:
                self.reconnect()
                self.get_artist(name)

    ####################################################
    ### gibt alle alben des übergebenen artist objektes zurück
    ####################################################
    def get_all_albums_from_artist(self, pArtist):
        try:
            #self.reconnect()
            albums = []
            artist = self.get_artist(pArtist)

            if artist == None:
                return []

            results = self.sptfy.artist_albums(artist['id'], album_type='album')

            albums.extend(results['items'])
            while results['next']:
                results = self.sptfy.next(results)
                albums.extend(results['items'])
            seen = set()  # to avoid dups
            albums.sort(key=lambda album: album['name'].lower())
            for album in albums:
                name = album['name']
                if name not in seen:
                    self.logger.debug("found album: " + name)
                seen.add(name)
            return albums

        except spotipy.client.SpotifyException as e:
            self.logger.error(e)
            self.connectionErrors += 1
            if self.connectionErrors < self.maxRetries:
                self.reconnect()
                self.get_all_albums_from_artist(pArtist)

    ####################################################
    ### liefert ein zufälliges Album anhand des artistnamens
    ####################################################
    def get_random_album_from_artist(self, params):
        try:
            self.reconnect()
            searchword = params[0]
            try:
                arr = self.get_all_albums_from_artist(searchword)
            except:
                arr = []

            ret = ""
            if len(arr) > 0:
                l = len(arr) - 1  # länge aller alben
                z = randint(0, l)  #
                album = arr[z]
                ret = "spiele album " + album["name"]
                
                self.sptfy.transfer_playback(self.deviceID, force_play=True)
                self.playSpotifyItem(album["uri"], self.deviceID)

            else:
                self.logger.warning("No Albums for " + searchword + " found")
                ret = "Ich habe keine Alben zu " + searchword + " gefunden."
            return ret

        except spotipy.client.SpotifyException as e:
            self.logger.error(e)
            self.connectionErrors += 1
            if self.connectionErrors < self.maxRetries:
                self.reconnect()
                self.get_random_album_from_artist(params)

    ####################################################
    ### spiele das lied xy von zzz
    ####################################################
    def playTrackByArtist(self, params):
        try:
            self.reconnect()
            trackname = params[0]
            artistname = params[1]

            self.logger.debug("looking for track: " + trackname + " from " + artistname)
            results = self.sptfy.search(q='artist:' + artistname + ' track:' + trackname, type='track')

            total = len(results["tracks"]["items"])
            if total > 0:
                self.logger.debug("tracks found: " + str(total))

                uri = results["tracks"]["items"][0]["uri"]
                trackname = results["tracks"]["items"][0]["name"]
                artistname = results["tracks"]["items"][0]["artists"][0]["name"]

                self.logger.debug("picking first track")
                #self.logger.debug(results["tracks"]["items"][0])
                #self.logger.debug("uri: " + uri)
                self.logger.info("playing " + trackname + " from " + artistname)

                self.playSpotifyItem([uri], self.deviceID)

            else:
                self.logger.warning("found no tracks")

        except spotipy.client.SpotifyException as e:
            self.logger.error(e)
            self.connectionErrors += 1
            if self.connectionErrors < self.maxRetries:
                self.reconnect()
                self.playTrackByArtist(params)

    ####################################################
    ### spiele das Album XXX von YYY
    ####################################################
    def playAlbumByArtist(self, params):
        try:
            self.reconnect()
            albumname = params[0]
            artistname = params[1]
            artist = self.get_artist(artistname)

            if artist == None:
                self.logger.warning("No Artist found")
            else:
                albums = self.get_all_albums_from_artist(artistname)
                found = False
                for i in albums:
                    if albumname.lower() in i["name"].lower():
                        found = i
                        break

                if found:
                    self.logger.info("spiele " + i["name"] + " von " + artistname)
                    self.playSpotifyItem(i["uri"], self.deviceID)
                else:
                    self.logger.warning("Kein Album mit dem Namen " + albumname + " von " + artistname + " gefunden")

        except spotipy.client.SpotifyException as e:
            self.logger.error(e)
            self.connectionErrors += 1
            if self.connectionErrors < self.maxRetries:
                self.reconnect()
                self.playAlbumByArtist(params)

    ####################################################
    ### spielt genau ein zufälliges lied von einem interpret
    ### BSP: SPiele ein Lied von Bran Van 3000
    ####################################################
    def playRandomSongByArtist(self, params):
        try:
            self.reconnect()
            pArtist = params[0]

            # zuerst alle alben auslesen
            arr = self.get_all_albums_from_artist(pArtist)
            ret = ""
            if len(arr) > 0:

                # zufälliges album auswählen
                l = len(arr) - 1
                z = randint(0, l)
                album = arr[z]
                self.logger.info("picked album " + album["name"])

                # tracks des albums auslesen
                tracks = self.sptfy.album_tracks(album["id"])
                self.logger.info("album hat " + str(album["total_tracks"]) + " tracks")

                # zufälligen track auslesen
                z = randint(0, album["total_tracks"] - 1)  #
                self.logger.info("spiele lied nr: " + str(z))

                track = tracks['items'][z-1]

                # alle verfügbaren lieder anzeigen
                count=0
                for trackitem in tracks['items']:
                    count +=1
                    self.logger.debug(str(count) + ": " + trackitem['name'])

                # lied abspielen
                self.logger.info("chosed track: " + track['name'])
                ret = "spiele " + track['name'] + " von " + pArtist
                self.playSpotifyItem([track['uri']], self.deviceID)

            else:
                self.logger.warning("No Tracks for " + pArtist + " found")
                ret = "Ich habe keine Lieder von " + pArtist + " gefunden."
            
            return ret


        except spotipy.client.SpotifyException as e:
            self.logger.error(e)
            self.connectionErrors += 1
            if self.connectionErrors < self.maxRetries:
                self.reconnect()
                self.playRandomSongByArtist(params)

    ####################################################
    ### stoppt die ausgabe auf dem aktuellen device
    ####################################################
    def stopPlayback(self, params):
        try:
            self.setActiveDevice()
            self.sptfy.pause_playback(self.deviceID)
        except spotipy.client.SpotifyException as e:
            self.logger.error(e)

    ####################################################
    ### startet die ausgabe auf dem aktuellen device
    ####################################################
    def startPlayback(self, params):
        try:
            self.setActiveDevice()
            self.sptfy.start_playback(self.deviceID)
        except spotipy.client.SpotifyException as e:
            self.logger.error(e)

    ####################################################
    ### spielt das nächste lied
    ####################################################
    def nextPlayback(self, params):
        try:
            self.setActiveDevice()
            self.reconnect()
            a = self.sptfy.current_playback()
            if a != None:
                self.logger.info("playing next spotify track")
                self.sptfy.next_track(self.deviceID)
                return ""
            else:
                self.logger.info("No track playing")
                return "aktuell wird kein lied abgespielt"

        except spotipy.client.SpotifyException as e:
            self.logger.error(e)
            self.logger.error("This Error often happens when you try to play, but there isnt any playing track. Use: 'spiele ein lied von xy' instead")
            self.connectionErrors += 1
            if self.connectionErrors < self.maxRetries:
                self.reconnect()

    ####################################################
    ### spielt das vorige lied
    ####################################################
    def prevPlayback(self, params):
        try:
            self.setActiveDevice()
            self.reconnect()
            a = self.sptfy.current_playback()
            if a != None:
                self.logger.info("playing previous spotify track")
                self.sptfy.previous_track(self.deviceID)
                return ""
            else:
                self.logger.info("No track playing")
                return "aktuell wird kein lied abgespielt"

        except spotipy.client.SpotifyException as e:
            self.logger.error(e)
            self.logger.error(
                "This Error often happens when you try to play, but there isnt any playing track. Use: 'spiele ein lied von xy' instead")
            self.connectionErrors += 1
            if self.connectionErrors < self.maxRetries:
                self.reconnect()

    ####################################################
    ### wird von allen anderen Methoden zum abspielen eines liedes verwendet
    ####################################################
    def playSpotifyItem(self, pUri, pDeviceID = os.getenv("SPOTIPY_DEFAULT_DEVICE_ID")):
        self.lastPlayedUri = pUri
        self.setActiveDevice()

        if type(pUri) == list:
            self.sptfy.start_playback(pDeviceID, uris = pUri)
        else:
            self.sptfy.start_playback(pDeviceID, pUri)
