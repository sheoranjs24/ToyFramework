'''
Created on Feb 22, 2015

@author: sheoranjs24
'''

import service, api
from consensus import TransactionManager
from dictionary import dictionary, ResourceManager, ReplicaManager

"""  Future
Steps:
 1. Configure Servers - dictionary & ResourceManagers
 2. Configure ReplicaManager
 3. Create connection with ReplicaManager
 4. perform operations like get, put, delete
 """

""" 
Steps:
 1. Configure Servers - dictionary & ResourceManagers
 2. Create TransactionManager()
 3. Add replicas RMs to TM
 4. perform operations like get, put, delete on RM1
 """

server = ''  #ReplicaManager

# Create a transaction manager
TM = TransactionManager()

# connect to two key-value pair stores
rc1 = connectToDBAtNode1(node1_host)
rc2 = connectToDBAtNode1(node2_host)

TM.register(rc1)
TM.register(rc2)

trx = TM.being_transaction()



