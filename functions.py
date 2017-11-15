import MySQLdb
import sys, os, shutil, threading, pexpect
import time
import ConfigParser
import string

global currentSlots
currentSlots = 0


def gen_ff_cmd(file):
    ifile = watchfolder + "/" + wf + "/" + file
    ofile = outfolder + "/" + file
    template = getCoderTemplate(wf,cfg)
    nt = template.replace("[input]", "\"" + ifile + "\"")
    nt = nt.replace("[output]", os.path.splitext( "\"" + ofile)[0] + "\"")
    nt = nt.replace("[ffmpeg_8bit]", getconfig(cfg, "general", "ffmpeg_8bit"))
    nt = nt.replace("[ffmpeg_10bit]", getconfig(cfg, "general", "ffmpeg_10bit"))
    return nt


def runCMD(rCommand):
    thread = pexpect.spawn(rCommand)
    print "started %s" % rCommand
    cpl = thread.compile_pattern_list([
        pexpect.EOF,
        "frame= *\d+",
        '(.+)'
    ])
    while True:
        i = thread.expect_list(cpl, timeout=None)
        if i == 0: # EOF
            print "the sub process exited"
            break
        elif i == 1:
            frame_number = thread.match.group(0)
            print frame_number
            thread.close
        elif i == 2:
            #unknown_line = thread.match.group(0)
            #print unknown_line
            pass



def execute_next_job(nt,nt_id,mSlots):
    global currentSlots
    if(currentSlots <= mSlots):
        currentSlots += 1
        job = threading.Thread(target=runCMD, args=(nt,))
        job.start()
        currentSlots -=1



def watch(watchfolder,outfolder,cfg):
    wf_array = os.listdir(watchfolder)
    for wf in wf_array:
        for file in os.listdir(watchfolder + "/" + wf):
            fullPathFile = watchfolder + "/" + wf + "/" + file
            if (not execute("check", fullPathFile, dbConnection, dbTable)):
                execute("add", file, dbConnection, dbTable)




def getCoderTemplate(format,cfg):
    template = getconfig(cfg, "formats", format)
    return template


def checkFolder(of,wf, items):
    if (not os.path.isdir(of)):
        os._make_statvfs_resultdirs(of)

    for fmt,desc in items:
        infolder = wf + "/" + fmt
        if (not os.path.isdir(infolder)):
            os.makedirs(infolder)
            print "create folder: " + infolder


def writelog(logfile, text):
    datetime = time.asctime(time.localtime(time.time()))
    log = open(logfile, "a")
    log.write(str(datetime) + " ## " + text+"\n\r")
    log.close()


def getconfig(configFile, section, option):
    config = ConfigParser.ConfigParser()
    config.read(configFile)
    value = config.get(section, option)
    return value


def getconfigOptions(configFile, section):
    config = ConfigParser.ConfigParser()
    config.read(configFile)
    options = dict(config.items(section))
    return options


def get_extension(filename):
    basename = os.path.basename(filename)  # os independent
    extension = os.path.splitext(basename)[1][1:]
    return extension if extension else None


def mysql_connect(mysql_server, mysql_port, mysql_db, mysql_user, mysql_pass, logfile):
    con = []
    try:
        con = MySQLdb.connect(host=mysql_server, port=mysql_port, user=mysql_user, passwd=mysql_pass, db=mysql_db)

    except MySQLdb.Error, e:
        print "Error %d: %s" % (e.args[0], e.args[1])
        writelog(logfile, "Error: " + e.args[0] + " " + e.args[1])
        sys.exit(1)

    finally:
        if con:
            return con


def mysql_disconnect(con):
    con.close()


def handler(signum,frame):
    sys.exit(0)
