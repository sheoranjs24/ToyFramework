import time, random

from collections import defaultdict


class RaftMessage:
   AppendEntries = "AppendEntries"
   VoteRequest = "VoteRequest"
   VoteResponse = "VoteResponse"
   Response = "Response"

class ReplicaState:
  Follower = "Follower"
  Candidate = "Candidate"
  Leader = "Leader"

class RaftServer(object):

  def __init__(self, name=1, db='database.db', timeout=500):
    self._name = name
    self._server = None
    self._state = ReplicaState.Follower
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
    
    # Candidate field
    self._votes = {}
    
    # Timeout
    self._timeout = timeout
    self._timeoutTime = self._nextTimeout()
  
  def start(self, interface):
    """ Start service """
    print 'endpoints:', interface.get_endpoints()
    self._server = (interface.listen_host, interface.listen_port)
    self._start_election() 

  def _nextTimeout(self):
    self._currentTime = time.time()
    return self._currentTime + random.randrange(self._timeout,
                                                2 * self._timeout)
    
  def getValue(self, key, interface):
    ''' Return a value from the database to the client '''
    return self._datastore.get_value(key)
  
  def setValue(self, key, value, interface):
    ''' Set a value for a key in the database: request by client '''
    if self._state == ReplicaState.Leader:
      # add to log
      self._datastore.set_value(key, value)
      
      # send append entries
      # if success, commit & return to the client
      # tell commitIndex to all nodes to update
       
  def on_timeout(self, message):
    """ Leader timeout is reached. """
  
  def _start_election(self, interface):
    """ Start election for Leader. """
    self._currentTerm += 1
    election = {'timestamp': int(time.time()),
                'sender': self._server,
                'receiver': None,
                'type': RaftMessage.VoteRequest,
                'term': self._currentTerm,
                'data': {
                         "lastLogIndex": self._lastLogIndex,
                         "lastLogTerm": self._lastLogTerm,
                         }
                }

    self.send_message(election, interface)
    self._last_vote = self._server
        
  def handle_vote_request(self, message):
    """ Vote request."""
    if (self._last_vote is None and \
      message['data']['lastLogIndex'] >= self._lastLogIndex):
      self._last_vote = message['sender']
      voteResponse = True
    else:
      voteResponse = False
      
    # Send Message
    response = {'timestamp': int(time.time()),
                'sender': self.server,
                'receiver': message['sender'],
                'type': RaftMessage.VoteResponse,
                'term': message['term'],
                'response': voteResponse
                }
    self.send_message_to_one(response, interface)
    
  def handle_vote_response(self, message, interface):
    """ Node received a vote."""
    if message['sender'] not in self._votes:
      self._votes[message['sender']] = message
      if (len(self._votes.keys()) > interface.get_endpoints() / 2):
        self._state = ReplicaState.Leader
        
        # Reset nodes indexes
        for ep in range(1, interface.get_endpoints()):
          node = str(interface.endpoints[ep])
          self._nextIndexes[node] = self._lastLogIndex + 1
          self._matchIndex[node] = 0
        
        # Start heart-beat
        self._send_heart_beat(interface)
        
  def handle_append_entries(self, message, interface):
    """ Request to append an entry to the log. """
    self._timeoutTime = self._nextTimeout()

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
                     'type': RaftMessage.AppendEntries,
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
               'type': RaftMessage.AppendEntries,
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
                'sender': self.server,
                'receiver': message['sender'], 
                'type': RaftMessage.Response,
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
    if 'type' in message.keys():
      if(message['type'] == RaftMessage.AppendEntries):
        self.handle_append_entries(message, interface)
      elif(message['type'] == RaftMessage.VoteRequest):
        self.handle_vote_request(message, interface)
      elif(message['type'] == RaftMessage.VoteResponse):
        self.handle_vote_response(message, interface)
      elif(message['type'] == RaftMessage.Response):
        self.handle_response_received(message, interface)
      else:
        print('Error: unknown message sent ...')
        return
    else:
      print('Error: No message found...')
      return

