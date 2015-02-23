"""
    Replication Manager: 
        Middleware between servers and clients
        Receives direct requests from the client and sends to server(s)
        
        Future: Handles load balancing
"""


import service, api
from dictionary import ResourceManager

class ReplicationManager(Object):
    
    def __init__(self, host=None, replicas=None):
        self.host = host
        self.replicas = replicas
    
    def set_host(self, host):
        self.host = host
    
    def add_replica(self, replica):
        if self.replica is not None:
            if type(replica) is list:
                self.replica = self.replica + replica
            else:
                self.replica.append(replica)
        else:
            self.replica = replica

    #TODO: send_message(), receive_message()

