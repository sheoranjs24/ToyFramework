import time, random, threading

from collections import defaultdict


class RaftMessage:
   AppendEntries = "AppendEntries"
   VoteRequest = "VoteRequest"
   VoteResponse = "VoteResponse"
   Response = "Response"
   ClientRequest = "ClientRequest"

class RaftState:
  FOLLOWER = "Follower"
  CANDIDATE = "Candidate"
  LEADER = "Leader"

class RaftServer(object):

  def __init__(self, name=1, db='database.db', timeout=500):
    self._name = name
    self._server = None
    self._state = RaftState.FOLLOWER
    self._datastore = Database(db)
    
    self._commitIndex = 0
    self._currentTerm = 0
    self._lastApplied = 0
    self._lastLogIndex = 0
    self._lastLogTerm = None
    
    # Leader fields
    self._nextIndexes = defaultdict(int)
    self._matchIndex = defaultdict(int)
    
    # Follower field
    self._last_vote = None 
    self._leader = None
    
    # Candidate field
    self._votes = {}
    
    # Timeout
    self._timeout = timeout
    self._timer = None
  
  def start(self, interface):
    """ Start service """
    print 'endpoints:', interface.get_endpoints()
    self._server = (interface.listen_host, interface.listen_port)
    
    # retrieve logs
    log_index = interface.get_log_count() - 1
    if log_index < 0:
      return
    
    last_log = interface.get_log(log_index)
    self._term = last_log['term']
    self._commitIndex = last_log['commitIndex']
    self._last_vote = last_log['vote']
    
    timeoutTime = self._nextTimeout()
    self._timer = threading.Timer(timeoutTime, self.on_timeout(interface))
    self._timer.start()

  def _nextTimeout(self):
    return random.randrange(self._timeout, 2 * self._timeout)
    
  def getValue(self, key, interface):
    ''' Return a value from the database to the client '''
    return self._datastore.get_value(key)
  
  def setValue(self, key, value, interface):
    ''' Set a value for a key in the database: request by client '''
    if self._state == RaftState.LEADER:
      oldValue = ''
      if key in self._datastore.keys():
        oldValue = self._datastore.get_value(key)
        
      self._datastore.set_value(key, value)
      
      # add to log
      interface.write_log({self._commitIndex: {
                                               'term': self._currentTerm,
                                               'commitIndex': self._commitIndex,
                                               'vote': self._server,
                                               'operation': 'set',
                                               'key': key,
                                               'oldValue': oldValue,
                                               'newValue': value
                                               }})
      self._datastore.commit()
      self._lastApplied = None
      self._lastLogIndex = self._commitIndex
      self._lastLogTerm = self._currentTerm
      self._commitIndex += 1
    else:
      print('Server is not the Leader.')
      # pass request to the leader
      interface.send_message_to_one({'sender': self._server,
                                     'receiver': self._leader,
                                     'type': 'msg',
                                     'operation': 'setValue',
                                     'key': key,
                                     'value': value
                                     })
  
  def handle_client_reqeust(self, message, interface):
    "Handles client request as passed from followers"
    if message['operation'] == 'setValue':
      self.setValue(message['key'], message['value'], message['interface'])
      return
    else:
      print('Unknown operation found.') 
      return
       
  def on_timeout(self, interface):
    """ Timeout is reached. """
    # Check the state of the server
    if self._state == RaftState.FOLLOWER:
      # Upgrade to Candidate and start election
      self._state = RaftState.CANDIDATE
      self._term += 1
      self._start_election(interface) 
    elif self._state == RaftState.CANDIDATE:
      # Restart the election
      self._start_election(interface)
  
  def _start_election(self, interface):
    """ Start election for Leader. """
    self._currentTerm += 1
    election = {'timestamp': int(time.time()),
                'sender': self._server,
                'receiver': None,
                'type': 'msg',
                'message': RaftMessage.VoteRequest,
                'term': self._currentTerm,
                'data': {
                         "lastLogIndex": self._lastLogIndex,
                         "lastLogTerm": self._lastLogTerm,
                         }
                }

    self.send_message(election, interface)
    self._last_vote = self._server
    
    # restart the timer
    timeoutTime = self._nextTimeout()
    self._timer = threading.Timer(timeoutTime, self.on_timeout(interface))
    self._timer.start()
        
  def handle_vote_request(self, message):
    """ Vote request."""
    if self._state == RaftState.FOLLOWER:
      # restart the timer
      self._timer.stop()
      timeoutTime = self._nextTimeout()
      self._timer = threading.Timer(timeoutTime, self.on_timeout(interface))
      self._timer.start()
    
    self._leader = None
    reason = ''
    
    # Compare term
    if message['term'] < self._currentTerm:
      voteResponse = False
      reason = 'term'  
    elif (self._last_vote is None and \
      message['data']['lastLogIndex'] >= self._lastLogIndex):
      self._last_vote = message['sender']
      voteResponse = True
    else:
      voteResponse = False
      reason = 'logIndex'
      
    # Send Message
    response = {'timestamp': int(time.time()),
                'sender': self._server,
                'receiver': message['sender'],
                'type': 'msg',
                'message': RaftMessage.VoteResponse,
                'term': message['term'],
                'response': voteResponse,
                'reason': reason
                }
    self.send_message_to_one(response, interface)
    
  def handle_vote_response(self, message, interface):
    """ Node received a vote."""
    if message['sender'] not in self._votes:
      if message['response'] == True:
        self._votes[message['sender']] = message
        if (len(self._votes.keys()) > interface.get_endpoints() / 2):
          self._state = RaftState.LEADER
          self._timer.stop()
          
          # Reset nodes indexes
          for ep in range(1, interface.get_endpoints()):
            node = str(interface.endpoints[ep])
            self._nextIndexes[node] = self._lastLogIndex + 1
            self._matchIndex[node] = 0
          
          # Start heart-beat
          self._send_heart_beat(interface)
      else:
          # Check if there is already a leader
          print('Vote No: reason', message['reason'])
          if message['reason'] == 'term':
            # step down to Follower
            self._state = RaftState.FOLLOWER
    else:
      print('Duplicate vote response.')
        
  def handle_append_entries(self, message, interface):
    """ Request to append an entry to the log. """
    self._timer.stop()
    # start the timer
    timeoutTime = self._nextTimeout()
    self._timer = threading.Timer(timeoutTime, self.on_timeout(interface))
    self._timer.start()
    
    self._leader = message['sender']
    
    # check state and step down to Follower
    if self._state == RaftState.CANDIDATE:
      self._state = RaftState.FOLLOWER

    if (message['term'] < self._currentTerm):
      self.send_message_response(message, interface, yes=False)
      return

    if (message['data'] != {}):
      log_index = interface.get_log_count() 
      data = message['data']

      # Check if leaderCommit matches the replic's commitIndex
      if (data['leaderCommit'] != self._commitIndex):
        self._commitIndex = min(data['leaderCommit'], log_index - 1)

      # Check if log index is smaller than prevLogIndex
      if (log_index < data['prevLogIndex']):
        self.send_message_response(message, interface, yes=False)
        return

      # Make sure that the prevLogIndex term is equal to the Leader.
      if (log_index > 0 and \
          interface.get_log(log_index)[data['prevLogIndex']]['term'] != data['prevLogTerm']):
        # Conflict: delete everything from this prevLogIndex 
        interface.delete_log(index=data['prevLogIndex'])
        self.send_message_response(message, interface, yes=False)
        self._lastLogIndex = data['prevLogIndex']
        self._lastLogTerm = data['prevLogTerm']
        return 
      else:
        # Check if the commitIndex value is equal to the leader.
        if (log_index > 0 and \
            data['leaderCommit'] > 0 and \
            interface.get_log(log_index)[data['leaderCommit']]['term'] != message['term']):
          # Data was found to be different so we fix that
          #   by taking the current log and slicing it to the
          #   leaderCommit + 1 range then setting the last
          #   value to the commitValue
          interface.delete_log(self._commitIndex)
          for e in data['entries']:
            interface.write_log(e)
            self._commitIndex += 1

          self.send_message_response(message, interface, yes=True)
          self._lastLogIndex =  interface.get_log_count() - 1
          self._lastLogTerm = interface.get_log(self._lastLogIndex-1)['term']
          self._commitIndex = interface.get_log_count() - 1
        else:
          # The commit index matches.
          if(len(data['entries']) > 0):
            for e in data['entries']:
              interface.write_log(e)
              self._commitIndex += 1

            self._lastLogIndex = interface.get_log_count() - 1
            self._lastLogTerm = interface.get_log(self._lastLogIndex-1)['term']
            self._commitIndex = interface.get_log_count() - 1
            self.send_message_response(message, interface, yes=True)

      self.send_message_response(message, interface, yes=True)
      return
    else:
      return 

  def handle_response_received(self, message, interface):
    """A response is sent back to the Leader"""
    # Was the last AppendEntries good?
    if(not message['data']['response']):
      # No, so lets back up the log for this node
      self._nextIndexes[message['sender']] -= 1

      # Get the next log entry to send to the client.
      previousIndex = max(0, self._nextIndexes[message['sender']] - 1)
      previous = interface.get_log(previousIndex)
      current = interface.get_log(self._nextIndexes[message['sender']])

      # Send the new log to the client and wait for it to respond.
      appendEntry = {'timestamp': int(time.time()),
                     'sender': self._server,
                     'receiver': message['sender'],
                     'type': 'msg',
                     'message': RaftMessage.AppendEntries,
                     'term': self._currentTerm,
                     'data': {
                              'leaderId': self._server,
                              'prevLogIndex': previousIndex,
                              'prevLogTerm': previous['term'],
                              'entries': [current],
                              'leaderCommit': self._commitIndex,
                              }
                     }

      self.send_message_to_one(appendEntry, interface)
    else:
      # The last append was good so increase their index.
      self._nextIndexes[message['sender']] += 1

      # Are they caught up?
      if(self._nextIndexes[message['sender']] > self._lastLogIndex):
        self._nextIndexes[message['sender']] = self._lastLogIndex
  
  def _send_heart_beat(self, interface):
    """ Send AppendEntries message to replicas """
    message = {'timestamp': int(time.time()),
               'sender': self._server,
               'receiver': None,
               'type': 'msg',
               'message': RaftMessage.AppendEntries,
               'term': self._currentTerm,
               'data': {'leaderId': self._server,
                        'prevLogIndex': self._lastLogIndex,
                        'prevLogTerm': self._lastLogTerm,
                        'entries': [],
                        'leaderCommit': self._commitIndex,
                        }
               }
    self.send_message(message, interface)  

  def send_message_response(self, message, interface, yes=True):
    response = {'timestamp': int(time.time()),
                'sender': self._server,
                'receiver': message['sender'], 
                'type': 'msg',
                'message': RaftMessage.Response,
                'term': msg['term'], 
                'data': {
                         'response': yes,
                         'currentTerm': self._currentTerm,
                         }
                }
    send_message_to_one(response, interface)
       
  def send_message_to_all(self, message, interface):
    nodes = interface.get_endpoints()
    for ep in range (1, nodes):
      interface.sendMessage(ep, message)
  
  def send_message_to_one(self, message, interface):
    # Find index of receiver node
    nodes = interface.get_endpoints()
    receiver = None
    for ep in range (1, nodes):
      if message['receiver'] == list(interface.endpoints[ep]):
        receiver = ep
        break
    if receiver is not None:
      interface.sendMessage(receiver, message)
           
  def gotMessage(self, message, interface):
    # Check if sender exists in the replica list
    if 'sender' in msg.keys():
      replica = None
      nodes = interface.get_endpoints() 
      for ep in range(1, nodes):
        if message['sender'] == list(interface.endpoints[ep]):
          replica = True
          break
      if replica is None:
        print('Error: unknown sender ...')
        return
    else:
      print('Error: sender key is not found in message ...')
      return
    
    # Check Term
    if(message['term'] > self._currentTerm):
      self._currentTerm = message['term']
    elif(message['term'] < self._currentTerm):
      self.send_message_response(message, interface, yes=False)
      return self, None
    
    # Message Type
    if 'message' in message.keys():
      if(message['message'] == RaftMessage.AppendEntries):
        self.handle_append_entries(message, interface)
      elif(message['message'] == RaftMessage.VoteRequest):
        self.handle_vote_request(message, interface)
      elif(message['message'] == RaftMessage.VoteResponse):
        self.handle_vote_response(message, interface)
      elif(message['message'] == RaftMessage.Response):
        self.handle_response_received(message, interface)
      elif(message['message'] == RaftMessage.ClientRequest):
        self.handle_client_reqeust(message, interface)
      else:
        print('Error: unknown message sent ...')
        return
    else:
      print('Error: No message found...')
      return

