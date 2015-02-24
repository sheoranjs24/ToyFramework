import logging
from spyne.application import Application
from spyne.protocol.json import JsonDocument
from spyne.protocol.http import HttpRpc
from spyne.server.wsgi import WsgiApplication
from wsgiref.simple_server import make_server

from transaction import TransactionManager

def main():
    # logging
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger('spyne.protocol.json').setLevel(logging.DEBUG)
    
    application = Application([TransactionManager], 'spyne.TM.replica.json',
                                in_protocol=JsonDocument(), out_protocol=JsonDocument())
    
    wsgi_app = WsgiApplication(application)
    
    # Register the WSGI application as handler to wsgi server & run http server
    server = make_server('127.0.0.1', 7789, wsgi_app)

    print "listening to http://127.0.0.1:7789"
    print "wsdl is at: http://localhost:7789/?wsdl"
    
    server.serve_forever()
    


if __name__=="__main__":
    main()