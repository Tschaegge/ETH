from flask import Flask, Response, jsonify
from threading import Thread


class http_server:
    port = 5002

    def __init__(self, tokens):
        self.http_server = Flask(__name__)
        self.tokens = tokens
        print(self.tokens)

        @self.http_server.route("/.well-known/acme-challenge/<string:token>")
        def reply(token):
            return Response(self.tokens[token], content_type="application/octet-stream")

        @self.http_server.route("/")
        def main():
            return jsonify(self.tokens)

    def start_http_server(self, record):
        server_thread = Thread(target=self.run_server, args=(record,))
        server_thread.start()

    def run_server(self, record):
        self.http_server.run(host=record, port=self.port, debug=False, threaded=True)
