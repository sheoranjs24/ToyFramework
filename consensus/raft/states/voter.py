import time

from .state import State


class Voter(State):

    def __init__(self):
        self._last_vote = None

    def on_vote_request(self, message):
        if(self._last_vote is None and
           message["lastLogIndex"] >= self._server._lastLogIndex):
            self._last_vote = message['sender']
            self._send_vote_response_message(message)
        else:
            self._send_vote_response_message(message, yes=False)

        return self, None

    def _send_vote_response_message(self, msg, yes=True):
        voteResponse = {
            'timestamp': int(time.time()),
            'sender': self._server._name,
            'receiver': msg['sender'],
            'type': 'RequestVoteResponse',
            'term': msg['term'],
            'response': yes
            }
        self._server.send_message(voteResponse)
