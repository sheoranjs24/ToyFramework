

class ResourceManager(Object):
    
    def __init__(self, undo_file='undo.log', redo_file='redo.log'):
        self.trx_id = None
        
        try:
            self.undo_log = open(self.undo_file, "r")
            # TODO: Go to the last line to record transaction index
        except IOError:
            print("log file did not exist and hence it will be created")
            self.undo_log = open (self.undo_file, "w+")
        
        try:
            self.redo_log = open(self.redo_file, "r")
            # TODO: Go to the last line to record transaction index
        except IOError:
            print("log file did not exist and hence it will be created")
            self.redo_log = open (self.redo_file, "w+")
        
    def abort(self):
        """ rollback """
        
    def tpc_begin(self, transaction): 
        """ Begin 2PC protocol """
          
    def commit(transaction):
        """ Commit """
        
    def tpc_vote(transaction):
        """ Vote """
        
    def tpc_finish(transaction):
        """ Confirmation of commit """
        
    def tpc_abort(transaction):
        """ Abort trx """
        
    def sortKey(self):
        """ For total ordering of resource managers """
        
    