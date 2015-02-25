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
if [ -d ToyFramework ]
then
  echo "ToyFramework folder already exists."
else
  git clone https://github.com/prashantchhabra89/ToyFramework.git
fi

echo "Done."