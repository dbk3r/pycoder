import time, os.path, sys
import sqlite3




class sqlite_DB:

    connection = None
    table = None
    db = None


    def __init__(self, db_filename, table):

        self.table = table
        self.db = db_filename
        self.table = table
        self.connection = sqlite3.connect(db_filename, check_same_thread=False)
        self.connection.row_factory = sqlite3.Row


    def createTable(self):
        sql = "CREATE TABLE IF not exists " + self.table +  " (post_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,ts_start varchar(255),ts_stop varchar(255),format varchar(255),filename MEDIUMTEXT,file_state INTEGER,file_progress INTEGER, message MEDIUMTEXT)"
        self.db_commit(sql)




    def db_commit(self, sql):
        try:
            cur = self.connection.cursor()
            cur.execute(sql)
            self.connection.commit()
        except sqlite3.Error as e:
            print ("SQLite-Error : " + (str(e)))




    def select(self,sql):
        try:
            cursor = self.connection.cursor()
            if cursor:
                cursor.execute(sql)
                results = cursor.fetchall()
                if(len(results) > 0):
                    return results

        except sqlite3.Error as e:
            print ("Error %d: %s" % (e))


    def update_job(self, job_id, state, messsage, progress, just_started):
        ts = time.time()
        if(not int(progress)):
            progress=0
        if state == '2':
            sql =  "update " + self.table + " set ts_stop='"+ str(ts) +"',file_state='" + str(state) + "',message='"+ str(messsage) +"',file_progress='"+ str(progress) +"' where post_id='"+ str(job_id)  +"';"
        elif just_started == '1':
            sql = "update " + self.table + " set ts_start='"+ str(ts) +"',file_state='" + str(state) + "',message='"+ str(messsage) +"',file_progress='"+ str(progress) +"' where post_id='"+ str(job_id)  +"';"
        else:
            sql = "update " + self.table + " set file_state='" + str(state) + "',message='"+ str(messsage) +"',file_progress='"+ str(progress) +"' where post_id='"+ str(job_id)  +"';"
        self.db_commit(sql)



    def next_job(self):
        sql = "select filename,format,post_id from " + self.table + " where file_state='0' order by ts_start LIMIT 1;"
        results = self.select(sql)
        if(results):
            return results[0]



    def db_clean(self):
        sql = "select post_id,filename from " + self.table + ";"
        results = self.select(sql)

        if results:
            for row in results:
                if(not os.path.isfile(row['filename'])):
                    sql = "delete from " + self.table + " where post_id='" + str(row['post_id']) + "';"
                    print ("delete db_entry : %5d" % (row['post_id']))
                    self.db_commit(sql)


    def check_entry(self,fullPathFile):
        c = None
        sql = "select post_id from " + self.table + " where filename ='"+ fullPathFile +"';"

        try:
            if self.connection:
                c = self.connection.cursor()
                c.execute(sql)
                result = c.fetchone()

            if result:
                return True
            else:
                return False

        except sqlite3.Error as e:
            print ("Error " + str(e))


    def add_entry(self, fullPathFile,subFolder):
        timestamp = int(time.time())
        sql = "INSERT INTO " + self.table + " (filename,ts_start,format,file_state) VALUES('"+ fullPathFile + "','" + str(timestamp) + "','"+ subFolder  +"','0');"
        print (sql)
        self.db_commit(sql)
