from frontend import app
import socket
import urllib2

from bottle import run
from multiprocessing import Process
from time import sleep

if __name__ == '__main__':
    while True:
        print "Starting frontend."
        p = Process(target=run, args = (app,), kwargs = {"host": "localhost", "port": 8080})
        p.start()

        
        while True:
            s = socket.socket()
            try:
                s.connect(("localhost", 8080))
                break
            except socket.error as msg:
                print "Server establishing..."
                sleep(5)
            finally:
                s.close()

        print "Server established."

        while True:
            try:
                s = urllib2.urlopen("http://localhost:8080/?test", timeout=30)
                s.close()
            except Exception as e:
                print(e)
                break

            sleep(5*60)
            
        p.terminate()
