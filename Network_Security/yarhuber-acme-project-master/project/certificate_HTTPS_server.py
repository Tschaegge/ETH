from flask import Flask
from threading import Thread
class certificate_server:
    Port = 5001
    def __init__(self):
        self.certificate_server = Flask(__name__)
        @self.certificate_server.route("/") # type: ignore  
        def route_get(self):
            return "Look the certificate!"


    def start_http_server(self,certPath, keyPath, record):
        server_thread = Thread(target=self.run_server, args=(certPath, keyPath, record))
        server_thread.start()


    def run_server(self,certPath, keyPath, record):
        self.certificate_server.run(
        host=record,
        ssl_context=(certPath, keyPath),
        port=self.Port,
        debug=False,
        threaded=True,
    )
