import logging, getopt, sys
from twisted.python import log
from twisted.internet import reactor
from twisted.web.server import Site
from twisted.web.wsgi import WSGIResource
from spyne.server.twisted import TwistedWebResource
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
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s: %(message)s')
    logging.getLogger('server').setLevel(logging.INFO)
        
    # command-line arguments
    hostname = '127.0.0.1' 
    port = 7788
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
            if isinstance(arg, str):
                port = int(arg)
            elif isinstance(arg, int):
                port = arg
            else:
                port = arg
    
    # Initialize the application
    observer = log.PythonLoggingObserver('twisted')
    log.startLoggingWithObserver(observer.emit, setStdout=False)

    application = Application([Replica], 'spyne.datastore.replica',
                                in_protocol=Soap11(), out_protocol=Soap11())
    #wsgi_app = WsgiApplication(application)
    
    # Register the WSGI application as handler to wsgi server & run http server
    #resource = WSGIResource(reactor, reactor, wsgi_app)
    resource = TwistedWebResource(application)
    site = Site(resource)
    
    reactor.listenTCP(port, site, interface=hostname)

    logging.info('listening on: %s:%d' % (hostname,port))
    logging.info('wsdl is at: http://%s:%d/?wsdl' % (hostname, port))

    sys.exit(reactor.run())
    #server = make_server(hostname, port, wsgi_app)   
    #server.serve_forever()
    
if __name__=="__main__":
    main(sys.argv[1:])