from spyne.decorator import srpc
from spyne.service import ServiceBase
from spyne.model.complex import Iterable
from spyne.model import  Integer, String, Boolean

from transaction import TransactionManager

class Replica(ServiceBase):
    
    transaction_manager = TransactionManager()
    
    @srpc(String, _returns=Boolean)
    def set_server(server):
        return Replica.transaction_manager.set_server(server)
    
    @srpc(String, _returns=Boolean)
    def add_replica(replica):
        return Replica.transaction_manager.add_replica(replica)
    
    @srpc(String, _returns=Boolean)    
    def tpc_vote_replica(msg):
        return Replica.transaction_manager.tpc_vote_replica(msg)
    
    @srpc(String, _returns=Boolean)
    def tpc_commit_replica(msg):
        return Replica.transaction_manager.tpc_commit_replica(msg)
    
    @srpc(String, _returns=Boolean)
    def tpc_abort_replica(msg):
        return Replica.transaction_manager.tpc_abort_replica(msg)

    @srpc(String, _returns=String)
    def tpc_ack(msg):
        return Replica.transaction_manager.tpc_ack(msg)

    @srpc(String, String, _returns=Boolean)
    def put(key, value):
        return Replica.transaction_manager.put(key, value)

    @srpc(String, _returns=Boolean)      
    def delete(key):
        return Replica.transaction_manager.delete(key)

    @srpc(String, _returns=String)
    def get(key):
        return Replica.transaction_manager.get(key)
    
    @srpc(String, _returns=String)
    def get_value_replica(key):
        return Replica.transaction_manager.get_value_replica(key)