import logging
import service, api

logger = logging.getLogger('ToyFramework')

class Participant:
    def __init__(self):
        self.host = service.get_host()
        self.data = None
        self.coodinator = None
        self.state = None
    
    def handle_query_to_commit_message(self, msg):
        # Do not process the transaction while one is already in progress
        if self.state is not None:
            # check for duplicate message
            if self.coordinator.match(msg['coordinator']) and self.data == msg['data']:
                logger.info("Duplicate message: QUERY TO COMMIT")
            else:
                logger.error("New message while transaction is in process")
                response = msg
                response['state'] = 'VOTE NO'
                service.send_message(self.host, msg['coordinator'], response)
        else:
            # Send VOTE YES message
            self.data = msg['data']
            self.coordinator = msg['coordinator']
            self.state = 'VOTE YES'
            response = msg
            response['state'] = 'VOTE YES'
            service.send_message(self.host, self.coordinator, response)
    
    def handle_commit_message(self, msg):
        # Confirm that it is same transaction
        if self.coordinator.match(msg['coordinator']) and self.data == msg['data']:
            logger.info("Commiting the data")
            #TODO: Commit data locally
            api.delete(key)
            
            # Send ACK to coordinator
            response = msg
            response['state'] = 'ACKNOWLEDGMENT'
            service.send_message(self.host, self.coordinator, response)
            
            # Transaction complete
            self.data = None
            self.coodinator = None
            self.state = None
        else:
            logger.error("Not the same transaction")
            # do nothing
                
    def handle_rollback_message(self, msg):
        # Confirm that it is same transaction
        if self.coordinator.match(msg['coordinator']) and self.data == msg['data']:
            logger.info("Rollback the data")
            # Send ACK to coordinator
            response = msg
            response['state'] = 'ACKNOWLEDGMENT'
            service.send_message(self.host, self.coordinator, response)
            
            # Transaction complete
            self.data = None
            self.coodinator = None
            self.state = None
        else:
            logger.error("Not the same transaction")
            # do nothing
                
    def receive_message(self, sender, msg):
        logger.debug("Message received: %s from sender: %s" % (msg, sender))
        
        if msg['state'].match('QUERY TO COMMIT'):
            self.handle_query_to_commit_message(msg)
        
        elif msg['state'].match('COMMIT'):
            self.handle_commit_message(msg)
        
        elif msg['state'].match('ROLLBACK'):
             self.handle_rollback_message(msg)
        

        