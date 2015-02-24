
import json
import os
import logging
from suds.client import Client
from suds.cache import NoCache
from spyne.client.http import HttpClient

from log import Log
from datastore import DataStore

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

class TransactionManager(object):
    
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
        self._replicaURIs = []
        #self._votes = {}
        if replica_uri_list is not None:
            for uri in replica_uri_list:
                if uri.find(self.server) == -1:
                    self._replicaURIs.append(uri)
                    self._replicas.append(Client(uri, cache=NoCache()))
    
    def set_server(self, server):
        logger.info('TM: set_server() called.')
        self.server = server
    
    def add_replica(self, replica_uri):
        logger.info('TM: add_replica() called.')
        if len(self._replicas)==0: 
            logger.debug('TM: replica added: %s', replica_uri)
            self._replicas = []
            self._replicaURIs = []
            self._replicaURIs.append(replica_uri)
            self._replicas.append(Client(replica_uri, cache=NoCache()))
        elif replica_uri not in self._replicaURIs:
            logger.debug('TM: replica added: %s', replica_uri)
            self._replicaURIs.append(replica_uri)
            self._replicas.append(replica_uri)
    
    def tpc_begin(self):
        # Create new transaction
        if self.currTransactionIndex is not None:
            return False
        else:
            logger.info('TM: new trx')
            if self._prevTransactionIndex is None:
                self.currTransactionIndex = 1
            else:
                self.currTransactionIndex = self._prevTransactionIndex + 1
            return True
    
    def tpc_vote_replica(self, msg):
        msg = eval(msg)
        logger.info('R: msg: %s', msg)
        # Check if a trx is already in process
        if self.currTransactionIndex is not None \
            and self.currTransactionIndex != int(msg['operation'][0]):
            logger.info('R: Another trx in process. Sending VOTE NO')
            DTEntry = [DTLogMessage.VOTEDNO, str(self.currTransactionIndex)]
            self._DTLog.write(DTEntry)
            return False
        
        # Check if trx if behind
        #TODO: Handle greater_than & less_than separately?
        if self._prevTransactionIndex is not None \
            and self._prevTransactionIndex+1 != int(msg['operation'][0]): 
            logger.info('R: trx is behind the coordinator. Sending VOTE NO')
            DTEntry = [DTLogMessage.VOTEDNO, str(self.currTransactionIndex)]
            self._DTLog.write(DTEntry)
            return False
        
        # Begin Trx
        status = self.tpc_begin()
        if status == False:
            logger.info('R: unable to begin trx. Sending VOTE NO')
            DTEntry = [DTLogMessage.VOTEDNO, str(self.currTransactionIndex)]
            self._DTLog.write(DTEntry)
            return False
        else:
            # Write entry into undo log
            undoEntry = msg['operation']
            self._undoLog.write(undoEntry)
            
            # Write to datastore
            if msg['operation'][1].find('put') == 0:
                key = msg['operation'][2]
                value = msg['operation'][3]
                self._datastore.put_value(key, value) 
            elif msg['operation'][1].find('delete') == 0:
                key = msg['operation'][2]
                self._datastore.delete_key(key)
            else:
                logger.info('R: operation not found. Sending VOTE NO')
                DTEntry = [DTLogMessage.VOTEDNO, str(self.currTransactionIndex)]
                self._DTLog.write(DTEntry)
                return False
         
        # Write to DT log
        DTEntry = [DTLogMessage.VOTEDYES, str(self.currTransactionIndex)]
        self._DTLog.write(DTEntry)
        # Send Vote
        return True
        
    def tpc_commit_replica(self, msg):
        msg = eval(msg)
        logger.info('R: msg: %s', msg)
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
            coordinator = Client(msg['coordinator'], cache=NoCache())
            ack_msg = {}
            ack_msg['sender'] = self.server
            ack_msg['state'] = TwoPhaseCommitMessage.ACKNOWLEDGEMENT
            ack_msg['operation'] = redoEntry
            coordinator.service.tpc_ack(str(ack_msg))  
        else:
            logger.info('R: Wrong trx id in msg:')
            return False
        
    def tpc_abort_replica(self, msg):
        msg = eval(msg)
        logger.info('R: msg: %s', msg)
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
            coordinator = Client(msg['coordinator'], cache=NoCache())
            ack_msg = {}
            ack_msg['sender'] = self.server
            ack_msg['state'] = TwoPhaseCommitMessage.ACKNOWLEDGEMENT
            ack_msg['operation'] = popedEntry
            coordinator.service.tpc_ack(str(ack_msg))  
        else:
            logger.info('R: Wrong trx id in msg.')
            return False

    def tpc_ack(self, msg):
        msg = eval(msg)
        logger.info('C: msg: %s', msg)
        if int(msg['operation'][0]) == self.currTransactionIndex \
            and msg['sender'] not in self._acks:
            self._acks.append(msg['sender'])
            
            # check if all ACKs are received
            if len(self._acks) == len(self._replicas):
                tpc_finish()
        else:
            logger.info('C: Wrong trx_id or duplicate message.')
    
    def tpc_commit(self):
        logger.info('C: tpc_commit()')
        # Commit trx locally
        redoEntry = self._undoLog.peek()
        self._redoLog.write(redoEntry)
        self._datastore.commit()
        
        # Send COMMIT msg to replicas
        DTEntry = [DTLogMessage.COMMIT, str(self.currTransactionIndex)]
        self._DTLog.write(DTEntry)
        
        msg = {}
        msg['coordinator'] = self.server
        msg['sender'] = self.server
        msg['state'] = TwoPhaseCommitMessage.COMMIT
        msg['operation'] = redoEntry
        self._acks = []
        logger.info('C: Sending COMMIT to replicas')
        for replica in self._replicas:
            replica.service.tpc_commit_replica(str(msg))
    
    def tpc_abort(self):
        logger.info('C: tpc_abort()')
        
        # Abort trx locally
        popedEntry = self._undoLog.peek()
        self._undoLog.pop()
        self._datastore.abort()
        
        # Send ROLLBACK msg to replicas
        DTEntry = [DTLogMessage.ABORT, str(self.currTransactionIndex)]
        self._DTLog.write(DTEntry)
        
        msg = {}
        msg['coordinator'] = self.server
        msg['sender'] = self.server
        msg['state'] = TwoPhaseCommitMessage.ROLLBACK
        msg['operation'] = popedEntry
        self._acks = []
        logger.info('C: sending ROLLBACK to replicas')
        for replica in self._replicas:
            replica.service.tpc_abort_replica(str(msg))
        
    def tpc_finish(self):
        # Close existing trx
        logger.info('C: tpc_finish()')
        self._prevTransactionIndex = self.currTransactionIndex
        self.currTransactionIndex = None
    
    def put(self, key, value):
        logger.info('C: put()')
        # Commit Phase 1 
        # Perform Action locally
        status = self.tpc_begin()
        if not status:
            logger.info('C:failure. Another trx already in process.')
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
        msg['sender'] = self.server
        msg['state'] = TwoPhaseCommitMessage.VOTEREQ
        msg['operation'] = undoEntry 
        #self._votes = {}
        for replica in self._replicas:
            logger.info("C: RPC call to replica: ")
            if replica.service.tpc_vote_replica(str(msg)) == False:
                logger.info('C: got VOTENO, hence aborting the trx.')
                self._datastore.abort()
                self._undoLog.pop()
                self.tpc_abort()
                return False
                
        # Commit Phase 2
        self.tpc_commit()
        print('\nAdded (%s, %s) to the data-store' % (key, value))
        return True
          
    def delete(self, key):
        logger.info('C: delete()')
        # Commit Phase 1 
        # Perform Action locally
        status = self.tpc_begin()
        if not status:
            logger.info('C: failure. Another trx already in process.')
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
        msg['sender'] = self.server
        msg['state'] = TwoPhaseCommitMessage.VOTEREQ
        msg['operation'] = undoEntry 
        #self._votes = {}
        for replica in self._replicas:
            if not replica.service.tpc_vote_replica(str(msg)):
                logger.info('C: got VOTENO, hence aborting the trx.')
                self._datastore.abort()
                self._undoLog.pop()
                self.tpc_abort()
                return False
                
        # Commit Phase 2
        self.tpc_commit()
        print('\nAdded (%s, %s) to the data-store' % (key, value))
        return True
    
    def get(self, key):  
        logger.info('C: get()')
        localValue = self._datastore.get_value(key)
        replicaValue = None
        
        for replica in self._replicas:
            replicaValue = replica.service.get_value_replica(key)
            if replicaValue is not None \
                and localValue is not None \
                and replicaValue!=localValue:
                print 'Inconsistent values!'
                return None
        return localValue
    
    def get_value_replica(self, key):
        logger.info('R: get_value_replica()')
        return self._datastore.get_value(key)
