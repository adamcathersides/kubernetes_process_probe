#!/usr/bin/env python

import SimpleHTTPServer
import socket
import SocketServer
import subprocess as sp
import time
import sys
import argparse
import threading
import os

#Setup args
parser = argparse.ArgumentParser(description='Kubernetes readiness/liveness probe')
parser.add_argument('probe', type=str, help='The probe type', choices=["http", "tcp"])
parser.add_argument('port', type=int, help='The listening port')
parser.add_argument('command', type=str, nargs='*', help='The command to run')
args, unknown = parser.parse_known_args()
command = args.command + unknown


class WebServer:

    def __init__(self, port):
        os.chdir("page")
        SocketServer.TCPServer.allow_reuse_address = True
        self.port = port
        self.handler = SimpleHTTPServer.SimpleHTTPRequestHandler
        self.httpd = SocketServer.TCPServer(('', self.port), self.handler)

    def start_web_server(self):
        try:
            print "Opening webserver on port {}".format(args.port)
            self.httpd.serve_forever()
        except Exception as exc:
            print "Error opening probe webserver: {}".format(exc)
            sys.exit(1)


    def stop_web_server(self):
        self.httpd.shutdown()
        self.httpd.server_close()


class TcpSocket:

    def __init__(self, port):
        self.port = port
        self.serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.serversocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def open_tcp_socket(self):

        try:
            print "Opening tcp listening socket on port {}".format(args.port)
            self.serversocket.bind(('', self.port))
            self.serversocket.listen(1)
        except socket.error, exc:
            print "Error opening probe socket: {}".format(exc)
            sys.exit(1)


    def close_tcp_socket(self):

        self.serversocket.shutdown(socket.SHUT_RDWR)
        self.serversocket.close()


# Run process
srt_proc = sp.Popen(command, stdout=sp.PIPE, stderr=sp.PIPE)

proc_returncode = srt_proc.poll()

# Run probe
if proc_returncode is None:

    if args.probe == "tcp":
        tcp_socket = TcpSocket(args.port)
        tcp_socket.open_tcp_socket()

    if args.probe == "http":
        web_server = WebServer(args.port)
        thread = threading.Thread(target=web_server.start_web_server)
        thread.start()

# Keep checking process and close probe if necessary
while True:

    time.sleep(1)
    proc_returncode = srt_proc.poll()

    if proc_returncode is not None:

        print "{} appears to have stopped.\nClosing {} probe".format(command[0], args.probe)
        if args.probe == "tcp":
            tcp_socket.close_tcp_socket()
            break
        if args.probe == "http":
            web_server.stop_web_server()
            break

sys.exit(0)
