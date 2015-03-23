import logging

from datastore import Database

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
  
  def __init__(self):
    self._datastore = Database()
    self._prevTransactionIndex = 0
    self.currTransactionIndex = None
    self._replicaResponses = []
    self.coordinator = None
  
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
    self.coordinator = interface.master
    nodes = interface.get_endpoints() 
    for ep in range(1, nodes):
      interface.sendMessage(ep, {'sender': self.coordinator,
                                 'coordinator': self.coordinator, 
                                 'type': 'msg', 
                                 'message': TPCMessage.VOTEREQ,
                                 'transaction_id': self.currTransactionIndex, 
                                 'operation': 'setValue', 
                                 'key': key, 
                                 'value': value
                                 }
                            )
    logging.info('TM: waiting for votes...')
  
  def tpc_commit(self, msg=None):
    ''' Commit the transaction '''
    # commit transaction
    self._datastore.commit()
    
    # send message
    if self.coordinator == interface.master:
      # send COMMIT message
      nodes = interface.get_endpoints() 
      for ep in range(1, nodes):
        interface.sendMessage(ep, {'sender': self.coordinator,
                                   'coordinator': self.coordinator, 
                                   'type': 'msg', 
                                   'message': TPCMessage.COMMIT,
                                   'transaction_id': msg['transaction_id']
                                   }
                                )
      logging.info('TM: waiting for acknowledgments...')
    else:
      self.tpc_finish()
      # Send ACK message
      interface.sendMessage(self.coordinator, {'sender': interface.master,
                                   'coordinator': self.coordinator, 
                                   'type': 'msg', 
                                   'message': TPCMessage.ACKNOWLEDGEMENT,
                                   'transaction_id': msg['transaction_id']
                                   }
                            )
    
    
  def tpc_rollback(self, msg=None):
    ''' Rollback the transaction '''
    # abort transaction
    self._datastore.abort()
    
    # send message
    if self.coordinator == interface.master:
      # send ROLLBACK message
      nodes = interface.get_endpoints() 
      for ep in range(1, nodes):
        interface.sendMessage(ep, {'sender': self.coordinator,
                                   'coordinator': self.coordinator, 
                                   'type': 'msg', 
                                   'message': TPCMessage.ROLLBACK,
                                   'transaction_id': msg['transaction_id']
                                   }
                                )
      logging.info('TM: waiting for acknowledgments...')
    else:
      self.tpc_finish()
      # Send ACK message
      interface.sendMessage(self.coordinator, {'sender': interface.master,
                                   'coordinator': self.coordinator, 
                                   'type': 'msg', 
                                   'message': TPCMessage.ACKNOWLEDGEMENT,
                                   'transaction_id': msg['transaction_id']
                                   }
                            )
      
  def handle_vote_request(self, msg):
    if msg['operation'] == 'setValue':
      if self.currTransactionIndex is None:
        # Check transaction number
        if self._prevTransactionIndex >= msg['transaction_id']:
          print('Duplicate request for transaction: %d', msg['transaction_id'])
          return
        elif self._prevTransactionIndex+1 < msg['transaction_id']:
          # Vote NO
          print('Transaction id is much higher than previous.')
          interface.sendMessage(msg['coordinator'], {'sender': interface.master,
                                                     'coordinator': msg['coordinator'], 
                                                     'type': 'msg', 
                                                     'message': TPCMessage.VOTENO,
                                                     'transaction_id': msg['transaction_id']
                                                     }
                                )
      
        else:
          # Prepare
          self.tpc_begin()
          self._datastore.set_value(msg['key'], msg['value'])
          self.coordinator = msg['coordinator']
          # Vote YES
          interface.sendMessage(msg['coordinator'], {'sender': interface.master,
                                                     'coordinator': msg['coordinator'], 
                                                     'type': 'msg', 
                                                     'message': TPCMessage.VOTEYES,
                                                     'transaction_id': self.currTransactionIndex
                                                     }
                                )
      else:
        print('Another transaction already in process.')
        # Vote NO
        interface.sendMessage(msg['coordinator'], {'sender': interface.master,
                                                   'coordinator': msg['coordinator'], 
                                                   'type': 'msg', 
                                                   'message': TPCMessage.VOTENO,
                                                   'transaction_id': self.currTransactionIndex
                                                   }
                              )
    else:
      print('Error: unknown operation.')
      return
  
  def handle_vote_yes(self, msg):
    ''' Record votes '''
    # 2PC Phase 2
    if self.currTransactionIndex == msg['transaction_id'] and \
      msg['sender'] not in self._repicaResponses:
      self._repicaResponses.append(msg['sender'])
      # Check if all votes are received
      if len(self._repicaResponses) == len(interface.get_endpoints()):
        self._replicaResponses = []
        self.tpc_commit()
    else:
      print('Duplicate VOTE-YES received for transaction: %d', msg['transaction_id'])
      return
    
  def handle_vote_no(self, msg):
    ''' Abort the transaction '''
    # 2PC Phase 2
    if self.currTransactionIndex == msg['transaction_id'] and \
      msg['sender'] not in self._repicaResponses:
      # Abort the transaction
      self._replicaResponses = []
      self.tpc_rollback()
    else:
      print('Duplicate VOTE-NO received for transaction: %d', msg['transaction_id'])
      return
  
  def handle_ack(self, msg):
    ''' Record Acknowledgments '''
    # 2PC Phase 2
    if self.currTransactionIndex == msg['transaction_id'] and \
      msg['sender'] not in self._repicaResponses:
      self._repicaResponses.append(msg['sender'])
      # Check if all acknowledgments are received
      if len(self._repicaResponses) == len(interface.get_endpoints()):
        self._replicaResponses = []
        self.tpc_finish()
    else:
      print('Duplicate ACK received for transaction: %d', msg['transaction_id'])
      return
  
  def handle_decision_request(self, msg):
    ''' Return decision of an old transaction '''
    
  def gotMessage(self, msg, interface):
    # Check if sender exists in the replica list
    if 'sender' in msg.keys():
      if msg['sender'] not in interface.get_endpoints():
        print('Error: unknown sender ...')
        return
    else:
      print('Error: sender key is not found in message ...')
      return
    
    if 'message' in msg.keys():
      if msg['message'] == TPCMessage.VOTEREQ:
        print('VOTE-REQ received by ...')
        handle_vote_request(msg)
        
      elif msg['message'] == TPCMessage.COMMIT:
        print('COMMIT received by ...')
        tpc_commit(msg)
        
      elif msg['message'] == TPCMessage.ROLLBACK:
        print('ROLLBACK received by ...')
        tpc_rollback(msg)
        
      elif msg['message'] == TPCMessage.VOTEYES:
        print('YES received by ...')
        handle_vote_yes(msg)
        
      elif msg['message'] == TPCMessage.VOTENO:
        print('NO received by ...')
        handle_vote_no(msg)
        
      elif msg['message'] == TPCMessage.ACKNOWLEDGEMENT:
        print('ACK received by ...')
        handle_ack(msg)
        
      elif msg['message'] == TPCMessage.DECISIONREQ:
        print('DECISION-REQ received by ...')
        handle_decision_request(msg)
        
      else:
        print('Error: unknown message sent by ...')
        return
    else:
      print('Error: No message found ...')
      return
