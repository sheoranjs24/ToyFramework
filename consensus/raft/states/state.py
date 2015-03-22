import time, random

class State(object):
    
    def set_server(self, server):
        self._server = server

    def on_message(self, message):
        """ This method is called when a message is received,
        and calls one of the other corresponding methods
        that this state reacts to.

        """
        _type = message['type']

        if(message['term'] > self._server._currentTerm):
            self._server._currentTerm = message['term']
        # Is the messages.term < ours? If so we need to tell
        #   them this so they don't get left behind.
        elif(message['term'] < self._server._currentTerm):
            self._send_response_message(message, yes=False)
            return self, None

        if(_type == 'AppendEntries'):
            return self.on_append_entries(message)
        elif(_type == 'RequestVote'):
            a = self.on_vote_request(message)
            return a
        elif(_type == 'RequestVoteResponse'):
            return self.on_vote_received(message)
        elif(_type == 'Response'):
            return self.on_response_received(message)

    def on_leader_timeout(self, message):
        """This is called when the leader timeout is reached."""

    def on_vote_request(self, message):
        """This is called when there is a vote request."""

    def on_vote_received(self, message):
        """This is called when this node receives a vote."""

    def on_append_entries(self, message):
        """This is called when there is a request to
        append an entry to the log.

        """

    def on_response_received(self, message):
        """This is called when a response is sent back to the Leader"""

    def on_client_command(self, message):
        """This is called when there is a client request."""

    def _nextTimeout(self):
        self._currentTime = time.time()
        return self._currentTime + random.randrange(self._timeout,
                                                    2 * self._timeout)
    def _send_response_message(self, msg, yes=True):
        response = {'timestamp': int(time.time()),
                    'sender': self._server._name,
                    'receiver': msg['sender'], 
                    'type': 'Response',
                    'term': msg['term'], 
                    'data': {
                             'response': yes,
                             'currentTerm': self._server._currentTerm,
                             }
                    }
        self._server.send_message_response(response)
