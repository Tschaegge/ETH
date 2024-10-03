from dns_server import Dns_Server
dns = Dns_Server('','')
dns.start_server() 
print('success')
dns.stop_server()