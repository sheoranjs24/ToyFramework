#! /bin/bash
# EmuLab Test Script

# Variables
path='/Volumes/JSHome/Users/sheoranjs24/Code/Grad-school-work/ToyFramework/Evaluation/'
user='jsheoran'
domain='.emulab.net'
sshFile='/Volumes/JSHome/Users/sheoranjs24/.ssh/emulab_rsa'
nodeFile='EmulabNodes.txt'

# Read node names from text file
readarray nodes < $path$nodeFile

# Explicitly report nodes
let i=0
while (( ${#nodes[@]} > i )); do
    printf "${nodes[i++]}\n"
done

# Test Bandwidth
# connect to server
host=$user+'@'+${nodes[0]}+$domain
echo "host: $host"
ssh -i $sshFile $host
/usr/local/etc/emulab/emulab-iperf -s &
exit
# connect to client
host=$user+'@'+${nodes[1]}+$domain
echo "host: $host"
ssh -i $sshFile $host
/usr/local/etc/emulab/emulab-iperf -c server -f k -i 60 -t 60
exit



