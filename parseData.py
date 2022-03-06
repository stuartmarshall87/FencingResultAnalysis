from inspect import BoundArguments
from math import log2
from unicodedata import category
import requests
from bs4 import BeautifulSoup
import re
import os

import json

class Bout:
    fileName = None
    date = None
    weapon = None
    category = None
    gender = None
    roundId = None    
    aSeed = None
    aName = None
    aScore = None
    bSeed = None
    bName = None
    bScore = None

    def __str__(self):
        return str(self.fileName or '') + ' ' + str(self.date or '') + ' ' + str(self.gender or '') + ' ' + str(self.category or '') + ' ' + str(self.weapon or '') + ' | Round of ' + str(self.roundId) + ' | ' + str(self.aSeed or '') + ' ' + str(self.aName or '') + ' vs ' + str(self.bSeed or '') + ' ' +str(self.bName  or '') + '(' + str(self.aScore) + '-' + str(self.bScore) + ')'

    def to_json(self):
        return json.dumps(self, default=lambda obj: obj.__dict__)

class Fencer:    
    def __init__(self, seed, name):
        self.seed = seed
        self.name = name
    
    def __str__(self):
        return self.seed + ' | ' + self.name


def getCategoryName(categoryAndGender):    
    if categoryAndGender == "oa": return 'Open A'
    if categoryAndGender == "ob": return 'Open B'
    if categoryAndGender == "ca": return 'Cadet A'
    if categoryAndGender == "cb": return 'Cadet B'
    if categoryAndGender == "o": return 'Open'
    if categoryAndGender == "i": return 'Intermediate'
    if categoryAndGender == "n": return 'Novice'
    if categoryAndGender == "ot": return 'Open Teams'
    if categoryAndGender == "u9": return 'U9'
    if categoryAndGender == "u11": return 'U11'
    if categoryAndGender == "u13": return 'U13'
    if categoryAndGender == "u13t": return 'U13 Teams'
    if categoryAndGender == "u14t": return 'U14 Teams'
    if categoryAndGender == "t": return 'Teams'
    if categoryAndGender == "u15": return 'U15'
    if categoryAndGender == "u1720": return 'U17/U20'
    if categoryAndGender == "v": return 'Veterans'
    if categoryAndGender == "yi": return 'Youth Intermediate'
    if categoryAndGender == "vt": return 'Veteran Teams'
    return None

def getWeaponName(weapon):
    if weapon == 'e' : return 'Epee'
    if weapon == 's' : return 'Sabre'
    if weapon == 'f' : return 'Foil'

def getGenderName(gender):
    if gender == 'm' : return 'Mens'
    if gender == 'f' : return 'Womens'
    return 'Mixed'

def readFile(filePath):
    file = open(filePath)
    htmlText = file.read()
    soup = BeautifulSoup(htmlText, 'html.parser')

    if soup.html.get('xmlns:ft') == 'http://www.fencingtime.com':
        return readFencingTime(filePath)
    return []

        
def readFencingTime(filePath):
    file = open(filePath)
    htmlText = file.read()
    soup = BeautifulSoup(htmlText, 'html.parser')

    fileName = os.path.basename(filePath)
    fileName = os.path.splitext(fileName)[0]
    date = fileName[0:8]
    weapon = getWeaponName(fileName[-1].lower())
    categoryAndGender = fileName[8:-1]
    category = getCategoryName(categoryAndGender.lower())
    gender = None
    if category == None:
        gender = getGenderName(categoryAndGender[-1].lower())
        categoryAndGender = categoryAndGender[0:-1]
        category = getCategoryName(categoryAndGender.lower())

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
            bout.fileName = fileName
            bout.roundId = maxSeed
            bout.aSeed = highSeed
            bout.bSeed = maxSeed - highSeed + 1
            bout.date = date
            bout.category = category
            bout.gender = gender
            bout.weapon = weapon
            bouts.append(bout)
        
    # Find fencers
    for bout in bouts:
        colIndex = colCount - int(log2(bout.roundId)) - 1
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
        colIndex = colCount - int(log2(bout.roundId))
        rows = table.findAll('tr')
        for rowIndex in range(len(rows)):
            row = rows[rowIndex]
            cell = row.findAll('td')[colIndex]
            cellClass = cell.get('class')
            if cellClass is not None and 'tableauNameCell' in cellClass:
                winnerName = str(cell.find('span', {'class': 'tableauCompName'}).text)

                if bout.aName == winnerName or bout.bName == winnerName:
                    rowIndex = rowIndex + 1
                    row = rows[rowIndex]
                    cell = row.findAll('td')[colIndex]
                    scores = cell.text
                    
                    scores = cell.text.replace('Â', '')
                    scores = scores.strip()
                    if 'Ref:' in scores:
                        scores = scores[0: scores.index('Ref:')]
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
    return bouts

bouts = []
directories = [
    'D:\\Business\\FSAResults\\FencingSAResults\\2021',
    'D:\\Business\\FSAResults\\FencingSAResults\\2020'
    ]

for directoryPath in directories:
    files = os.listdir(directoryPath)
    for file in files:
        if file.endswith(".htm"):
           bouts = bouts + readFile(directoryPath + '\\' + file)

json_string = json.dumps([ob.__dict__ for ob in bouts])
with open("D:\\Business\\FSAAnalysis\\file.json", "w") as file:
    file.write(json_string)
