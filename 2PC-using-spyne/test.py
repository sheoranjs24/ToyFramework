import logging, sys, getopt
from suds.client import Client
from suds.cache import NoCache

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(level)s: %(message)s')

def main(argv):
    
    # Command-line arguments
    port = 7789
    serverFile = None
    try:
       opts, args = getopt.getopt(argv,"hP:F:",["port=", "serverFile="])
    except getopt.GetoptError:
        print './test.py -P <port> -F <serverFile>'
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print './test.py -P <port> -F <serverFile>'
            sys.exit()
        elif opt in ("-P", "--port"):
            port = arg
        elif opt in ("-U", "--serverFile="):
            serverFile = arg
    
    #Read server address file and append to list
    if serverFile is none:
        logging.error('No server or client name provided.')
        sys.exit(1)
    sfile = None 
    try:
        sfile = open(serverFile, 'r')
    except:
        logging.error("error while trying to open the file.")
        sys.exit(1)
    
    servers = []
    for line in sfile:
        uri = 'http://' + line + ':' + port + '/?wsdl'  #'http://hostname:7789/?wsdl' 
        servers.append(uri)
    
    #Create clients
    clients = []
    logging.info("Testing single client with single server...")
    clients[0] = Client(servers[0], cache=NoCache(), timeout=60)
    logging.info("Get value for key 1: result: %s", clients[0].service.get('1'))
    
    logging.info("Put key 1: result: %s", clients[0].service.put('1', 'one'))
    logging.info("Put key 2: result: %s", clients[0].service.put('2', 'two'))
    logging.info("Put key 3: result: %s", clients[0].service.put('3', 'three'))
    logging.info("Get value for key 1: result: %s", clients[0].service.get('1'))
    logging.info("Get value for key 3: result: %s", clients[0].service.get('3'))
    
    logging.info("Put key 1: result: %s", clients[0].service.put('1', 'One'))
    logging.info("Get value for key 1: result: %s", clients[0].service.get('1'))
    
    logging.info("Delete key 1: result: %s", clients[0].service.delete('1'))
    logging.info("Get value for key 1: result: %s", clients[0].service.get('1'))
    
    # Test with two clients connected to single server.
    logging.info("Testing two clients with single server...")
    clients[1] = Client(servers[0], cache=NoCache(), timeout=60)
    logging.info("Get value for key 2: result: %s", clients[1].service.get('2'))
    
    logging.info("Put key 4: result: %s", clients[1].service.put('4', 'Four'))
    logging.info("Put key 5: result: %s", clients[0].service.put('5', 'Five'))
    logging.info("Get value for key 5: result: %s", clients[1].service.get('5'))
    logging.info("Get value for key 4: result: %s", clients[1].service.get('4'))
    logging.info("Get value for key 4: result: %s", clients[0].service.get('4'))
    
    logging.info("Delete key 2: result: %s", clients[0].service.delete('2'))
    logging.info("Delete key 3: result: %s", clients[1].service.delete('3'))
    logging.info("Get value for key 3: result: %s", clients[0].service.get('3'))
    logging.info("Get value for key 2: result: %s", clients[0].service.get('2'))
    logging.info("Get value for key 2: result: %s", clients[1].service.get('2'))
    
    #Test connections b/w servers, bandwidth
    

if __name__ == "__main__":
    main(sys.argv[1:])