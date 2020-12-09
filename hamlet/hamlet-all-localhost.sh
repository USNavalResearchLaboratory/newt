#!/bin/bash

python workflow.py -a I -s I
python workflow.py -a I -s II
python workflow.py -a I -s III
python workflow.py -a I -s IV
python workflow.py -a I -s V

python workflow.py -a II -s I
python workflow.py -a II -s II

python workflow.py -a III -s I
python workflow.py -a III -s II
python workflow.py -a III -s III
python workflow.py -a III -s IV

python workflow.py -a IV -s I
python workflow.py -a IV -s II
python workflow.py -a IV -s III
python workflow.py -a IV -s IV
python workflow.py -a IV -s V
python workflow.py -a IV -s VI
python workflow.py -a IV -s VII

python workflow.py -a V -s I
python workflow.py -a V -s II

