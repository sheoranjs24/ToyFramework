from state.follower import Follower

class Server(object):

  def __init__(self, name=0, log=[], interface):
    self._name = name
    self._state = Follower()
    self._log = log
    self._neighbors = interface.get_endpoints()
    self._total_nodes = 0

    self._commitIndex = 0
    self._currentTerm = 0

    self._lastApplied = 0

    self._lastLogIndex = 0
    self._lastLogTerm = None

    self._state.set_server(self)

  def send_message(self, message, interface):
    for ep in range (1, self._neighbors):
      interface.sendMessage(ep, message)

  def send_message_response(self, message, interface):
    n = [n for n in self._neighbors if n._name == message.receiver]
    if(len(n) > 0):
      interface.sendMessage(n[0], message)
            
  def gotMessage(self, message, interface):
    state, response = self._state.on_message(message)

    self._state = state

