#!/bin/sh

cd $CI_HOME/conpaas-client
python setup.py install

cd $CI_HOME/conpaas-director
python setup.py install
coverage run --source=cpsdirector test.py