# ! /bin/bash
SERVER_PORT=$1

# activate virtual env
source $HOME/.bashrc
workon toyframework

# get into directory
folder=`echo $HOST | cut -d. -f1`
cd $folder

# start server
DATE=$(date +"%Y%m%d%H%M")
python $HOME/ToyFramework/2PC-using-spyne/server.py -H $HOST -P $SERVER_PORT > toyframework-$DATE.log 2>&1 &
echo "server started!"

