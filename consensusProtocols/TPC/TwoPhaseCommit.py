import logging

from dictionary.datastore import Database
from Carbon.AppleEvents import ePageDownKey

'''
TODOs:
  ADD logs for recovery
  ADD recovery code
  ADD exceptions
  ADD logging 
  ADD documentation comments
'''
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
  
  def __init__(self, server_name=1, db_name=None):
    self._datastore = Database(db_name)
    self._prevTransactionIndex = 0
    self.currTransactionIndex = None
    self._replicaResponses = []
    self.coordinator = None
    self.server = None
    self.name = server_name
  
  def start(self, interface):
    print 'endpoints:', interface.get_endpoints()
    self.server = (interface.listen_host, interface.listen_port)
    
    for i in range(0, interface.get_log_count()):
      key = interface.get_log(i)['key']
      value = interface.get_log(i)['value']
      self._datastore.set_value(key, value)
    self._datastore.commit()
      
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
  
  def tpc_finish(self):
    ''' Close existing transaction '''
    logging.info('TM: Transaction complete: %d', self.currTransactionIndex)
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
    self._datastore.commit()
    
    # send message
    if self.coordinator == self.server:
      # send COMMIT message
      nodes = interface.get_endpoints() 
      for ep in range(1, nodes):
        interface.sendMessage(ep, {'sender': self.coordinator,
                                   'coordinator': self.coordinator, 
                                   'type': 'msg', 
                                   'message': TPCMessage.COMMIT,
                                   'transaction_id': msg['transaction_id'],
                                   }
                                )
      logging.info('TM: waiting for acknowledgments...')
    else:
      self.tpc_finish()    
      # Find coordinator index
      receiver = None
      for ep in range(1, interface.get_endpoints()):
        if msg['coordinator'] == list(interface.endpoints[ep]):
          receiver = ep
          break  
      # Send ACK message
      interface.sendMessage(receiver, {'sender': self.server,
                                   'coordinator': msg['coordinator'], 
                                   'type': 'msg', 
                                   'message': TPCMessage.ACKNOWLEDGEMENT,
                                   'transaction_id': msg['transaction_id'],
                                   }
                            )
    
    
  def tpc_rollback(self, msg, interface):
    ''' Rollback the transaction '''
    # abort transaction
    self._datastore.abort()
    
    # send message
    if self.coordinator == self.server:
      # send ROLLBACK message
      nodes = interface.get_endpoints() 
      for ep in range(1, nodes):
        interface.sendMessage(ep, {'sender': self.coordinator,
                                   'coordinator': self.coordinator, 
                                   'type': 'msg', 
                                   'message': TPCMessage.ROLLBACK,
                                   'transaction_id': msg['transaction_id'],
                                   }
                                )
      logging.info('TM: waiting for acknowledgments...')
    else:
      self.tpc_finish()     
      # Find coordinator index
      receiver = None
      for ep in range(1, interface.get_endpoints()):
        if msg['coordinator'] == list(interface.endpoints[ep]):
          receiver = ep 
          break
      # Send ACK message
      interface.sendMessage(receiver, {'sender': self.server,
                                   'coordinator': msg['coordinator'], 
                                   'type': 'msg', 
                                   'message': TPCMessage.ACKNOWLEDGEMENT,
                                   'transaction_id': msg['transaction_id'],
                                   }
                            )
      
  def handle_vote_request(self, msg, interface):
    if msg['operation'] == 'setValue':
      if self.currTransactionIndex is None:
        # Check transaction number
        if self._prevTransactionIndex >= msg['transaction_id']:
          print('Duplicate request for transaction: %d', msg['transaction_id'])
          return
        elif self._prevTransactionIndex+1 < msg['transaction_id']:
          print('Transaction id is much higher than previous.')
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
      self.tpc_rollback(msg, interface)
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
        self.tpc_finish()
    else:
      print('Duplicate ACK received for transaction: %d', msg['transaction_id'])
      return
  
  def handle_decision_request(self, msg, interface):
    ''' Return decision of an old transaction '''
    
  def gotMessage(self, msg, interface):
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
        print('VOTE-REQ received for trx: %d.' % msg['transaction_id'])
        self.handle_vote_request(msg, interface)
        
      elif msg['message'] == TPCMessage.COMMIT:
        print('COMMIT received for trx: %d.' % msg['transaction_id'])
        self.tpc_commit(msg, interface)
        
      elif msg['message'] == TPCMessage.ROLLBACK:
        print('ROLLBACK received for trx: %d.' % msg['transaction_id'])
        self.tpc_rollback(msg, interface)
        
      elif msg['message'] == TPCMessage.VOTEYES:
        print('YES received for trx: %d.'% msg['transaction_id'])
        self.handle_vote_yes(msg, interface)
        
      elif msg['message'] == TPCMessage.VOTENO:
        print('NO received for trx: %d.' % msg['transaction_id'])
        self.handle_vote_no(msg, interface)
        
      elif msg['message'] == TPCMessage.ACKNOWLEDGEMENT:
        print('ACK received for trx: %d.'% msg['transaction_id'])
        self.handle_ack(msg, interface)
        
      elif msg['message'] == TPCMessage.DECISIONREQ:
        print('DECISION-REQ received for trx: %d.' % msg['transaction_id'])
        self.handle_decision_request(msg, interface)
        
      else:
        print('Error: unknown message sent ...')
        return
    else:
      print('Error: No message found...')
      return
