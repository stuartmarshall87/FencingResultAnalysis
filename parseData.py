from inspect import BoundArguments
from math import log2
import requests
from bs4 import BeautifulSoup
import re

class Bout:
    roundId = None    
    aSeed = None
    aName = None
    aScore = None
    bSeed = None
    bName = None
    bScore = None

    def __str__(self):
        return 'Round of ' + str(self.roundId) + ' | ' + str(self.aSeed or '') + ' ' + str(self.aName or '') + ' vs ' + str(self.bSeed or '') + ' ' +str(self.bName  or '') + '(' + str(self.aScore) + '-' + str(self.bScore) + ')'

class Fencer:    
    def __init__(self, seed, name):
        self.seed = seed
        self.name = name
    
    def __str__(self):
        return self.seed + ' | ' + self.name


f = open(".\\20210228OMF.htm")
html_text = f.read()
soup = BeautifulSoup(html_text, 'html.parser')

divs = soup.findAll('div')

for divIndex in range(len(divs) - 1, 0, -1):
    div = divs[divIndex]
    if '- DE - Scores' in div.text:
        divIndex = divIndex + 1
        break

div = divs[divIndex]
table = div.table

colCount = len(table.findAll('col'))

maxFencers = pow(2, colCount - 1)

bouts = []
for roundId in range(1, colCount):
    maxSeed = pow(2, roundId)
    for highSeed in range(1, int(maxSeed / 2) + 1):
        bout = Bout()
        bout.roundId = maxSeed
        bout.aSeed = highSeed
        bout.bSeed = maxSeed - highSeed + 1
        bouts.append(bout)
    
# Find fencers
for bout in bouts:
    #print(bout.roundId)
    colIndex = colCount - int(log2(bout.roundId)) - 1
    #print(colIndex)
    rows = table.findAll('tr')
    for row in rows:
        cell = row.findAll('td')[colIndex]
        cellClass = cell.get('class')
        if cellClass is not None and 'tableauNameCell' in cellClass:
            resultSeed = int(cell.find('span', {'class': 'tableauSeed'}).text.replace('(', '').replace(')', ''))
            name = str(cell.find('span', {'class': 'tableauCompName'}).text)
            if resultSeed == bout.aSeed:
                bout.aName = name
            if resultSeed == bout.bSeed:
                bout.bName = name

bouts = [bout for bout in bouts if bout.bName != '-BYE-']

scoresRegex = re.compile('[0-9]+ - [0-9]+')               
# Find scores
for bout in bouts:
    #print(bout.roundId)
    colIndex = colCount - int(log2(bout.roundId))
    #print(colIndex)
    rows = table.findAll('tr')
    for rowIndex in range(len(rows)):
        row = rows[rowIndex]
        cell = row.findAll('td')[colIndex]
        cellClass = cell.get('class')
        if cellClass is not None and 'tableauNameCell' in cellClass:
            winnerName = str(cell.find('span', {'class': 'tableauCompName'}).text)

            if bout.aName == winnerName or bout.bName == winnerName:
                #print(winnerName)
                rowIndex = rowIndex + 1
                row = rows[rowIndex]
                cell = row.findAll('td')[colIndex]
                scores = cell.text
                
                scores = cell.text.replace('Â', '')
                scores = scores.strip()
                if len(scores) == 0:
                    continue
                    
                if not re.match(scoresRegex, scores):
                    print(scores)
                    continue

                winnerScore = scores.split(' - ')[0]
                loserScore = scores.split(' - ')[1]

                if bout.aName == winnerName:
                    bout.aScore = winnerScore
                    bout.bScore = loserScore
                else:
                    bout.bScore = winnerScore
                    bout.aScore = loserScore
    
    if not re.match(scoresRegex, scores):
        continue


bouts = [bout for bout in bouts if bout.bScore != None]


for bout in bouts:
    print(bout)
exit()
