"""
    Transaction Manager for Two Phase Commit (2PC)
"""

import service, api

class TransactionManager(object):
    
    def __init__(self, log_path='distributed_transaction.log'):
        self._txn = None
        self.server = None
        self._replicas = []
        self._prevTransactionIndex = None
        self.currTransactionIndex = None
        
        # log records: trx_id, start, resources, commit_decisions
        try:
            self.log_file = open(self.log_path, "r")
            # TODO: Go to the last line to record transaction index
        except IOError:
            print("log file did not exist and hence it will be created")
            self.log_file = open (self.log_path, "w+")
    
    def set_server(self, server):
        self.server = server
    
    def begin_transaction(self):
        # If there is a transaction in progress, abort the new transaction
        if self._txn is not None:
            return -1
        self.currTransactionIndex = prevTransactionIndex+1
        self._txn = Transaction(self)
        return self.currTransactionIndex
    
    def get_transaction(self):
        if self._txn is None:
            self._txn = Transaction(self)
        return self._txn
    
    def free(self, txn):
        if txn is not self._txn:
            raise ValueError("Unknown transaction")
        self._txn = None
    
    def commit(self, data):
        self.get_transaction().commit(data)
        
    def rollback(self):
        self.get_transaction().rollback()
    
    def register(self):
        """ register a resource manager """
    