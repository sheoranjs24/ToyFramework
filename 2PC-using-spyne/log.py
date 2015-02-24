import logging, pickle

class Log(object):
    
    def __init__(self, log_path='log_file.log'):
        self.log_path = log_path
        self.log = []
        
        # Read the log file and load data
        try:
            log_file = open(self.log_path, 'r')
        except IOError:
            log_file = None

        if log_file is not None:
            try:
                self.log = pickle.load(log_file)
            except EOFError:
                pass
    
    def write(self, msg):
        self.log.append(msg)
        # write to file
        log_file = open(self.log_path, 'w')
        pickle.dump(self.log, log_file)
        print "log: ", msg
        
    def peek(self):
        print "logg:", self.log
        if len(self.log) == 0:
            return None
        else:
            return self.log[len(self.log)-1]
        
    def pop(self):
        self.log.pop()
        # write to file
        log_file = open(self.log_path, 'w')
        pickle.dump(self.log, log_file)