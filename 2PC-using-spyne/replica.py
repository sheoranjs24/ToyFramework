import logging
from spyne.decorator import srpc, rpc
from spyne.service import ServiceBase
from spyne.model.complex import Iterable
from spyne.model import  Integer, String, Boolean

from transaction import TransactionManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Replica(ServiceBase):
    
    transaction_manager = TransactionManager()
    
    @rpc(String)
    def set_server(ctx, server):
        logger.info('Replica: set_server()')
        Replica.transaction_manager.set_server(server)
    
    @rpc(String)
    def add_replica(ctx, replica):
        logger.info('Replica: add_replica()')
        Replica.transaction_manager.add_replica(replica)
    
    @srpc(String, _returns=Boolean)    
    def tpc_vote_replica(msg):
        logger.info('Replica: tpc_vote_replica()')
        return Replica.transaction_manager.tpc_vote_replica(msg)
    
    @rpc(String)
    def tpc_commit_replica(ctx, msg):
        logger.info('Replica: tpc_commit_replica()')
        return Replica.transaction_manager.tpc_commit_replica(msg)
    
    @rpc(String)
    def tpc_abort_replica(ctx, msg):
        logger.info('Replica: tpc_abort_replica()')
        return Replica.transaction_manager.tpc_abort_replica(msg)

    @rpc(String)
    def tpc_ack(ctx, msg):
        logger.info('Replica: tpc_ack()')
        return Replica.transaction_manager.tpc_ack(msg)

    @srpc(String, String, _returns=Boolean)
    def put(key, value):
        logger.info('Replica: put()')
        return Replica.transaction_manager.put(key, value)

    @srpc(String, _returns=Boolean)      
    def delete(key):
        logger.info('Replica: delete()')
        return Replica.transaction_manager.delete(key)

    @srpc(String, _returns=String)
    def get(key):
        logger.info('Replica: get()')
        return Replica.transaction_manager.get(key)
    
    @srpc(String, _returns=String)
    def get_value_replica(key):
        logger.info('Replica: get_value_replica()')
        return Replica.transaction_manager.get_value_replica(key)