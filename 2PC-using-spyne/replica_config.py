import logging, sys, getopt
from suds.client import Client
from suds.cache import NoCache

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s: %(message)s')

def main(argv):
    
    #Command line arguments
    serverFile = None
    try:
       opts, args = getopt.getopt(argv,"hF:",["serverFile="])
    except getopt.GetoptError:
        print './replica_config.py -F <serverFile>'
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print './replica_config.py -F <serverFile>'
            sys.exit()
        elif opt in ("-F", "--serverFile="):
            serverFile = arg
    
    #Read server address file and append to list
    if serverFile is None:
        logging.error("serverFile is needed to add replicas.")
        sys.exit(1)
    sfile = None
    try:
        sfile = open(serverFile, 'r')
    except:
        logging.error("error while trying to open the serverFile")
        sys.exit(1)
    
    servers = []
    for line in sfile:
        addr = line.strip('\n').split(' ')
        uri = 'http://' + addr[0] + ':' + addr[1] + '/?wsdl'  #'http://localhost:7789/?wsdl' 
        logging.info("replica uri: %s", uri)
        servers.append(uri)
    
    #Create a client & add replica to each server
    logging.info("Establishing connection with servers...")
    for server in servers:
        client = Client(uri, cache=NoCache(), timeout=120)
        client.service.set_server(server)
        # Add replicas
        for replica in servers:
            if replica.find(server) == -1:
                client.service.add_replica(replica)
    logging.info("Connections b/w servers is setup.")
    sys.exit(0)

if __name__ == "__main__":
    main(sys.argv[1:])