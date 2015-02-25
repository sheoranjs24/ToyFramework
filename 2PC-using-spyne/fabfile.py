from fabric.api import *
import logging

#logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s: %(message)s')

#-----------------------
# Fabric Configuration
env.key_filename="/Volumes/JSHome/Users/sheoranjs24/.ssh/emulab_rsa"
env.user='jsheoran'
env.server_port = '7789'
env.home_dir = '/users/jsheoran'
#env.always_use_pty=False

# Read nodes name from the file
env.hosts = []
try:
    nodeFile = open('nodes.txt', 'r')
    for node in nodeFile:
        env.hosts.append(node.strip('\n'))
except:
    logging.error('File read error: nodes.txt')
    exit()
#print "hosts: ", env.hosts

# Identify server and client nodes
servers = []
clients = []
try:
    nodeFile = open('server-nodes.txt', 'r')
    for node in nodeFile:
        servers.append(node.strip('\n'))
except:
    logging.error('File read error: server-nodes.txt')
    servers = env.hosts
#print "servers: ", servers

try:
    nodeFile = open('client-nodes.txt', 'r')
    for node in nodeFile:
        clients.append(node.strip('\n'))
except:
    logging.error('File read error: client-nodes.txt')
    clients = env.hosts
#print "clients: ", clients

# define roles
env.roledefs.update({
    'server': servers,
    'client': clients,
    'configServer': [servers[0]]
})

#-----------------------
# Fabric Functions

def pingtest():
    run('ping -c 3 www.yahoo.com')

def uptime():
    run('uptime')

# Run only all nodes
@parallel
def config_nodes():
    with hide('warnings'), settings(warn_only=True):
        put('setup_nodes.sh', mode=0755)
        run("/bin/bash %s/setup_nodes.sh" % (env.home_dir))

# Run only on one node, as homedir is same in EmuLab
@roles('configServer')
def config_homedir():
    with hide('warnings'), settings(warn_only=True):
        put('setup_homedir.sh', mode=0755)
        run("/bin/bash %s/setup_homedir.sh" % (env.home_dir))

@roles('server')
@parallel
def start_servers():
    with hide('warnings'), settings(warn_only=True):
        put('start_server.sh', mode=0755)
        run("/bin/bash %s/start_server.sh %s " % (env.home_dir, env.server_port), pty=False)

@roles('configServer')
def connect_replicas():
     with hide('warnings'), settings(warn_only=True):
        put('replica_config.py', mode=0755)
        serverFile = env.home_dir + '/ToyFramework/2PC-using-spyne/server-nodes.txt'
        run("python %s/replica_config.py -P %s -F %s " % (env.home_dir, env.server_port, serverFile))

@roles('client')
@parallel
def start_clients():
    with hide('warnings'), settings(warn_only=True):
        put('start_client.sh', mode=0755)
        run("/bin/bash %s/start_client.sh %s" % (env.home_dir, env.server_port), pty=False)
