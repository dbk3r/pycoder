#!/usr/local/python-3.5.2/bin/python3.5

import os, sys, time, threading
import signal, uuid, argparse, socket

from config_class import *
#from db_class import *
from sqlite_class import *
from io_class import *




#config_file = os.path.dirname(os.path.realpath(sys.argv[0])) + "/dbtranscode.conf"
parser = argparse.ArgumentParser()
cf = os.path.dirname(os.path.realpath(sys.argv[0])) + "/dbtranscode.conf"
parser.add_argument('-m', action='store', dest='module', help='seeker | coder', default='seeker')
parser.add_argument('-c', action='store', dest='configfile', help='Config File', default=cf)
parser.add_argument('--version', action='version', version='%(prog)s 0.1')

results = parser.parse_args()
module = results.module
config_file = results.configfile

CONFIG = db_config(config_file)
SQL_CONNECTION = sqlite_DB(CONFIG.sql_db, CONFIG.sql_table)
IO = db_IO(CONFIG.logfile)
maxTranscodingSlots = 3

signal.signal(signal.SIGTERM, IO.handler)
signal.signal(signal.SIGINT, IO.handler)

IO.checkIoFolder(CONFIG.outfolder, CONFIG.watchfolder, CONFIG.formats.items())
SQL_CONNECTION.createTable()

IO.writelog('dbtranscode-' + module + '[' + socket.gethostname() + '] started.')


try:
    loop = 0
    while True:

        if(module == "seeker"):
            wf_array = os.listdir(CONFIG.watchfolder)
            for wf in wf_array:
                for file in os.listdir(CONFIG.watchfolder + "/" + wf):
                    fullPathFile = CONFIG.watchfolder + "/" + wf + "/" + file
                    if(IO.file_is_locked(fullPathFile)):
                        continue
                    if(IO.get_extension(file).lower() in CONFIG.extensions):
                        if (not SQL_CONNECTION.check_entry(fullPathFile)):
                            SQL_CONNECTION.add_entry(fullPathFile,wf)
                            IO.writelog('add '+ fullPathFile + ' to Queue')
            if(loop == 2):
                SQL_CONNECTION.db_clean()
                loop = 0

        elif(module == "coder"):
            nextjob = SQL_CONNECTION.next_job()
            if(nextjob):
                if(threading.activeCount() <= maxTranscodingSlots):
                    nextjob_id = nextjob['post_id']
                    SQL_CONNECTION.update_job(nextjob_id, "1","", 0,'0')
                    fCount = IO.getFrameCount(nextjob['filename'],CONFIG.mediainfo)
                    ff_command = CONFIG.gen_ff_cmd(IO, nextjob['filename'], nextjob['format'])
                    rewrap = []
                    if(nextjob['format'] == "avcintra100"):
                        try:
                            rewrap.append(CONFIG.bmxtranswrap + " -t op1a --afd 8 --ard-zdf-hdf -o \"" + CONFIG.outfolder + "/" + os.path.splitext(IO.get_filename(nextjob['filename']))[0] + "_.mxf\"" + " \"" +  CONFIG.outfolder + "/" + os.path.splitext(IO.get_filename(nextjob['filename']))[0] + ".mxf\"")
                            rewrap.append("/usr/bin/rm \"" + CONFIG.outfolder + "/" + os.path.splitext(IO.get_filename(nextjob['filename']))[0] + ".mxf\"")
                        except:
                            pass
                    else:
                        rewrap = []

                    try:
                        t = threading.Thread(target=IO.runCMD, args=[ff_command,fCount,SQL_CONNECTION,nextjob_id, nextjob['filename'], rewrap])
                        t.start()
                        IO.writelog('start ' + nextjob['filename'] + ' transcode to ' + nextjob['format'] )
                    except Error as e:
                        print ("Error %d: %s" % (e.args[0], e.args[1]))

        else:
            sys.exit(2)
        time.sleep(2)
        loop += 1


finally:
    time.sleep(1)
    IO.writelog('dbtranscoder ' + module + ' stopped.')
    print ("exit")
