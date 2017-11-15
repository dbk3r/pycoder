import sys, os, shlex, os, time, subprocess,re, pexpect, random
#from capturer import CaptureOutput


class db_IO:

    currentSlots = 0
    logfile = None

    def __init__(self,logfile):
        self.logfile = logfile


    def get_filename(self,fullPathFile):
        return os.path.basename(fullPathFile)

    def get_extension(self,filename):
        basename = os.path.basename(filename)  # os independent
        extension = os.path.splitext(basename)[1][1:]
        return extension if extension else None


    def handler(self,signum,frame):
        sys.exit(2)


    def checkIoFolder(self, outfolder,watchfolder, formats):
        if (not os.path.isdir(outfolder)):
            os.mkdirs(outfolder)

        for fmt,desc in formats:
            infolder = watchfolder + "/" + fmt
            if (not os.path.isdir(infolder)):
                os.makedirs(infolder)
                print ("create folder: " + infolder)



    def file_is_locked(self,filepath):
        locked = None
        try:
            os.rename(filepath, filepath+".ren")
            os.rename(filepath+".ren", filepath)
            locked = False
        except OSError as e:
            locked = True
        return locked



    def writelog(self, text):
        datetime = time.asctime(time.localtime(time.time()))
        log = open(self.logfile, "a")
        log.write(str(datetime) + " ## " + text+"\n\r")
        log.close()


    def execute_cmd(self,command):
        try:
            cmd = subprocess.run(command, shell=True, stdout=subprocess.PIPE, universal_newlines=True)
            return cmd.stdout
        except:
            print ("execution Error")
            return "0"


    def get_start_timecode(self, iFile, ffprobe):
        try:
            starttimecode = subprocess.run(ffprobe + ' -v 0 -show_entries format_tags=timecode -of default=noprint_wrappers=1 \"' + iFile + '\"', shell=True, stdout=subprocess.PIPE, universal_newlines=True)
            return starttimecode.stdout
        except:
            print ("MediaInfo-Error")
            return "0"

    def get_audio_stream_channel(self, iFile, mediainfo):
        try:
            streamchannel = subprocess.run(mediainfo + ' \"--Inform=Audio;%Channels%\" \"' + iFile + '\"', shell=True, stdout=subprocess.PIPE, universal_newlines=True)
            #print(mediainfo + ' \"--Inform=Audio;%Channels%\" \"' + iFile + '\"')
            return streamchannel.stdout
        except:
            print ("MediaInfo-Error")
            return "0"


    def get_audio_stream_order(self, iFile, mediainfo):
        try:
            streamorder = subprocess.run(mediainfo + ' \"--Inform=Audio;%StreamOrder%\" \"' + iFile + '\"', shell=True, stdout=subprocess.PIPE, universal_newlines=True)
            #print(mediainfo + ' \"--Inform=Audio;%StreamOrder%\" \"' + iFile + '\"')
            return streamorder.stdout
        except:
            print ("MediaInfo-Error")
            return "0"

    def getFrameCount(self,iFile,mediainfo):
        try:
            framecount = subprocess.run(mediainfo + ' \"--Inform=Video;%FrameCount%\" \"' + iFile + '\"', shell=True, stdout=subprocess.PIPE, universal_newlines=True)
            return framecount.stdout
        except:
            print ("MediaInfo-Error")
            return 0


    def makeSafeFilename(inputFilename):
        try:
            safechars = string.letters + string.digits + " -_."
            return filter(lambda c: c in safechars, inputFilename)
        except:
            return ""
        pass


    def runCMD(self, rCommand,frameCount,SQL_CONNECTION,job_id, filename, rewrap):
        print(rCommand)
        thread = pexpect.spawnu(rCommand)
        cpl = thread.compile_pattern_list([pexpect.EOF, "frame= *\d+", '(.+)'])
        message = ""
        progress = 0
        SQL_CONNECTION.update_job(job_id,"1","",0,'1')
        while True:
            try:
                i = thread.expect_list(cpl, timeout=None)
                if i == 0: # EOF
                    if message:
                        print (message)
                        SQL_CONNECTION.update_job(job_id,"99",message,progress,'0')
                    else:
                        SQL_CONNECTION.update_job(job_id,"2","",100,'0')

                    if(not rewrap == ""):
                        for rewrap_cmd in rewrap:
                            SQL_CONNECTION.update_job(job_id,"1","rewrapping",99,'0')
                            self.writelog('DO: ' + rewrap_cmd)
                            print ('DO: ' + rewrap_cmd)
                            self.execute_cmd(rewrap_cmd)

                    self.writelog('DONE: ' + filename)
                    SQL_CONNECTION.update_job(job_id,"2","done",100,'0')
                    break

                elif i == 1:
                    frame_number = thread.match.group(0).split()
                    try:
                        progress = int(frame_number[1]) * 100 / int(frameCount)
                    except:
                        progress = 0
                    SQL_CONNECTION.update_job(job_id,"1","",progress,'0')
                    print (str(job_id) + " : " + str(int(progress)))
                    time.sleep(1)

                    thread.close
                elif i == 2:
                    unknown_line = thread.match.group(0)
                    if("fps=" not in unknown_line):
                        if "error" in unknown_line:
                            message += unknown_line

            except OSError as e:
                print (e)
