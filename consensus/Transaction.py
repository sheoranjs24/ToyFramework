"""
    Transaction for Two Phase Commit (2PC)
"""

import Coordinator, Participant

_LOGGER = None
def _makeLogger():
    if _LOGGER is not None:
        return _LOGGER
    return logging.getLogger("txn")

class TransactionException(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class TransactionError(Exception):
    """An error occurred due to normal transaction processing."""
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class Status:
    # New is the initial State
    NEW = "New"
    COMMITTING = "Committing"
    COMMITTED = "Committed"
    COMMITFAILED = "Commit Failed"
    READONLY = "Read Only"  #Not sure if we need this: QUESTION

class TwoPhaseCommitMessage:
    VOTEREQ = "Vote Request"
    VOTEYES = "Vote Yes"
    VOTENO = "Vote No"
    COMMIT = "Commit"
    ROLLBACK = "Rollback"
    ACKNOWLEDGEMENT = "Acknowledgement"

class Transaction(object):
    
    def __init__(self, transaction_manager=None):
        self.status = Status.NEW
        self._transaction_manager = transaction_manager
        self._resources = []
        self._voted = {}  # true if voted
        self._failure_traceback = None
        self.log = _makeLogger()
        self.log.debug("new transaction")
    
    def _prior_operation_failed(self):
        assert self._failure_traceback is not None
        raise TransactionError("An operation previously failed, "
                "with traceback:\n\n%s" %
                self._failure_traceback.getvalue())
    
    def join(self, resource):
        if self.status is Status.COMMITFAILED:
            self._prior_operation_failed() 

        if (self.status is not Status.ACTIVE):
            raise ValueError("expected txn status %r, but it's %r" % (
                             Status.ACTIVE, self.status))
        self._resources.append(resource)

    def _unjoin(self, resource):
        self._resources = [r for r in self._resources if r is not resource]
    
    def commit(self, data):
        
        if self.status is Status.COMMITFAILED:
            self._prior_operation_failed()
        
        self.status = Status.COMMITTING
        
        try:
            self._commitData(data)
            self.status = Status.COMMITTED
        except:
            self.log("Exception while performing commit")
        self.log.debug("commit")
        
    def _commitData(self):
        # Execute the two-phase commit protocol.
        coordinator = Coordinator(self.transaction_manager.participants)
                
    def rollback(self):
        for rm in self._resources:
            service.send_message()
        self.log.debug("rollback")
        
        
        