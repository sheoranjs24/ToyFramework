import logging, getopt, sys
from spyne.application import Application
from spyne.protocol.json import JsonDocument
from spyne.protocol.soap import Soap11
from spyne.protocol.http import HttpRpc
from spyne.server.wsgi import WsgiApplication
from spyne.util.simple import wsgi_soap_application
from wsgiref.simple_server import make_server

from replica import Replica

def main(argv):
    # logging
    logging.basicConfig(level=logging.INFO)
    logging.getLogger('spyne.protocol.json').setLevel(logging.INFO)
        
    # command-line arguments
    hostname = '127.0.0.1'  
    port = 7789
    try:
       opts, args = getopt.getopt(argv,"hH:P:",["host=","port="])
    except getopt.GetoptError:
        print './server.py -H <hostname> -P <port>'
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print './server.py -H <hostname> -P <port>'
            sys.exit()
        elif opt in ("-H", "--host"):
            hostname = arg
        elif opt in ("-P", "--port"):
            port = arg
    
    application = Application([Replica], 'spyne.TM.replica.json',
                                in_protocol=Soap11(), out_protocol=Soap11())
    wsgi_app = WsgiApplication(application)
    
    # Register the WSGI application as handler to wsgi server & run http server
    server = make_server(hostname, port, wsgi_app)

    print("listening to http://%s:%s" % (hostname, port))
    print("wsdl is at: http://%s:%s/?wsdl" % (hostname, port))
    
    server.serve_forever()
    
if __name__=="__main__":
    main(sys.argv[1:])