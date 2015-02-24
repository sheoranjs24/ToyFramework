import logging
from suds.client import Client

import transaction
import datastore

def main(uri_list):
    # logging
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger('client').setLevel(logging.DEBUG)
    
    # Create one client for each replica of server
    clients = []
    for uri in uri_list:
        clients.append(Client(uri))
    
    print clients[0].get_value('key1')


if __name__ == "__main__":
    uri = ['http://localhost:7789/?wsdl']  #TODO: command-line-argument
    main(uri)