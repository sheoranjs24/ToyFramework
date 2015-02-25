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
1. Access to EmuLab experiment(www.emulab.net). 
2. Ubuntu 14.04 OS on EmuLab nodes.

## Steps to run the code:
1. Environment setup:
 - Make sure python and git are installed. 
 - Install pip: `$ python get-pip.py`      
 - Install fabric: `$ pip install fabric`     
2. Configuration:
 - Create a file 'nodes.txt' containing a list of all the nodes address (hostname or ipaddress). 
 - Optionally create server-nodes.txt and client-nodes.txt contain list of server and client nodes respectively.
 - Configure user, server_port and key_filename in fabfile.py.  [Note: fabfile is configured to work with EmuLab. Change the config to work with other systems]
 - Note: Script files (.sh) used in fabfile.py assumes Ubuntu 14.04. If your OS is different, please make relevant changes to the script files.
3. Execute the program:
 - Configure nodes: `$ fab config_nodes`  
 - Configure EmuLab's home directory: `$ fab config_homedir`
 - Start servers: `$ fab start_servers`
 - Create connection between servers: `$ fab connect_replicas`
 - Start client(s): `$ fab start_clients`   
 - [Note: Clients will run in parallel on each client node]   
