# ToyFramework
A distributed framework for testing consensus of distributed algorithms

## Contributors
Jyoti Sheoran   
Min Xiang   
Prashant Chhabra   

## Main Components
- Framework   
- Distributed Application  
- Consensus Protocol(s)   
- Analysis and tests  

## Project #1
1. Implement basic Framework using twisted library.
 - Provide communication protocols for relicas to communicate with each other and with client
 - Provide basic consensus protocol
 - A basic clients that connects with a replica and send commands to put/get keys.
 - Profiler with basic tests : correctness, performance, etc.
2. Implement Two Phase Commit Protocol with synchronous RPC calls between the replicas using Spyne library.
 - A Transaction Manager to handle automic transactions (put/get)
 - A Replica Manager to forward requests to Transaction Manager
 - Test on EmuLab.
3. A distributed key-value storage service with reliable storage
4. Scripts to perform testing on Emulab.

## Project #2
1. Add more features to the Framework.
 - Provide logging on stable storage.
 - Trace for debugging protocol implementation.
 - Reproducible event/failure sequence for debugging/profiling.
 - Provide API for Profiler to shutdown node and cutoff connection.
2. Implement Two Phase Commit Protocol using the ToyFramework.
 - Consensus Protocol implemenation
 - Recovery logs
 - Handle node failure/recovery.
3. Implement Raft Protocol using the ToyFramework.
 - Consensus Protocol implemenation
 - Recovery logs
 - Handle node failure/recovery.

## Requirements
1. Access to EmuLab experiment (www.emulab.net). 
2. Ubuntu 14.04 OS on EmuLab nodes. Refer Evaluation/EmuLabExperiment.ns for a sample ns file.

## Steps to run the code:
1. Environment setup:
 - Make sure python and git are installed. 
 - Install pip: `$ python get-pip.py`      
 - Install fabric: `$ pip install fabric`     
2. Configuration:
 - Create a file 'nodes.txt' containing a list of all the nodes address (hostname or ipaddress). 
 - Create server-nodes.txt and client-nodes.txt contain list of server and client nodes respectively.
 - Configure user, server_port and key_filename in fabfile.py.  [Note: fabfile is configured to work with EmuLab. Change the config to work with other systems]
 - Note: Script files (.sh) used in fabfile.py assumes Ubuntu 14.04. If your OS is different, please make relevant changes to the script files.
3. Execute the program:
 - Configure nodes: `$ fab config_nodes`  
 - Configure EmuLab's home directory: `$ fab config_homedir`
 - Start servers: `$ fab start_servers`
 - Create connection between servers: `$ fab connect_replicas`
 - Start client(s): `$ fab start_clients`   
 - [Note: Clients will run in parallel on each client node]   

## Structure of the code
1. **Framework** (code available in 'interface' folder)    
![ToyFramework Diagram](https://drive.google.com/uc?id=0B8fAcTjfL47FMmZxNGdOMWlWS00)
2. **Consensus Protocols** (code available in 'consensusProtocols' folder)     
Implementation of various consensus protocols. We have implemented 2PC and Raft.    
 2.1 **Two Phase Commit**   
Replicas communicate with each other via the ToyFramework communication protocol. There are 7 types of messages that can be sent between replicas : VOTE-REQ, VOTE-YES, VOTE-NO, COMMIT, ROLLBACK, ACKNOWLEDGEMENT and DECISION-REQ. The transaction logs are saved in stable storage using ToyFramework for failure recovery. When a server starts, it calls the method start(), which looks at the logs to determine if it needs to deal with failure recovery. Client can request get_value() and set_value() methods. The set_value() methods initiates a Two-Phase Commit Transaction.    
 2.2 **Raft**      
RaftServer class implements the Raft protocol. The server store the state of the replica in _state, which can be any one of Follower, Candidate and Leader. A server is initiated with Follower state. Once a leader is elected, the leader regularly sends AppendEntries message to all replicas. 
3. **Distributed Key-value Store** : (code available in 'dictionary' folder)    
There are two implementations of distributed key-value store. One uses static functions (dictionary.py) and the other uses non-static functions (datastore.py). Both the implemenations save data on stable storage. 
The implementation in datastore.py provides transaction support (commit/abort). Any update is first saved in the RAM and  stored in stable storage on commit() operation.   
4. **Testing on Emulab** : (code available in 'evaluation' folder)   
We have provided sample scripts to perform testing on Emulab. 2PC-using-spyne also contains ready-made scripts to perform test on Emulab.
5. **Two-Phase Commit implementation using RPC** (code available in '2PC-using-spyne' folder)       
A server Replica consists of Transaction Manager. Transaction Manager connects to Resource Manager (key-value datastore). A server communicates to its replicas using RPC calls over HTTP (transport protocol) with SOAP (information exchange protocol). A client can connected to any of the server using the server address (hostname or public ip address) and the port number.
 1. Two-Phase Commit Implementation: Transaction Manager (TM) is responsible for handling 2PC commit protocol. TM is exposed to client and its replicas using Replica class RPC methods. Each put() or delete() request from the client is treated as atomic transaction. TM also maintains 3 logs - Undo log, Redo log and TM log. Each log entry contains the transaction id. Whenever Server is restarted, it checks the logs to see if there is any unfinished transaction and rollbacks to last consistent state. All logs are saved in files in non-volatile memory (e.g. hard-disk).
 2. RPC communication between Replicas: We used Spyne package to implement RPC communication between the replicas. SOAP protocol is used as information exchange protocol. To communicate with a replica, server act as a client and vice-versa. Most of the RPC calls are synchronous (i.e. client waits for a certain amount of time for the results).
 3. Data-store: All uncommitted data is stored in volatile memory (put() and delete() methods). When a commit is made, the data is saved to a file in hard-disk. 
 4. Client: A client first connects to the server and asks for WSDL file. It then calls server methods using client.service.method_name().


## Handling Failures
- Clients waits for a certain timeout time, before throwing exception that they are unable to get response or connect to the server.
- TM maintains logs for each transaction which can be used for recovery.

## Test-cases
- Sanity check: Have a client connect to a server and give some queries.
- Two clients connected to same server.
- Multiple clients connected multiple servers. 
- Performance Test.

## Future Scope
- As the logs are maintained, new replicas can be added any time and can be made up-to-date using the logs. In future, we would like to explore this scenario.
- Consider 2PC optimizations.
- Authentication and security

## Running the framework alone
- Go to Interface/ folder, start a framework instance:
 - python node.py 127.0.0.1:5000 --logfile 1.log
- Start another instance, connecting to the first one:
 - python node.py 127.0.0.1:6000 --logfile 2.log --connect 127.0.0.1:5000
- Start a client that connect to one of the instance:
 - python client.py 127.0.0.1:6000
- Under the client you can use folling command to interact with the framework instance
 - get &lt;key&gt;
 - set &lt;key&gt; &lt;value&gt;
 - exit
- You can check the console that runs the framework instance to see the even logging and the log file you specified for protocol related storages.
- To use consensus protocols (2PC or Raft):
 - add additional argument when firing up the replicas: --db database.db
   `python interfaces/node.py --logfile log1.log --db database1.pkl --name 1 127.0.0.1:11122`
 - Also, make sure that the server is started with the consensus protocol:
   `protocol.setAlgorithm(TwoPhaseCommit(opt.name, opt.db))`

