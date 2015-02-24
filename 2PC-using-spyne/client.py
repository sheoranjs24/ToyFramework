import logging, sys, getopt
from suds.client import Client
from spyne.client.http import HttpClient

def main(argv):
    # logging
    logging.basicConfig(level=logging.INFO)
    logging.getLogger('client').setLevel(logging.INFO)
    
    # command-line arguments
    uri_file = ['http://localhost:7788/?wsdl', 'http://localhost:7789/?wsdl']
    uriFilePath = None
    try:
       opts, args = getopt.getopt(argv,"hU:",["uri_file="])
    except getopt.GetoptError:
        print './server.py -U <uri_file>'
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print './server.py -U <uri_file>'
            sys.exit()
        elif opt in ("-U", "--uri_file"):
            uriFilePath = arg
    
    # load URIs
    if uriFilePath is not None:
        try:
            uri_file = open(uriFilePath, 'r')
        except IOError:
            print 'unable to open URI file'
            uri_file = ['http://localhost:7788/?wsdl', 'http://localhost:7789/?wsdl'] #TODO: remove this line
            
    # Create one client for each replica of server
    clients = []
    uriList = []
    for uri in uri_file:
        uriList.append(uri)
        clients.append(Client(uri))
    
    #print "client: ", clients[0], dir(clients[0])
    # Add server and replica info
    print "Adding replicas", len(uriList)
    counter=-1
    while (counter < len(uriList)-1):
        counter = counter + 1
        address = uriList[counter]
        print "address: ", address
        clients[counter].service.set_server(address)
        for uri in uriList:
            if uri.find(address) == -1:
                print "replica: ", uri
                clients[counter].service.add_replica(address)
    
    print "starting queries..."
    print clients[0].service.get('key1')
    print clients[0].service.put('key1', 'foo')
    print clients[0].service.get('key1')
    print clients[0].service.delete('key1')
    print clients[0].service.get('key1')


if __name__ == "__main__": 
    main(sys.argv[1:])
