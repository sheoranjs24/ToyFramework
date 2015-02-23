import logging
import service

logger = logging.getLogger('ToyFramework')

class Coordinator:
    
    def __init__(self):
        self.host = service.get_host()
        
        # Get a list of participants lists : QUESTION
        self.participants = service.get_replica_set()
        if (self.host in self.participants):
            self.participants.remove(self.host)
        
    def inititate_commit(self, data):
        # Commit Request Phase
        self.msg = dict()
        self.msg['state'] = 'QUERY TO COMMIT'
        self.msg['coordinator'] = self.host
        self.msg['data'] = data
        self.voteList = dict()
        service.send_message(self.host, self.participants, self.msg)
        logger.debug('QUERY To COMMIT message sent.')
    
    def commit(self):
        self.msg['state'] = 'COMMIT'
        self.ackList = []
        service.send_message(self.host, self.participants, self.msg)
        logger.debug('COMMIT message sent.')
    
    def rollback(self):
        self.msg['state'] = 'ROLLBACK'
        self.ackList = []
        service.send_message(self.host, self.participants, self.msg)
        logger.debug('ROLLBACK message sent.')
    
    def receive_message(self, sender, msg):
        logger.debug("Message received: %s from sender: %s" % (msg, sender))
        
        if sender not in self.participants:
            logger.exception("Sender is not in the participants list: %s" % sender)
            raise UnknownHostException
        
        if not msg['state'].match(self.msg['state']):
            logger.error("State does not match the Coordinator's state: %s" % msg['state'])
        
        # Parse the messgge: VOTE YES/NO, COMMIT/ROLLBACK, ACKNOWLEDGMENT
        if msg['response'].match('VOTE YES') and msg['state'].match('QUERY TO COMMIT'):
            # Record sender response in the list
            if sender not in self.voteList.keys():
                self.voteList[sender] = true
            else:
               logger.info("Duplicate message: %s received from: %s" % (msg['response'], sender)) 
            
            # check if all messages are collected
            if self.voteList.len() == self.participants.len():
                logger.info("All votes received")
                self.commit()
                            
        elif msg['response'].match('VOTE NO') and msg['state'].match('QUERY TO COMMIT'):
            # Send ROLLBACK message to every participant
            self.rollback()
        
        elif msg['response'].match('ACKNOWLEDGMENT') and not msg['state'].match('QUERY TO COMMIT'):
            if sender not in self.ackList:     
                self.ackList.append(sender)
            else:
                logger.info("Duplicate message: %s received from: %s" % (msg['response'], sender))
           
           # check if all messages are collected
            if self.ackList.len() == self.participants.len():
                logger.info("All ACK received")
                #TODO: Send transaction complete signal
        
                
            
            
        