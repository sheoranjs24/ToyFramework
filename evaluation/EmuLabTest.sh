#! /bin/bash
# EmuLab Test Script

# Variables
path='/Volumes/JSHome/Users/sheoranjs24/Code/Grad-school-work/ToyFramework/Evaluation/'
user='jsheoran'
domain='.emulab.net'
sshFile='/Volumes/JSHome/Users/sheoranjs24/.ssh/emulab_rsa'
nodeFile='EmulabNodes.txt'

# Read node names from text file
#readarray nodes < $path$nodeFile
IFS=$'\r\n' GLOBIGNORE='*' :; nodes=($(cat $path$nodeFile))

# Explicitly report nodes
let i=0
while (( ${#nodes[@]} > i )); do
    printf "${nodes[i++]}\n"
done

# Test Bandwidth
# connect to server
server=$user'@'${nodes[0]}$domain
echo "server: $server"
ssh -i $sshFile $server 'bash -s' < $path'ServerScript.sh'
# connect to client
client=$user'@'${nodes[1]}$domain
echo "client: $client"
ssh -i $sshFile $client 'bash -s' <  $path'ClientScript.sh' ${nodes[0]}$domain >> /tmp/client.txt 
cat /tmp/client.txt




