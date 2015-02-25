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

sudo apt-get install -y libxml2-dev 
sudo apt-get install -y libxslt1-dev 
sudo apt-get install -y python-dev 
sudo apt-get install -y git
sudo apt-get install -y curl
if [ $? -ne 0 ] 
then
  echo "Error while installing packages."
fi

# install python packages
echo "installing python dependencies..."
curl https://bootstrap.pypa.io/get-pip.py > get-pip.py
sudo python get-pip.py
sudo pip install virtualenv
sudo pip install virtualenvwrapper
echo "# python virtual environment \n\
VIRTUALENVWRAPPER_PYTHON=/usr/bin/python \n\
export VIRTUALENVWRAPPER_SCRIPT='/usr/local/bin/virtualenvwrapper.sh' \n\
export WORKON_HOME=$HOME/.virtualenvs \n\
source /usr/local/bin/virtualenvwrapper.sh\n" >> $HOME/.bashrc
source $HOME/.bashrc
mkvirtualenv toyframework

sudo pip install lxml
sudo pip install twisted
sudo pip install spyne
sudo pip install suds

# install project files
echo "downloading project from github..."
git clone https://github.com/prashantchhabra89/ToyFramework.git
mkdir client_run
cd client_run
python $HOME/ToyFramework/2PC-using-spyne/test.py -P $SERVER_PORT -F "$HOME/ToyFramework/2PC-using-spyne/server-nodes.txt" > toyframework.log 2>&1 &
echo "client started!"


