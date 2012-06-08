from httplib import HTTPConnection, HTTPException
import json
import os
import socket

from crab import CrabError, CrabStatus

class CrabClient:
    def __init__(self, command = None, id = None):
        self.command = command
        self.id = id
        self.conn = None

    def start(self):
        self.write_json(self.get_url("start"),
                {"command": self.command})

    def finish(self, status = CrabStatus.UNKNOWN,
            stdoutdata = "", stderrdata = ""):
        self.write_json(self.get_url("finish"),
                {"command": self.command,
                "status":   status,
                "stdout":   stdoutdata,
                "stderr":   stderrdata})

    def fail(self, status = CrabStatus.FAIL, message = ""):
        self.finish(status, stderrdata = message)

    def send_crontab(self, crontab, timezone = None):
        self.write_json(self.get_url("crontab"),
                {"crontab": crontab.split("\n"),
                "timezone": timezone})

    def fetch_crontab(self):
        data = self.read_json(self.get_url("crontab"))
        return "\n".join(data["crontab"])

    def get_host(self):
        return socket.getfqdn()

    def get_user(self):
        return os.getlogin()

    def get_url(self, action):
        url = "/api/0/" + action \
            + "/" + self.get_host() \
            + "/" + self.get_user()

        if self.id != None:
            url = url + "/" + self.id

        return url

    def get_conn(self):
        if self.conn == None:
            self.conn = HTTPConnection("localhost", 8000)

        return self.conn

    def read_json(self, url):
        try:
            conn = self.get_conn()
            conn.request("GET", url)

            res = conn.getresponse()
            if res.status != 200:
                raise CrabError("server error : " + res.reason)

            return json.load(res)

        except HTTPException as err:
            raise CrabError("HTTP error : " + str(err))

        except socket.error as err:
            raise CrabError("socket error : " + str(err))

        except ValueError as err:
            raise CrabError("did not understand response : " + str(err))

    def write_json(self, url, obj):
        try:
            conn = self.get_conn()
            conn.request("PUT", url, json.dumps(obj))

            res = conn.getresponse()

            if res.status != 200:
                raise CrabError("server error : " + res.reason)

        except HTTPException as err:
            raise CrabError("HTTP error : " + str(err))

        except socket.error as err:
            raise CrabError("socket error : " + str(err))

