INSTALLATION ============

use Virtual wrapper to avoid conflitcs

pip install virtualenvwrapper

export WORKON_HOME=~/Envs
mkdir -p $WORKON_HOME
source /usr/local/bin/virtualenvwrapper.sh
mkvirtualenv newt

pip install netifaces
pip install pyzmq

Install Protolib and MGEN

Download protolib and mgen:
https://github.com/USNavalResearchLaboratory/mgen
https://github.com/USNavalResearchLaboratory/protolib

Compile and install each one

Protolib:

cd protolib
./waf configure --build-python
python setup.py install

MGEN:
cd makefiles
make -f Makefile.YOUR_OS
cd ..
python setup.py install


Then in the root, built newt for use:

python setup.py install

