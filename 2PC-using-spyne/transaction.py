
import json, os, logging
from suds.client import Client
from suds.cache import NoCache
from spyne.client.http import HttpClient

from log import Log
from datastore import DataStore

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(level)s: %(message)s')
#logging.getLogger(__name__).setLevel(logging.INFO)

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
        logging.info('TM: set_server() called.')
        self.server = server
    
    def add_replica(self, replica_uri):
        logging.info('TM: add_replica() called.')
        if len(self._replicas)==0: 
            logging.debug('TM: replica added: %s', replica_uri)
            self._replicas = []
            self._replicaURIs = []
            self._replicaURIs.append(replica_uri)
            self._replicas.append(Client(replica_uri, cache=NoCache()))
        elif replica_uri not in self._replicaURIs:
            logging.debug('TM: replica added: %s', replica_uri)
            self._replicaURIs.append(replica_uri)
            self._replicas.append(replica_uri)
    
    def tpc_begin(self):
        # Create new transaction
        if self.currTransactionIndex is not None:
            return False
        else:
            logging.info('TM: new trx')
            if self._prevTransactionIndex is None:
                self.currTransactionIndex = 1
            else:
                self.currTransactionIndex = self._prevTransactionIndex + 1
            return True
    
    def tpc_vote_replica(self, msg):
        msg = eval(msg)
        logging.info('R: msg: %s', msg)
        # Check if a trx is already in process
        if self.currTransactionIndex is not None \
            and self.currTransactionIndex != int(msg['operation'][0]):
            logging.info('R: Another trx in process. Sending VOTE NO')
            DTEntry = [DTLogMessage.VOTEDNO, str(self.currTransactionIndex)]
            self._DTLog.write(DTEntry)
            return False
        
        # Check if trx if behind
        #TODO: Handle greater_than & less_than separately?
        if self._prevTransactionIndex is not None \
            and self._prevTransactionIndex+1 != int(msg['operation'][0]): 
            logging.info('R: trx is behind the coordinator. Sending VOTE NO')
            DTEntry = [DTLogMessage.VOTEDNO, str(self.currTransactionIndex)]
            self._DTLog.write(DTEntry)
            return False
        
        # Begin Trx
        status = self.tpc_begin()
        if status == False:
            logging.info('R: unable to begin trx. Sending VOTE NO')
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
                logging.info('R: operation not found. Sending VOTE NO')
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
        logging.info('R: msg: %s', msg)
        # Check trx id
        if self.currTransactionIndex is not None \
            and self.currTransactionIndex == int(msg['operation'][0]):   
            # Commit trx locally
            logging.debug("Writing to REDO log.")
            redoEntry = self._undoLog.peek()
            self._redoLog.write(redoEntry)
            self._datastore.commit()
            
            # Send COMMIT msg to replicas
            DTEntry = [DTLogMessage.COMMIT, str(self.currTransactionIndex)]
            self._DTLog.write(DTEntry)
            
            # Send ACK
            index = self._replicaURIs.index(msg['coordinator'])
            ack_msg = {}
            ack_msg['sender'] = self.server
            ack_msg['state'] = TwoPhaseCommitMessage.ACKNOWLEDGEMENT
            ack_msg['operation'] = redoEntry
            logging.info('R: sending ACK to coordinator.')
            #print 'Replica list: ', self._replicas, 
            #print self._replicas[index].last_sent(), self._replicas[index].last_received()
            #self._replicas[index].service.tpc_ack(str(ack_msg)) 
            logging.info('R: trx is finished.')
            self.tpc_finish()
            return True
        else:
            logging.info('R: Wrong trx id in msg:')
            return False
        
    def tpc_abort_replica(self, msg):
        msg = eval(msg)
        logging.info('R: msg: %s', msg)
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
            index = self._replicaURIs.index(msg['coordinator'])
            ack_msg = {}
            ack_msg['sender'] = self.server
            ack_msg['state'] = TwoPhaseCommitMessage.ACKNOWLEDGEMENT
            ack_msg['operation'] = popedEntry
            #logging.info('R: sending ACK to coordinator')
            #self._replicas[index].service.tpc_ack(str(ack_msg)) 
            logging.info('R: trx is finished')
            self.tpc_finish() 
            return True
        else:
            logging.info('R: Wrong trx id in msg.')
            return False

    def tpc_ack(self, msg):
        msg = eval(msg)
        logging.info('C: msg: %s', msg)
        if int(msg['operation'][0]) == self.currTransactionIndex \
            and msg['sender'] not in self._acks:
            self._acks.append(msg['sender'])
            
            # check if all ACKs are received
            if len(self._acks) == len(self._replicas):
                self.tpc_finish()
        else:
            logging.info('C: Wrong trx_id or duplicate message.')
    
    def tpc_commit(self):
        logging.info('C: tpc_commit()')
        # Commit trx locally
        logging.debug("writing to REDO log")
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
        logging.info('C: sending COMMIT to %d replicas', len(self._replicas))
        #print "rep: ", self._replicas
        for replica in self._replicas:
            print "Sending  to replica", replica
            #print replica.last_sent()
            #print replica.last_received()
            replica.service.tpc_commit_replica(str(msg))
            print "Sent  to replica"
        logging.info('C: waiting for ACKs.')
        self.tpc_finish()
    
    def tpc_abort(self):
        logging.info('C: tpc_abort()')
        
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
        logging.info('C: sending ROLLBACK to replicas')
        for replica in self._replicas:
            replica.service.tpc_abort_replica(str(msg))
        logging.info('C: waiting for ACKs.')
        self.tpc_finish()
        
    def tpc_finish(self):
        # Close existing trx
        logging.info('C: tpc_finish()')
        self._prevTransactionIndex = self.currTransactionIndex
        self.currTransactionIndex = None
    
    def put(self, key, value):
        logging.info('C: put()')
        # Commit Phase 1 
        # Perform Action locally
        status = self.tpc_begin()
        if not status:
            logging.info('C:failure. Another trx already in process.')
            #return False
        else:
            # Write entry into undo log
            logging.debug("writing to UNDO log")
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
            logging.info('C: send VOTE-REQ to replicas.')
            if replica.service.tpc_vote_replica(str(msg)) == False:
                logging.info('C: got VOTENO, hence aborting the trx.')
                self._datastore.abort()
                self._undoLog.pop()
                self.tpc_abort()
                #return False
                
        # Commit Phase 2
        self.tpc_commit()
        print('\nAdded (%s, %s) to the data-store' % (key, value))
        #return True
          
    def delete(self, key):
        logging.info('C: delete()')
        # Commit Phase 1 
        # Perform Action locally
        status = self.tpc_begin()
        if not status:
            logging.info('C: failure. Another trx already in process.')
            return False 
        else:
            # Write entry into undo log
            logging.debug("writing to UNDO log")
            undoEntry = [str(self.currTransactionIndex), 'delete', key]
            self._undoLog.write(undoEntry)
            self._datastore.delete_key(key)
            
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
                logging.info('C: got VOTENO, hence aborting the trx.')
                self._datastore.abort()
                self._undoLog.pop()
                self.tpc_abort()
                return False
                
        # Commit Phase 2
        self.tpc_commit()
        print('\nAdded (%s) to the data-store' % (key))
        return True
    
    def get(self, key):  
        logging.info('C: get()')
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
        logging.info('R: get_value_replica()')
        return self._datastore.get_value(key)
