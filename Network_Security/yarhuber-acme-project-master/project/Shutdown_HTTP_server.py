from flask import Flask, Response, request
from threading import Thread

port = 5003
shutdown_server = Flask(__name__)


@shutdown_server.route("/shutdown")  # type: ignore
def shutdown():
    func = request.environ.get("werkzeug.server.shutdown")
    if func is not None:
        func()
    
def start_shutdown_server(record):
    server_thread = Thread(target=run_server, args=(record,))
    server_thread.start()

def run_server(record):
    shutdown_server.run(host=record, port=port, debug=False, threaded=True)