
import time, os.path
import pymysql.cursors

class db_DB:

    connection = None
    table = None
    server = None
    port = None
    db = None
    user = None
    passwd = None
    table = None

    def __init__(self, server, port, db, user, passwd, table):

        self.table = table
        self.server = server
        self.port = port
        self.db = db
        self.user = user
        self.passwd = passwd
        self.table = table
        self.connect(server, port, db, user, passwd)


    def reconnect(self):
        print ("reconnect to Database")
        self.connect(self.server, self.port, self.db, self.user, self.passwd)


    def connect(self, server, port, db, user, passwd):
        con = None
        try:

            con = pymysql.connect(host=server, port=port, user=user, passwd=passwd, db=db, charset='utf8mb4', cursorclass=pymysql.cursors.DictCursor)
            con.ping(True)
        except pymysql.Error as e:
            print ("Error %d: %s" % (e.args[0], e.args[1]))
            #db_DB.connection = None
            #sys.exit(1)
        except pymysql.ProgrammingError as e:
            print ("Error %d: %s" % (e.args[0], e.args[1]))
            db_DB.connection = None
        finally:
            if con:
                db_DB.connection = con



    def createTable(self):
        sql = "CREATE TABLE IF NOT EXISTS `" + self.table +  "` (`ID` int(11) unsigned NOT NULL auto_increment,`ts_start` varchar(255),`ts_stop` varchar(255),`format` varchar(255),`filename` MEDIUMTEXT,`file_state` tinyint(1),`file_progress` tinyint(2), `message` MEDIUMTEXT, PRIMARY KEY  (`ID`))"
        if(not self.check_if_table_exists()):
            self.db_commit(sql)


    def check_if_table_exists (self):
        stmt = "SHOW TABLES LIKE '" + self.table + "'"
        c = db_DB.connection.cursor()
        c.execute(stmt)
        result = c.fetchone()
        db_DB.connection.commit()
        c.close()
        if result:
            return True
        else:
            return False



    def db_commit(self, sql):
        try:
            c = db_DB.connection.cursor()
            c.execute(sql)
            db_DB.connection.commit()
            c.close()
        except pymysql.Error as e:
            print ("Error %d: %s" % (e.args[0], e.args[1]))



    def disconnect(self):
        self.connection.close()
        self.connection = None


    def select(self,sql):
        try:
            cursor = self.connection.cursor()
            if cursor:
                cursor.execute(sql)
                results = cursor.fetchall()
                self.connection.commit()
                cursor.close()
                if(len(results) > 0):
                    return results

        except pymysql.Error as e:
            print ("Error %d: %s" % (e))


    def update_job(self, job_id, state, messsage, progress):
        if(not int(progress)):
            progress=0
        sql = "update " + self.table + " set file_state='" + str(state) + "',message='"+ str(messsage) +"',file_progress='"+ str(progress) +"' where ID='"+ str(job_id)  +"'"
        self.db_commit(sql)


    def next_job(self):
        sql = "select filename,format,ID from " + self.table + " where file_state='0' order by ts_start LIMIT 1"
        results = self.select(sql)
        if(results):
            return results[0]



    def db_clean(self):
        sql = "select ID,filename from " + self.table
        results = self.select(sql)
        if results:
            for row in results:
                if(not os.path.isfile(row['filename'])):
                    sql = "delete from " + self.table + " where ID='" + str(row['ID']) + "'"
                    print ("delete db_entry : %5d" % (row['ID']))
                    self.db_commit(sql)


    def check_entry(self,fullPathFile):
        c = None
        sql = "select id from " + self.table + " where filename ='"+ fullPathFile +"'"

        try:
            if self.connection:
                c = db_DB.connection.cursor()
            c.execute(sql)
            result = c.fetchone()
            db_DB.connection.commit()
            c.close()
            if result:
                return True
            else:
                return False

        except pymysql.ProgrammingError as e:
            print ("Error %d: %s" % (e.args[0], e.args[1]))
        except pymysql.Error as e:
            print ("Error %d: %s" % (e.args[0], e.args[1]))


    def add_entry(self, fullPathFile,subFolder):
        timestamp = int(time.time())
        sql = "INSERT INTO " + self.table + " (filename,ts_start,format,file_state) VALUES('"+ fullPathFile + "','" + str(timestamp) + "','"+ subFolder  +"','0')"
        print (sql)
        self.db_commit(sql)
