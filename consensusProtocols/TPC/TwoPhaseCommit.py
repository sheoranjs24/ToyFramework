import logging

from dictionary.datastore import Database
from collections import defaultdict

'''
TODOs:
  ADD exceptions
  ADD logging 
  ADD documentation comments
'''

class TCPLog:
  START = 1
  FINISH = 2
  COMMIT = 3
  ROLLBACK = 4
  VOTEYES = 5
  VOTENO = 6
  UPDATE = 7
  ABORT = 8

class TPCMessage:
  VOTEREQ = "Vote Request"
  VOTEYES = "Vote Yes"  
  VOTENO = "Vote No"  
  COMMIT = "Commit"  
  ROLLBACK = "Rollback"
  ACKNOWLEDGEMENT = "Acknowledgement"
  DECISIONREQ = "Decision Request"
    
class TwoPhaseCommit(object):
  ''' Implements Transaction Manager for Two Phase Commit (2PC) '''
  
  def __init__(self, server_name=1, db=None):
    self._datastore = Database(file_path=db)
    self._prevTransactionIndex = 0
    self.currTransactionIndex = None
    self._replicaResponses = []
    self.coordinator = None
    self.server = None
    self.name = server_name
  
  def start(self, interface):
    print 'endpoints:', interface.get_endpoints()
    self.server = (interface.listen_host, interface.listen_port)
    
    # Read last log
    log_index = interface.get_log_count() 
    log_type = interface.get_log(log_index)['type']
    
    if log_type == TCPLog.START:
      # coordinator node, Rollback the transaction
      self.currTransactionIndex = interface.get_log(log_index)['trx_id']
      self._prevTransactionIndex = self.currTransactionIndex - 1 
      self.coordinator = self.server
      self.tpc_rollback(interface)
      return
    
    elif log_type == TCPLog.VOTEYES:
      # participant node, Request coordinator for decision
      self.currTransactionIndex = interface.get_log(log_index)['trx_id']
      self._prevTransactionIndex = self.currTransactionIndex - 1 
      self.coordinator = interface.get_log(log_index)['coordinator'] 
      # send decision request to coordinator
      self.send_decision_request(interface)
      return
    
    elif log_type == TCPLog.VOTENO:
      # participant node, Rollback the transaction
      self.currTransactionIndex = interface.get_log(log_index)['trx_id']
      self._prevTransactionIndex = self.currTransactionIndex - 1 
      self.coordinator = interface.get_log(log_index)['coordinator']      
      tpc_rollback(interface)
      return
    
    elif log_type == TCPLog.UPDATE:
      self.currTransactionIndex = interface.get_log(log_index)['trx_id']
      self._prevTransactionIndex = self.currTransactionIndex - 1 
      self.coordinator = interface.get_log(log_index)['coordinator'] 
      
      # check if database value is correct
      key = interface.get_log(log_index)['key']
      newValue = interface.get_log(log_index)['newdata']
      if self._datastore.get_value(key) != newValue:
        self._datastore.set_value(key, newValue)
        self._datastore.commit()
        
      # process transaction
      if self.coordinator == self.server:
        send_decision_to_all(TPCMessage.COMMIT, interface)
      else:
        # send ACK
        send_ack(interface)
      return
    
    elif log_type == TCPLog.ABORT:
      # rollback the transction, 
      # if coordinator send ROLLBACK message
      # if participant, send Acknowledgement to coordinator
      self.currTransactionIndex = interface.get_log(log_index)['trx_id']
      self._prevTransactionIndex = self.currTransactionIndex - 1 
      self.coordinator = interface.get_log(log_index)['coordinator']
            
      # Check node state in the transaction  
      if self.coordinator == self.server:
        # send ROLLBACK message
        send_decision_to_all(TPCMessage.ROLLBACK, interface)
      else:
        # send ACK
        send_ack(interface)
      return
      
    elif log_type == TCPLog.COMMIT:
      # Node is coordinator, send decision to participants
      self.coordinator = self.server
      self.currTransactionIndex = interface.get_log(log_index)['trx_id']
      self._prevTransactionIndex = self.currTransactionIndex - 1           
      # send COMMIT message
      send_decision_to_all(TPCMessage.COMMIT, interface)
      return
    
    elif log_type == TCPLog.ROLLBACK:
      # Node is coordinator, send decision to participants
      self.coordinator = self.server
      self.currTransactionIndex = interface.get_log(log_index)['trx_id']
      self._prevTransactionIndex = self.currTransactionIndex - 1         
      # send ROLLBACK message
      send_decision_to_all(TPCMessage.ROLLBACK, interface)
      return
    
    elif log_type == TCPLog.FINISH:
      # Last transction was successful.
      self._prevTransactionIndex = interface.get_log(log_index)['trx_id']
      print('Database is up-to-date.')
      return
    
    else:
      print('Unknown log type...')
      return
    
      
  def getValue(self, key, interface):
    ''' Return a value from the database '''
    return self._datastore.get_value(key)
  
  def tpc_begin(self):
    ''' Start a new transaction '''
    if self.currTransactionIndex is not None:
      return False
    else:
      logging.info('TM: New Transaction started.')
      self.currTransactionIndex = self._prevTransactionIndex + 1
      return True
  
  def tpc_finish(self, interface):
    ''' Close existing transaction '''
    logging.info('TM: Transaction complete: %d', self.currTransactionIndex)
    interface.write_log({'time': int(time.time()),
                         'trx_id' : self.currTransactionIndex,
                         'type' : TCPLog.FINISH,
                         'coordinator': self.coordinator,
                         'participants': interface.endpoints,
                         })
    self._prevTransactionIndex += 1
    self.currTransactionIndex = None
    self.coordinator = None
  
  def setValue(self, key, value, interface):
    ''' Set a value for a key in the database '''
    logging.info('TM: setValue %s %s', key, value)
    
    # 2PC Phase 1
    # Prepare
    status = self.tpc_begin()
    if not status:
      logging.info('TM: Another transaction is already in process.')
      return False  
    self._datastore.set_value(key, value)
    
    # write to log
    oldValue = self._datastore.get(key)
    interface.write_log({'time': int(time.time()),
                         'trx_id' : self.currTransactionIndex,
                         'type' : TCPLog.START,
                         'coordinator': self.coordinator,
                         'participants': interface.endpoints
                         })
    
    # Send 'VOTE-REQ' to participants
    self.coordinator = self.server
    nodes = interface.get_endpoints() 
    for ep in range(1, nodes):
      interface.sendMessage(ep, {'sender': self.coordinator,
                                 'coordinator': self.coordinator, 
                                 'name': self.name,
                                 'type': 'msg', 
                                 'message': TPCMessage.VOTEREQ,
                                 'transaction_id': self.currTransactionIndex, 
                                 'operation': 'setValue', 
                                 'key': key, 
                                 'value': value,
                                 }
                            )
    logging.info('TM: waiting for votes...')
  
  def tpc_commit(self, msg, interface):
    ''' Commit the transaction '''
    # commit transaction
    interface.write_log({'time': int(time.time()),
                         'trx_id' : self.currTransactionIndex,
                         'type' : TCPLog.UPDATE,
                         'coordinator': self.coordinator,
                         'participants': interface.endpoints,
                         'operation': 'set',
                         'key': key,
                         'olddata': oldValue,
                         'newdata' : value
                         })
    self._datastore.commit()
    
    # check node
    if self.coordinator == self.server:
      send_decision_to_all(self.currTransactionIndex, TPCMessage.COMMIT, interface)
      return
    else:
      send_ack(msg, interface)
      return
    
  def tpc_rollback(self, interface):
    ''' Rollback the transaction '''
    # abort transaction
    interface.write_log({'time': int(time.time()),
                         'trx_id' : self.currTransactionIndex,
                         'type' : TCPLog.ABORT,
                         'coordinator': self.coordinator,
                         'participants': interface.endpoints
                         })
    self._datastore.abort()
    
    # check node
    if self.coordinator == self.server:
      send_decision_to_all(self.currTransactionIndex, TPCMessage.ROLLBACK, interface)
      return
    else:
      send_ack(interface)
      return
  
  def send_ack(self, interface):
    ''' Send Acknowledgement to the coordinator. '''
    
    self.tpc_finish(interface)  
      
    # Find coordinator index
    receiver = None
    for ep in range(1, interface.get_endpoints()):
      if msg['coordinator'] == list(interface.endpoints[ep]):
        receiver = ep
        break  
      
    # Send ACK message
    interface.sendMessage(receiver, {'sender': self.server,
                                     'coordinator': self.coordinator, 
                                     'type': 'msg', 
                                     'message': TPCMessage.ACKNOWLEDGEMENT,
                                     'transaction_id': self.currTransactionIndex,
                                     }
                          )
  
  def send_decision_to_all(self, decision, interface):
    if decision == TPCMessage.ROLLBACK:
      log_type = TCPLog.ROLLBACK
    elif decision == TPCMessage.COMMIT:
      log_type = TCPLog.COMMIT
      
    # write to log
    interface.write_log({'time': int(time.time()),
                         'trx_id' : self.currTransactionIndex,
                         'type' : log_type,
                         'coordinator': self.coordinator,
                         'participants': interface.endpoints
                         })
  
    # send ROLLBACK message
    nodes = interface.get_endpoints() 
    for ep in range(1, nodes):
      interface.sendMessage(ep, {'sender': self.coordinator,
                                 'coordinator': self.coordinator, 
                                 'type': 'msg', 
                                 'message': decision,
                                 'transaction_id': self.currTransactionIndex,
                                 }
                              )
    logging.info('TM: waiting for acknowledgments...')
    
  def handle_vote_request(self, msg, interface):
    if msg['operation'] == 'setValue':
      if self.currTransactionIndex is None:
        # Check transaction number
        if self._prevTransactionIndex >= msg['transaction_id']:
          print('Duplicate request for transaction: %d', msg['transaction_id'])
          return
        elif self._prevTransactionIndex+1 < msg['transaction_id']:
          print('Transaction id is much higher than previous.')
          # Write to log
          interface.write_log({'time': int(time.time()),
                               'trx_id' : self.currTransactionIndex,
                               'type' : TCPLog.VOTENO,
                               'coordinator': self.coordinator,
                               'participants': interface.endpoints
                               })
          
          # Find coordinator index
          receiver = None
          for ep in range(1, interface.get_endpoints()):
            if self.coordinator == list(interface.endpoints[ep]):
              receiver = ep 
              break
          # Vote NO
          interface.sendMessage(receiver, {'sender': self.server,
                                           'coordinator': msg['coordinator'], 
                                           'type': 'msg', 
                                           'message': TPCMessage.VOTENO,
                                           'transaction_id': msg['transaction_id'],
                                          }
                                )
      
        else:
          # Prepare
          self.tpc_begin()
          self._datastore.set_value(msg['key'], msg['value'])
          self.coordinator = msg['coordinator']
          print 'coordinator: ', self.coordinator
          
          # Write to log
          interface.write_log({'time': int(time.time()),
                               'trx_id' : self.currTransactionIndex,
                               'type' : TCPLog.VOTEYES,
                               'coordinator': self.coordinator,
                               'participants': interface.endpoints
                               })
          
          # Find coordinator index
          receiver = None
          for ep in range(1, interface.get_endpoints()):
            if self.coordinator == list(interface.endpoints[ep]):
              receiver = ep 
              break
          # Vote YES
          interface.sendMessage(receiver, {'sender': self.server,
                                           'coordinator': msg['coordinator'], 
                                           'type': 'msg', 
                                           'message': TPCMessage.VOTEYES,
                                           'transaction_id': self.currTransactionIndex,
                                           }
                                )
      else:
        print('Another transaction already in process.')
        # Write to log
        interface.write_log({'time': int(time.time()),
                             'trx_id' : self.currTransactionIndex,
                             'type' : TCPLog.VOTENO,
                             'coordinator': self.coordinator,
                             'participants': interface.endpoints
                             })
          
        # Find coordinator index
        receiver = None
        for ep in range(1, interface.get_endpoints()):
          if self.coordinator == list(interface.endpoints[ep]):
            receiver = ep 
            break
        # Vote NO
        interface.sendMessage(receiver, {'sender': self.server,
                                         'coordinator': msg['coordinator'], 
                                         'type': 'msg', 
                                         'message': TPCMessage.VOTENO,
                                         'transaction_id': self.currTransactionIndex,
                                         }
                              )
    else:
      print('Error: unknown operation.')
      return
  
  def handle_vote_yes(self, msg, interface):
    ''' Record votes '''
    # 2PC Phase 2
    if self.currTransactionIndex == msg['transaction_id'] and \
      msg['sender'] not in self._replicaResponses:
      self._replicaResponses.append(msg['sender'])
      # Check if all votes are received
      if len(self._replicaResponses) == (interface.get_endpoints() - 1):
        self._replicaResponses = []
        self.tpc_commit(msg, interface)
    else:
      print('Duplicate VOTE-YES received for transaction: %d', msg['transaction_id'])
      return
    
  def handle_vote_no(self, msg, interface):
    ''' Abort the transaction '''
    # 2PC Phase 2
    if self.currTransactionIndex == msg['transaction_id'] and \
      msg['sender'] not in self._replicaResponses:
      # Abort the transaction
      self._replicaResponses = []
      self.tpc_rollback(interface)
    else:
      print('Duplicate VOTE-NO received for transaction: %d', msg['transaction_id'])
      return
  
  def handle_ack(self, msg, interface):
    ''' Record Acknowledgments '''
    # 2PC Phase 2
    if self.currTransactionIndex == msg['transaction_id'] and \
      msg['sender'] not in self._replicaResponses:
      self._replicaResponses.append(msg['sender'])
      # Check if all acknowledgments are received
      if len(self._replicaResponses) == (interface.get_endpoints() - 1):
        self._replicaResponses = []
        self.tpc_finish(interface)
    else:
      print('Duplicate ACK received for transaction: %d', msg['transaction_id'])
      return
  
  def handle_decision_request(self, msg, interface):
    ''' Return decision of an old transaction '''
  
  def send_decision_request(self, interface):
    ''' Send Decision Request to Coordinator '''
    # Find coordinator index
    receiver = None
    for ep in range(1, interface.get_endpoints()):
      if self.coordinator == list(interface.endpoints[ep]):
        receiver = ep 
        break  
    
    # send message
    interface.sendMessage(receiver, {'sender': self.server,
                                     'coordinator': self.coordinator, 
                                     'type': 'msg', 
                                     'message': TPCMessage.DECISIONREQ,
                                     'transaction_id': self.currTransactionIndex,
                                     }
                              )
      
  def gotMessage(self, msg, interface):
    ''' Handle received messages '''
    # Check if sender exists in the replica list
    if 'sender' in msg.keys():
      replica = None
      nodes = interface.get_endpoints() 
      for ep in range(1, nodes):
        if msg['sender'] == list(interface.endpoints[ep]):
          replica = True
          break
      if replica is None:
        print('Error: unknown sender ...')
        return
    else:
      print('Error: sender key is not found in message ...')
      return
    
    if 'message' in msg.keys():
      if msg['message'] == TPCMessage.VOTEREQ:
        logging.info('VOTE-REQ received for trx: %d.', msg['transaction_id'])
        self.handle_vote_request(msg, interface)
        
      elif msg['message'] == TPCMessage.COMMIT:
        logging.info('COMMIT received for trx: %d.', msg['transaction_id'])
        self.tpc_commit(msg, interface)
        
      elif msg['message'] == TPCMessage.ROLLBACK:
        logging.info('ROLLBACK received for trx: %d.', msg['transaction_id'])
        self.tpc_rollback(interface)
        
      elif msg['message'] == TPCMessage.VOTEYES:
        logging.info('YES received for trx: %d.', msg['transaction_id'])
        self.handle_vote_yes(msg, interface)
        
      elif msg['message'] == TPCMessage.VOTENO:
        logging.info('NO received for trx: %d.', msg['transaction_id'])
        self.handle_vote_no(msg, interface)
        
      elif msg['message'] == TPCMessage.ACKNOWLEDGEMENT:
        logging.info('ACK received for trx: %d.', msg['transaction_id'])
        self.handle_ack(msg, interface)
        
      elif msg['message'] == TPCMessage.DECISIONREQ:
        logging.info('DECISION-REQ received for trx: %d.', msg['transaction_id'])
        self.handle_decision_request(msg, interface)
        
      else:
        print('Error: unknown message sent ...')
        return
    else:
      print('Error: No message found...')
      return
