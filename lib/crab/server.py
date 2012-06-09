from BaseHTTPServer import BaseHTTPRequestHandler
import json
import socket
import urllib

from crab import CrabError, CrabStatus

class CrabServer(BaseHTTPRequestHandler):
    @staticmethod
    def initialize():
        pass

    def do_GET(self):
        self.split_path()

        if self.command == None:
            self.send_error(404, "no command specified")
        elif self.command == "crontab":
            if None in (self.host, self.user):
                self.send_error(500, "host or user not specified")
            else:
                try:
                    crontab = self.store.get_crontab(self.host, self.user)
                    self.write_json({"crontab": crontab})
                except CrabError as err:
                    self.send_error(500, "read error : " + str(err))
        else:
            self.send_error(404, "unknown request")

    def do_PUT(self):
        self.split_path()

        if self.command == None:
            self.send_error(404, "no command specified")

        elif None in (self.host, self.user):
            self.send_error(500, "host or user not specified")
            return

        elif self.command == "start":
            try:
                data = self.read_json()
                command = data.get("command")

                if command == None:
                    raise CrabError("cron command not specified")

                self.store.log_start(self.host, self.user, self.id, command)
                self.send_response(200)

            except ValueError as err:
                self.send_error(500, "did not understand request")
            except CrabError as err:
                self.send_error(500, "log error : " + str(err))

        elif self.command == "finish":
            try:
                data = self.read_json()
                command = data.get("command")
                status  = data.get("status")

                if None in (command, status):
                    raise CrabError("insufficient information to log finish")

                if status not in CrabStatus.VALUES:
                    raise CrabError("invalid finish status")

                self.store.log_finish(self.host, self.user, self.id, command,
                        status, data.get("stdout"), data.get("stderr"))

                self.send_response(200)

            except ValueError as err:
                self.send_error(500, "did not understand request")
            except CrabError as err:
                self.send_error(500, "log error : " + str(err))

        elif self.command == "crontab":
            try:
                data = self.read_json()
                crontab = data.get("crontab")

                if crontab == None:
                    raise CrabError("no crontab received")

                self.store.save_crontab(self.host, self.user,
                        crontab, timezone = data.get("timezone"))
                self.send_response(200)

            except ValueError as err:
                self.send_error(500, "did not understand request")
            except CrabError as err:
                self.send_error(500, "write error : " + str(err))

        else:
            self.send_error(404, "unknown request")

    def split_path(self):
        path = urllib.unquote(self.path).split("/")[3:]
        self.command = self.host = self.user = self.id = None
        try:
            self.command = path[0]
            self.host = path[1]
            self.user = path[2]
            self.id = path[3]
        except IndexError:
            pass

#    def get_host(self):
#        (host, port) = self.client_address
#        try:
#            (hostname, alias, ipaddrlist) = socket.gethostbyaddr(host)
#            return hostname
#        except socket.herror:
#            return host

    def read_json(self):
        length = int(self.headers.getheader('content-length'))
        return json.loads(self.rfile.read(length))

    def write_json(self, obj):
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        json.dump(obj , self.wfile)

