import argparse
from inspect import Arguments
import certificate_HTTPS_server
import os
import Shutdown_HTTP_server

from click import argument  # python standard library

from acmeClient import acme_client


def main():
    #  we use an argument parser as described in https://docs.python.org/3/library/argparse.html
    parser = argparse.ArgumentParser()
    parser.add_argument("type", choices=["dns01", "http01"])
    parser.add_argument(
        "--dir",
        required=True,
        help="DIR_URL is the directory URL of the ACME server that should be used",
    )
    parser.add_argument(
        "--record",
        required=True,
        help="IPv4_ADDRESS is the IPv4 address which must be returned by your DNS server for all A-record queries.",
    )
    parser.add_argument(
        "--domain",
        required=True,
        action="append",
        help="DOMAIN is the domain for which to request the certificate. If multiple - -domain flags are present, a single certificate for multiple domains should be requested. Wildcard domains have no special flag and are simply denoted by, e.g., *.example.net.",
    )
    parser.add_argument(
        "--revoke",
        required=False,
        action="store_true",
        help="If present, your application should immediately revoke the certificate after obtaining it. In both cases, your application should start its HTTPS server and set it up to use the newly obtained certificate.",
    )
    arguments = parser.parse_args()

    client = acme_client(arguments.dir)
    client.populateUrls()
    client.create_account()
    client.submit_order(arguments.domain)
    client.get_challenge(arguments.type)
    client.execute_challenge(arguments.type, arguments.record)
    client.finalization()
    client.download_certificate()
    certificate_server = certificate_HTTPS_server.certificate_server()
    certificate_server.start_http_server(
        os.path.realpath("cert.pem"), os.path.realpath("key.pem"), arguments.record
    )
    #Shutdown_HTTP_server.start_shutdown_server(arguments.record)

    if arguments.revoke:
        client.revoke()
    client.Dns_Test(arguments.record)


if __name__ == "__main__":
    main()
