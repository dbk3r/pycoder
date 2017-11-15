#!/usr/bin/env python
import web
import json
import uuid

from config_class import *
from sqlite_class import *
from io_class import *


urls = (
    '/getstat/(.*)', 'get_stat',
    '/addjob/(.*)', 'add_job'
)

app = web.application(urls, globals())

class get_stat:
    def GET(self,uuid):
        stat = ""
        return stat

class add_job:
    def GET(self, jstring):
        j = json.loads(jstring)
        inFile = j['in']
        outDir = j['out']
        outFormat = j['format']
        new_uuid = str(uuid.uuid4())
        return new_uuid

if __name__ == "__main__":
    app.run()
