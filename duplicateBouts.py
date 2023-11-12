# Reads the bouts.json file, takes each bout in it. Duplicates the bout with reversed values, saves.
import json
import copy
from fileinput import fileno
from importlib.metadata import FileHash
from inspect import _void
from math import log2
from bs4 import BeautifulSoup
import re
import os
import hashlib
import json
import numpy as np


f = open('bouts.json')
 
data = json.load(f)
 
bouts = []
counter = 0
for bout in data:
    bouts.append(bout)
    clone = copy.copy(bout)
    aName = bout.get('aName')
    aScore = bout.get('aScore')
    aSeed = bout['aSeed']
    clone['aName'] = bout.get('bName')
    clone['aScore'] = bout.get('bScore')
    clone['aSeed'] = bout['bSeed']    
    clone['bName'] = aName
    clone['bScore'] = aScore
    clone['bSeed'] = aSeed
    bouts.append(clone)

f.close()


with open(".\\bouts.json", "w") as file:
    file.write(json.dumps(bouts))
