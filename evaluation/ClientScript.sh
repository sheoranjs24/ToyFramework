#! /bin/bash
server=$1

/usr/local/etc/emulab/emulab-iperf -c $server -f k -i 60 -t 60