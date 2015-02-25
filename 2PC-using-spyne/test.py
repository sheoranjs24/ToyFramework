import logging
from suds.client import Client

import transaction
import datastore

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(level)s: %(message)s')

def main(uri):

    userA = Client(uri)
    
    print userA.get_value('key1')


if __name__ == "__main__":
    uri = 'http://localhost:7789/?wsdl'  #TODO: command-line-argument
    main(uri)