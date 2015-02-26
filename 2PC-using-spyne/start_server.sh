# ! /bin/bash
SERVER_PORT=$1

# activate virtual env
source $HOME/.bashrc
workon toyframework

# get into directory
folder=`echo $HOST | cut -d. -f1`
cd $folder

# get public ip
IPADDR=`ifconfig eth0 | grep "inet addr:" | cut -d: -f2 | awk '{ print $1}'`

# start server
DATE=$(date +"%Y%m%d%H%M")
python $HOME/ToyFramework/2PC-using-spyne/server.py -H $IPADDR -P $SERVER_PORT > toyframework-$DATE.log 2>&1 &
echo "server started!"

