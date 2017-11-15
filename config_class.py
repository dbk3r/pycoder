import sys, os
import time
import configparser
import string

class db_config:

    configFile = None
    ff8 = None
    ffprobe = None
    ffmbc = None
    bmxtranswrap = None
    mediainfo = None
    watchfolder = None
    outfolder = None
    formats = None
    extensions = []
    sql_db = None
    logfile = None
    sql_table = None

    def __init__(self, configFile):
        db_config.configFile = configFile
        db_config.sql_db = self.getconfig("sqlite", "database")
        db_config.sql_table = self.getconfig("sqlite", "table")
        db_config.logfile = self.getconfig("general", "logfile")
        db_config.ff8 =  self.getconfig("general", "ffmpeg_8bit")
        db_config.ffmbc =  self.getconfig("general", "ffmbc")
        db_config.ffprobe =  self.getconfig("general", "ffprobe")
        db_config.bmxtranswrap =  self.getconfig("general", "bmxtranswrap")
        db_config.mediainfo =  self.getconfig("general", "mediainfo")
        db_config.watchfolder = self.getconfig("general", "watchfolder")
        db_config.outfolder = self.getconfig("general", "outfolder")
        db_config.formats = self.getconfigOptions("formats")
        db_config.extensions = self.getconfig("general", "extensions").split(",")


    def gen_ff_cmd(self, IO, fullPathFile,wf):
        file = IO.get_filename(fullPathFile)
        file_ext = IO.get_extension(file)

        audio_stream_channel = list(IO.get_audio_stream_channel(fullPathFile,self.mediainfo).rstrip('\n'))
        audio_stream_order = list(IO.get_audio_stream_order(fullPathFile,self.mediainfo).rstrip('\n'))
        start_timecode = IO.get_start_timecode(fullPathFile,self.ffprobe).rstrip('\n').split('=')
        timecode = ""
        audio_stream_order = [x for x in audio_stream_order if x != '-']
        print(audio_stream_order)
        print(audio_stream_channel)
        if(len(start_timecode) > 1):
            timecode = "-timecode " + start_timecode[1]

        map_audio_channel = ""
        newaudio = ""
        channel_count = 0

        if(not file_ext == "ts"):
            try:
                if(int(audio_stream_order[0]) == 0):
                    fixchannel = 1
                else:
                    fixchannel = 0
                ac = 0

            except:
                pass

            try:
                for audiostream in audio_stream_order:
                    ac += 1
                    if(int(audio_stream_channel[channel_count]) > 1 and len(audio_stream_order) < 2):
                        map_audio_channel += " -map_audio_channel 0:" + str(audiostream) + ":0:0:" + str(ac) + " -map_audio_channel 0:" + str(audiostream) + ":1:0:" + str(int(ac) + 1)
                        newaudio = " -newaudio"
                        break
                    else:
                        map_audio_channel += " -map_audio_channel 0:" + str(int(audiostream))  + ":0:0:" + str(int(ac))
                    channel_count += 1
            except:
                pass

            for nv in range(1, channel_count):
                newaudio += " -newaudio"
            #print (map_audio_channel + " " + newaudio)

        ifile = self.watchfolder + "/" + wf + "/" + file
        ofile = self.outfolder + "/" + file
        template = self.getconfig("formats", wf)
        nt = template.replace("[input]", "\"" + ifile + "\"")
        nt = nt.replace("[output]", os.path.splitext( "\"" + ofile)[0] + "\"")
        nt = nt.replace("[ffmpeg_8bit]", self.getconfig("general", "ffmpeg_8bit"))
        nt = nt.replace("[ffmbc]", self.getconfig("general", "ffmbc"))
        nt = nt.replace("[audio_mapping]", map_audio_channel)
        nt = nt.replace("[newaudio]", newaudio)
        nt = nt.replace("[timecode]", timecode)
        return nt


    def getconfig(self, section, option):
        config = configparser.ConfigParser()
        config.read(db_config.configFile)
        value = config.get(section, option)
        return value


    def getconfigOptions(self, section):
        config = configparser.ConfigParser()
        config.read(db_config.configFile)
        options = dict(config.items(section))
        return options
