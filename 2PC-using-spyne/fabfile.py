from fabric.api import *
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(level)s: %(message)s')

#-----------------------
# Fabric Configuration
env.key_filename="/Volumes/JSHome/Users/sheoranjs24//.ssh/emulab_rsa"
env.user='jsheoran'
env.server_port = 7789

# Read nodes name from the file
env.hosts = []
try:
    nodeFile = open('nodes.txt', 'r')
    for node in nodeFile:
        env.hosts.append(node)
except:
    logging.error('File read error: nodes.txt')
    exit()

# Identify server and client nodes
servers = []
clients = []
try:
    nodeFile = open('server-nodes.txt', 'r')
    for node in nodeFile:
        servers.append(node)
except:
    logging.error('File read error: server-nodes.txt')
    servers = env.hosts
try:
    nodeFile = open('client-nodes.txt', 'r')
    for node in nodeFile:
        clients.append(node)
except:
    logging.error('File read error: client-nodes.txt')
    clients = env.hosts
    
env.roledefs.update({
    'server': servers,
    'client': clients,
    'configServer': servers[0]
})

#-----------------------
# Fabric Functions

def pingtest():
    run('ping -c 3 www.yahoo.com')

def uptime():
    run('uptime')

@roles('server')
@parallel
def start_servers():
    with hide('running','warnings'), settings(warn_only=True):
        put('server_setup_script.sh', mode=0755)
        run('/root/server_setup_script.sh %s' % env.server_port)

@roles('configServer')
def configure_replicas():
     with hide('running','warnings'), settings(warn_only=True):
        put('replica_config.py', mode=0755)
        run('python /root/replica_config.py %s' % env.server_port)

@roles('client')
@parallel
def start_clients():
    with hide('running','warnings'), settings(warn_only=True):
        put('client_setup_script.sh', mode=0755)
        run('/root/client_setup_script.sh %s' % env.server_port)
