
import json
import os
import logging

from spyne.decorator import srpc
from spyne.service import ServiceBase
from spyne.model.complex import Iterable, Integer, String, Boolean
from suds.client import Client

from log import Log
from datastore import DataStore
from __builtin__ import None

class TwoPhaseCommitMessage:
    VOTEREQ = "Vote Request"
    VOTEYES = "Vote Yes"  #Unused
    VOTENO = "Vote No"  #Unused
    COMMIT = "Commit"  
    ROLLBACK = "Rollback"
    ACKNOWLEDGEMENT = "Acknowledgement"
    
class DTLogMessage:
    START2PC = "Start 2PC"
    VOTEDYES = "Voted Yes"
    VOTEDNO = "Voted No"
    COMMIT = "Commit"
    ABORT = "Abort"

class TransactionManager(ServiceBase):
    
    def __init__(self, undo_log='undo.log', redo_log='redo.log', dt_log='distributed_transaction.log', 
                 server=None, replica_uri_list=None):
        self.server = server
        self._datastore = DataStore()
        self._prevTransactionIndex = None
        self.currTransactionIndex = None
        
        self._undoLog = Log(undo_log)
        self._redoLog = Log(redo_log)
        self._DTLog = Log(dt_log)
        
        # Create connection with replicas
        self._replicas = []
        #self._votes = {}
        if replica_uri is not None:
            for uri in replica_uri_list:
                if not uri.match(self.server):
                    self._replicas.append(Client(uri))
    
    def tpc_begin(self):
        # Create new transaction
        if self.currTransactionIndex is not None:
            return false
        else:
            print '\nNew Trx'
            if self._prevTransactionIndex is None:
                self.currTransactionIndex = 1
            else:
                self.currTransactionIndex = self._prevTransactionIndex + 1
            return success
    
    @srpc(String, _returns=Boolean)
    def tpc_vote_replica(self, msg):
        # Check if a trx is already in process
        if self.currTransactionIndex is not None \
            and self.currTransactionIndex != int(msg['operation'][0]):
            print '\nVOTE NO for msg:', msg
            DTEntry = [DTLogMessage.VOTEDNO, str(self.currTransactionIndex)]
            self._DTLog.write(DTEntry)
            return False
        
        # Check if trx if behind
        #TODO: Handle greater_than & less_than separately?
        if self._prevTransactionIndex+1 != int(msg['operation'][0]): 
            print '\ntrx is behind the coordinator', msg
            DTEntry = [DTLogMessage.VOTEDNO, str(self.currTransactionIndex)]
            self._DTLog.write(DTEntry)
            return False
        
        # Begin Trx
        status = self.tpc_begin()
        if not status:
            print '\nunable to begin trx'
            DTEntry = [DTLogMessage.VOTEDNO, str(self.currTransactionIndex)]
            self._DTLog.write(DTEntry)
            return False
        else:
            # Write entry into undo log
            undoEntry = msg['operation']
            self._undoLog.write(undoEntry)
            
            # Write to datastore
            if msg['operation'][1].match('put'):
                key = msg['operation'][2]
                value = msg['operation'][3]
                self._datastore.put_value(key, value) 
            elif msg['operation'][1].match('delete'):
                key = msg['operation'][2]
                self._datastore.delete_key(key)
            else:
                print '\noperation not found'
                DTEntry = [DTLogMessage.VOTEDNO, str(self.currTransactionIndex)]
                self._DTLog.write(DTEntry)
                return False
         
        # Write to DT log
        DTEntry = [DTLogMessage.VOTEDYES, str(self.currTransactionIndex)]
        self._DTLog.write(DTEntry)
        # Send Vote
        return True
        
                
    @srpc(String, _returns=Boolean)
    def tpc_commit_replica(self, msg):
        # Check trx id
        if self.currTransactionIndex is not None \
            and self.currTransactionIndex == int(msg['operation'][0]):   
            # Commit trx locally
            redoEntry = self._undoLog.peek()
            self._redoLog.write(redoEntry)
            self._datastore.commit()
            
            # Send COMMIT msg to replicas
            DTEntry = [DTLogMessage.COMMIT, str(self.currTransactionIndex)]
            self._DTLog.write(DTEntry)
            
            # Send ACK
            coordinator = Client(msg['Coordinator'])
            ack_msg = {}
            ack_msg['sender'] = self.server
            ack_msg['state'] = TwoPhaseCommitMessage.ACKNOWLEDGEMENT
            ack_msg['operation'] = redoEntry
            coordinator.tpc_ack(ack_msg)  
        else:
            print '\nWrong trx id in msg:', msg
            return False
        
    
    @srpc(String, _returns=Boolean)
    def tpc_abort_replica(self, msg):
        # Check trx id
        if self.currTransactionIndex is not None \
            and self.currTransactionIndex == int(msg['operation'][0]):   
            # Abort trx locally
            popedEntry = self._undoLog.peek()
            self._undoLog.pop()
            self._datastore.abort()
            
            # Send COMMIT msg to replicas
            DTEntry = [DTLogMessage.ABORT, str(self.currTransactionIndex)]
            self._DTLog.write(DTEntry)
            
            # Send ACK
            coordinator = Client(msg['Coordinator'])
            ack_msg = {}
            ack_msg['sender'] = self.server
            ack_msg['state'] = TwoPhaseCommitMessage.ACKNOWLEDGEMENT
            ack_msg['operation'] = popedEntry
            coordinator.tpc_ack(ack_msg)  
        else:
            print '\nWrong trx id in msg:', msg
            return False
    
    @srpc(String, _returns=String)
    def tpc_ack(self, msg):
        if int(msg['operation'][0]) == self.currTransactionIndex \
            and msg['sender'] not in self._acks:
            self._acks.append(msg['sender'])
            
            # check if all ACKs are received
            if len(self._acks) == len(self._replicas.keys()):
                tpc_finish()
            return 'Success'
        else:
            print '\nWrong trx_id or duplicate message. Message: ', msg
            return 'Error'
    
    def tpc_commit(self):
        # Commit trx locally
        redoEntry = self._undoLog.peek()
        self._redoLog.write(redoEntry)
        self._datastore.commit()
        
        # Send COMMIT msg to replicas
        DTEntry = [DTLogMessage.COMMIT, str(self.currTransactionIndex)]
        self._DTLog.write(DTEntry)
        
        msg = {}
        msg['coordinator'] = self.server
        msg['state'] = TwoPhaseCommitMessage.COMMIT
        msg['operation'] = redoEntry
        self._acks = []
        for replica in self._replicas:
            replica.tpc_commit_replica(msg)
    
    def tpc_abort(self):
        # Abort trx locally
        popedEntry = self._undoLog.peek()
        self._undoLog.pop()
        self._datastore.abort()
        
        # Send ROLLBACK msg to replicas
        DTEntry = [DTLogMessage.ABORT, str(self.currTransactionIndex)]
        self._DTLog.write(DTEntry)
        
        msg = {}
        msg['coordinator'] = self.server
        msg['state'] = TwoPhaseCommitMessage.ROLLBACK
        msg['operation'] = popedEntry
        self._acks = []
        for replica in self._replicas:
            replica.tpc_abort_replica(msg)
        
    def tpc_finish(self):
        # Close existing trx
        print 'close trx.'
        self._prevTransactionIndex = self.currTransactionIndex
        self.currTransactionIndex = None
    
    @srpc(String, _returns=Boolean)
    def put(self, key, value):
        # Commit Phase 1 
        # Perform Action locally
        status = self.tpc_begin()
        if not status:
            print '\nfailure. Another trx already in process.'
            return False
        else:
            # Write entry into undo log
            undoEntry = [str(self.currTransactionIndex), 'put', key, value]
            self._undoLog.write(undoEntry)
            self._datastore.put_value(key, value)
            
        # Send VOTEREQ message to replicas
        DTEntry = [DTLogMessage.START2PC, str(self.currTransactionIndex)]
        self._DTLog.write(DTEntry)
        
        msg = {}
        msg['coordinator'] = self.server
        msg['state'] = TwoPhaseCommitMessage.VOTEREQ
        msg['operation'] = undoEntry 
        #self._votes = {}
        for replica in self._replicas:
            if not replica.tpc_vote_replica(msg):
                print '\ngot VOTENO, hence aborting the trx.'
                self._datastore.abort()
                self._undoLog.pop()
                self.tpc_abort()
                return False
                
        # Commit Phase 2
        self.tpc_commit()
        print('\nAdded (%s, %s) to the data-store' % (key, value))
        return True
    
    @srpc(String, _returns=Boolean)      
    def delete(self, key):
        # Commit Phase 1 
        # Perform Action locally
        status = self.tpc_begin()
        if not status:
            print '\nfailure. Another trx already in process.'
            return False 
        else:
            # Write entry into undo log
            undoEntry = [str(self.currTransactionIndex), 'delete', key, value]
            self._undoLog.write(undoEntry)
            self._datastore.delete_key(key, value)
            
        # Send VOTEREQ message to replicas
        DTEntry = [DTLogMessage.START2PC, str(self.currTransactionIndex)]
        self._DTLog.write(DTEntry)
        
        msg = {}
        msg['coordinator'] = self.server
        msg['state'] = TwoPhaseCommitMessage.VOTEREQ
        msg['operation'] = undoEntry 
        #self._votes = {}
        for replica in self._replicas:
            if not replica.tpc_vote_replica(msg):
                print '\nG\got VOTENO, hence aborting the trx.'
                self._datastore.abort()
                self._undoLog.pop()
                self.tpc_abort()
                return False
                
        # Commit Phase 2
        self.tpc_commit()
        print('\nAdded (%s, %s) to the data-store' % (key, value))
        return True
    
    @srpc(String, _returns=String)
    def get(self, key):  
        localValue = self._datastore.get_value(key)
        replicaValue = None
        
        for replica in self._replicas:
            replicaValue = replica.get_value_replica(key)
            if replicaValue is not None \
                and localValue is not None \
                and replicaValue!=localValue:
                print 'Inconsistent values!'
                return None
        return localValue
    
    @srpc(String, _returns=String)
    def get_value_replica(self, key):
        return self._datastore.get_value(key)
        
        
    
     
        