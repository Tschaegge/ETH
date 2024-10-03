from dnslib.server import DNSServer, DNSLogger
from dnslib.zoneresolver import ZoneResolver


class Dns_Server:

    def __init__(self, zone, record):
        self.resolver = ZoneResolver(zone)
        self.logger = DNSLogger()
        print("config " + record+ ":10053")
        self.server = DNSServer(
            self.resolver, address=record, port=10053, tcp = False
        )

    def start_server(self):
        self.server.start_thread()

    def stop_server(self):
        # self.server.thread.join()
        self.server.server.server_close()

    def setZone(self, zone, record):
        self.stop_server()
        self.resolver = ZoneResolver(zone=zone)
        self.server = DNSServer(
            resolver=self.resolver, address=record, port=10053, tcp=False
        )
        self.start_server()

