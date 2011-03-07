# -*- coding: utf-8 -*-
import BaseHTTPServer
import threading


WP_MENU = '''
<div class="menu">
 <ul>
  <li><a href="#">wp-nav-1</a></li>
  <li><a href="#">wp-nav-2</a></li>
 </ul>
</div>
'''

WP_CONTENT = '''
<html>
<head>
<title>wordpress-title</title>
</head>
<body>
%s
<div id="content">
 Wobsnasm
</div>
</body>
</html>
''' % WP_MENU

WP_ERROR = '''
<html>
<body id="error-page">
%s
 <div>whoopsy</div>
</body>
</html>
''' % WP_MENU

WP_EMPTY = '''
<html>
<body>
%s
</body>
</html>
''' % WP_MENU

WP_UTF8 = '''
<html>
<title>Thorn</title>
<body>
%s
<div id="content">
þ
</div>
</body>
</html>
''' % WP_MENU


class MockHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    def do_GET(self):
        if "about" in self.path:
            self.send_response(404)
            self.end_headers()
            content = WP_CONTENT
        elif "license" in self.path:
            self.send_response(500)
            self.end_headers()
            content = "someerror"
        elif "exists_in_wordpress" in self.path:
            self.send_response(200)
            self.end_headers()
            content = WP_CONTENT
        elif "error_in_wordpress" in self.path:
            self.send_response(500)
            self.end_headers()
            content = WP_ERROR
        elif "utf8_in_wordpress" in self.path:
            self.send_response(200)
            self.end_headers()
            content = WP_UTF8
        elif "404" in self.path:
            self.send_response(404)
            self.end_headers()
            content = "blah"
        elif "redirect" in self.path:
            self.send_response(301)
            self.send_header('Location',
                             'http://localhost:6969/exists_in_wordpress')
            self.end_headers()
            content = ""
        elif "notmodified" in self.path:
            self.send_response(304)
            self.end_headers()
            content = ""
        else:
            self.send_response(200)
            self.end_headers()
            content = "empty"
        self.wfile.write(content)

    def do_POST(self):
        return self.do_GET()

    def do_HEAD(self):
        self.send_response(200)
        content = ""
        self.end_headers()
        self.wfile.write(content)

    def do_QUIT(self):
        self.send_response(200)
        self.end_headers()
        self.server.stop = True


class ReusableServer(BaseHTTPServer.HTTPServer):
    allow_reuse_address = 1

    def serve_til_quit(self):
        self.stop = False
        while not self.stop:
            self.handle_request()


def runmockserver():
    server_address = ('localhost', 6969)
    httpd = ReusableServer(server_address,
                           MockHandler)
    httpd_thread = threading.Thread(target=httpd.serve_til_quit)
    httpd_thread.setDaemon(True)
    httpd_thread.start()
    return httpd_thread
