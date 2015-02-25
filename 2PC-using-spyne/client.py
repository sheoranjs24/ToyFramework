import logging, sys, getopt, json, urllib2
from suds.client import Client
from suds.sax.element import Element
from suds.cache import NoCache
from spyne.client.http import HttpClient
from twisted.web import client
#from spyne.client.twisted import 

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(level)s: %(message)s')
#logging.getLogger(__name__).setLevel(logging.INFO)

def main(argv):
    # logging
    #logging = logging.getlogging('client').setLevel(logging.DEBUG)
    
    # command-line arguments
    uri_file = ['http://127.0.0.1:7788/?wsdl', 'http://127.0.0.1:7789/?wsdl']
    uriFilePath = None
    try:
       opts, args = getopt.getopt(argv,"hU:",["uri_file="])
    except getopt.GetoptError:
        print './client.py -U <uri_file>'
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print './client.py -U <uri_file>'
            sys.exit()
        elif opt in ("-U", "--uri_file"):
            uriFilePath = arg
    
    # load URIs
    if uriFilePath is not None:
        try:
            uri_file = open(uriFilePath, 'r')
        except IOError:
            logging.error('unable to open URI file')
            uri_file = ['http://127.0.0.1:7788/?wsdl', 'http://127.0.0.1:7789/?wsdl'] #TODO: remove this line     
    
    # Create one client for each replica of server
    clients = []
    uriList = []
    counter =  -1
    for uri in uri_file:
        counter += 1
        uriList.append(uri)
        #c = Client('file://' + uri, nosend=True, autoblend=True, cache=NoCache())
        c = Client(uri, cache=NoCache(), timeout=120)
        clients.append(c)
        
    
    #print "client: ", clients[0], dir(clients[0])
    # Add server and replica info
    logging.debug('Adding replicas %d', len(uriList))
    counter=-1
    while (counter < len(uriList)-1):
        logging.debug('counter: %d', counter)
        counter = counter + 1
        # set server
        logging.debug('server: %s', uriList[counter])
        clients[counter].service.set_server(uriList[counter])
        #context = clients[counter].service.set_server(uriList[counter])
        #d = client.getPage(url=context.client.location(), postdata=str(context.envelope), 
        #                   method='POST', headers=context.client.headers())
        
        # Add replicas
        for uri in uriList:
            if uri.find(uriList[counter]) == -1:
                logging.debug('replica: %s', uri)
                clients[counter].service.add_replica(uri)
        
        
    logging.debug('starting queries...')
    print clients[0].service.get('key1')
    #context = clients[0].service.put('key1', 'fee')
    #d = client.getPage(url=context.client.location(), postdata=str(context.envelope), 
    #                   method='POST', headers=context.client.headers())
    #print "success"
    print clients[0].service.put('key1', 'foo')
    print clients[0].service.get('key1')
    print clients[0].service.delete('key1')
    print clients[0].service.get('key1')


if __name__ == "__main__": 
    main(sys.argv[1:])
