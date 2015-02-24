import logging
from suds.client import Client

import transaction
import datastore

def main(uri):
    # logging
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger('client').setLevel(logging.DEBUG)
    
    userA = Client(uri)
    
    print userA.get_value('key1')


if __name__ == "__main__":
    uri = 'http://localhost:7789/?wsdl'  #TODO: command-line-argument
    main(uri)