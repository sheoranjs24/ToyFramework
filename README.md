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
- Communication Protocol  
- Analysis and tests  

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
1. **Framework** (code available in Interface folder)    
2. **Two-Phase Commit implementation using RPC** (code available in 2PC-using-spyne folder)    
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

## Future Scope
- As the logs are maintained, new replicas can be added any time and can be made up-to-date using the logs. In future, we would like to explore this scenario.
- Consider 2PC optimizations.
- Authentication and security

## Project #2
Test consensus protocol(s) using our test framework.
 
