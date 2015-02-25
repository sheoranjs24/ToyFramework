# ! /bin/bash
SERVER_PORT=$1

# check if basic command line utilites are present
echo "checking installed softwares..."
which python
if [ $? -ne 0 ] 
then
  echo "python not found."
fi

# install stuff
echo "updating the system..."
apt-get update
if [ $? -ne 0 ] 
then
  echo "Error while updating the server."
fi

apt-get install -y libxml2-dev 
apt-get install -y libxslt1-dev 
apt-get install -y python-dev 
apt-get install -y git
if [ $? -ne 0 ] 
then
  echo "Error while installing packages."
fi

# install python packages
echo "installing python dependencies..."
sudo python get-pip.py
sudo pip install virtualenv
sudo pip install virtualenvwrapper
cat "# python virtual environment
VIRTUALENVWRAPPER_PYTHON=/usr/local/bin/python
export VIRTUALENVWRAPPER_SCRIPT='/usr/local/bin/virtualenvwrapper.sh'
export WORKON_HOME=$HOME/.virtualenvs
source /usr/local/bin/virtualenvwrapper.sh" >> $HOME/.bashrc
source $HOME/.bashrc
mkvirtualenv server

sudo pip install lxml
sudo pip install twisted
sudo pip install spyne
sudo pip install suds

# install project files
echo "downloading project from github..."
git clone https://github.com/prashantchhabra89/ToyFramework.git
mkdir server_run
cd server_run
python $HOME/ToyFramework/2PC-using-spyne/server.py -H $HOSTNAME -P $SERVER_PORT > toyframework.log 2>&1 &
echo "server started!"


