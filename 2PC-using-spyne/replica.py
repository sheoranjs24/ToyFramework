import logging
from spyne.decorator import srpc, rpc
from spyne.service import ServiceBase
from spyne.model.complex import Iterable
from spyne.model import  Integer, String, Boolean

from transaction import TransactionManager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s: %(message)s')
#logging.getLogger(__name__).setLevel(logging.INFO)

class Replica(ServiceBase):
    
    transaction_manager = TransactionManager()

    @rpc(String)
    def set_server(ctx, server):
        logging.info(' set_server()')
        Replica.transaction_manager.set_server(server)

    @rpc(String)
    def add_replica(ctx, replica):
        logging.info(' add_replica()')
        Replica.transaction_manager.add_replica(replica)

    @srpc(String, _returns=Boolean)    
    def tpc_vote_replica(msg):
        logging.info(' tpc_vote_replica()')
        return Replica.transaction_manager.tpc_vote_replica(msg)

    @srpc(String, _returns=Boolean)
    def tpc_commit_replica(msg,):
        logging.info(' tpc_commit_replica()')
        return Replica.transaction_manager.tpc_commit_replica(msg)

    @srpc(String, _returns=Boolean)
    def tpc_abort_replica(msg):
        logging.info(' tpc_abort_replica()')
        return Replica.transaction_manager.tpc_abort_replica(msg)
    
    @rpc(String)
    def tpc_ack(ctx, msg):
        logging.info(' tpc_ack()')
        Replica.transaction_manager.tpc_ack(msg)

    @rpc(String, String)
    def put(ctx, key, value):
        logging.info(' put()')
        return Replica.transaction_manager.put(key, value)

    @srpc(String, _returns=Boolean)      
    def delete(key):
        logging.info(' delete()')
        return Replica.transaction_manager.delete(key)

    @srpc(String, _returns=String)
    def get(key):
        logging.info(' get()')
        return Replica.transaction_manager.get(key)
    
    @srpc(String, _returns=String)
    def get_value_replica(key):
        logging.info(' get_value_replica()')
        return Replica.transaction_manager.get_value_replica(key)