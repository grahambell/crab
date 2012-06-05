from BaseHTTPServer import BaseHTTPRequestHandler
import json
import socket

class CrabServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.split_path()

        if self.command == None:
            self.send_response(404, "no command specified")
        elif self.command == "crontab":
            self.write_json({"crontab": ["* * * * * some command",
                "* * * * * another command"]})
        else:
            self.send_response(404, "unknown request")

    def do_PUT(self):
        self.split_path()

        if self.command == None:
            self.send_response(404, "no command specified")
        elif self.command == "start":
            try:
                data = self.read_json()
                print "start:", data, "from:", self.get_host()
                print "host:", self.host, "user:", self.user, "id:", self.id
                self.send_response(200)
            except ValueError as err:
                self.send_response(500, "did not understand request")

        elif self.command == "finish":
            try:
                data = self.read_json()
                print "finish:", data, "from:", self.get_host()
                self.send_response(200)
            except ValueError as err:
                self.send_response(500, "did not understand request")

        elif self.command == "crontab":
            try:
                data = self.read_json()
                print "received:", data, "from:", self.get_host()
                self.send_response(200)
            except ValueError as err:
                self.send_response(500, "did not understand request")
        else:
            self.send_response(404, "unknown request")

    def split_path(self):
        path = self.path.split("/")[2:]
        self.command = self.host = self.user = self.id = None
        try:
            self.command = path[0]
            self.host = path[1]
            self.user = path[2]
            self.id = path[3]
        except IndexError:
            pass

    def get_host(self):
        (host, port) = self.client_address
        try:
            (hostname, alias, ipaddrlist) = socket.gethostbyaddr(host)
            return hostname
        except socket.herror:
            return host

    def read_json(self):
        length = int(self.headers.getheader('content-length'))
        return json.loads(self.rfile.read(length))

    def write_json(self, obj):
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        json.dump(obj , self.wfile)


