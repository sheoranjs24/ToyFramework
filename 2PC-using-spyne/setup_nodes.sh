# check if basic command line utilites are present
echo "checking installed softwares..."
which python
if [ $? -ne 0 ] 
then
  echo "python not found."
fi

# install stuff
echo "updating the system..."
sudo apt-get update
if [ $? -ne 0 ] 
then
  echo "Error while updating the server."
fi

sudo apt-get install build-essential
sudo apt-get install libssl-dev
sudo apt-get install -y libxml2-dev 
sudo apt-get install -y libxslt1-dev
sudo apt-get install -y libevent-dev 
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

folder=`echo $HOST | cut -d. -f1`
mkdir $folder

echo "done."

