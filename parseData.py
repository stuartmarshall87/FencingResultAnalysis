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

class CompInfo:
    date = None
    weapon = None    
    category = None
    gender = None

def getCategoryName(categoryCode):
    if categoryCode == "oa": return 'Open A'
    if categoryCode == "ob": return 'Open B'
    if categoryCode == "ca": return 'Cadet A'
    if categoryCode == "cb": return 'Cadet B'
    if categoryCode == "o": return 'Open'
    if categoryCode == "i": return 'Intermediate'
    if categoryCode == "n": return 'Novice'
    if categoryCode == "ot": return 'Open Teams'
    if categoryCode == "u9": return 'U9'
    if categoryCode == "u11": return 'U11'
    if categoryCode == "u13": return 'U13'
    if categoryCode == "u13t": return 'U13 Teams'
    if categoryCode == "u14t": return 'U14 Teams'
    if categoryCode == "t": return 'Teams'
    if categoryCode == "u15": return 'U15'
    if categoryCode == "u1720": return 'U17/U20'
    if categoryCode == "v": return 'Veterans'
    if categoryCode == "yi": return 'Youth Intermediate'
    if categoryCode == "vt": return 'Veteran Teams'
    return None

def getWeaponName(weapon):
    if weapon == 'e' : return 'Epee'
    if weapon == 's' : return 'Sabre'
    if weapon == 'f' : return 'Foil'

def getGenderName(gender):
    if gender == 'm' : return 'Mens'
    if gender == 'f' : return 'Womens'
    if gender == 'w' : return 'Womens'
    if gender == 'b' : return 'Boys'
    if gender == 'g' : return 'Girls'
    return 'Mixed'

def readFile(filePath):
    fileName = os.path.basename(filePath)
    fileName = os.path.splitext(fileName)[0]
    comp = getCompInfo(fileName)
    if comp == None:
        print('Invalid file: ' + fileName)
        return []
    if comp.category is None:
        print('Unknown comp category:' + fileName)
        return []
    elif 'Team' in comp.category:
        return []

    file = open(filePath)
    htmlText = file.read()
    soup = BeautifulSoup(htmlText, 'html.parser')

    if soup.html.get('xmlns:ft') == 'http://www.fencingtime.com':
        return readFencingTime(filePath)
    if soup.find('a', {'href': 'http://betton.escrime.free.fr/index.php/bellepoule'}):
        return readBellepoule(filePath)
    if soup.find('meta', {'content': 'Engarde'}):
        return readEngardeOneFile(filePath)
    if soup.find('table', {'class': 'rankingTable'}):
        return readLanceHolden(filePath)
    else:
        print('Unknown file type')
        return []

def getCompInfo(fileName):
    comp = CompInfo()
    comp.date = fileName[0:8]

    if not str(comp.date).isnumeric():
        return comp

    weaponCode = fileName[-2:].lower()
    if weaponCode == 'ef' or weaponCode == 'ff' or weaponCode == 'sf':
        return comp

    weaponCode = fileName[-1].lower()
    if weaponCode == 'p' or weaponCode == 'r' or weaponCode == 't':
        return comp

    comp.weapon = getWeaponName(fileName[-1].lower())
    categoryAndGender = fileName[8:-1]
    category = getCategoryName(categoryAndGender.lower())
    gender = None
    if category == None:
        genderCode = categoryAndGender[-1].lower()
        if genderCode != 't':
            gender = getGenderName(genderCode)        
            categoryCode = categoryAndGender[0:-1]
            category = getCategoryName(categoryCode.lower())
            comp.gender = gender
            comp.category = category
    else:
        comp.gender = gender
        comp.category = category

    return comp
        
def readFencingTime(filePath):
    fileName = os.path.basename(filePath)
    fileName = os.path.splitext(fileName)[0]
    comp = getCompInfo(fileName)

    file = open(filePath)
    htmlText = file.read()
    soup = BeautifulSoup(htmlText, 'html.parser')
    divs = soup.findAll('div')

    for divIndex in range(len(divs) - 1, 0, -1):
        div = divs[divIndex]
        if '- DE - Scores' in div.text:
            divIndex = divIndex + 1
            break

    div = divs[divIndex]
    table = div.table

    colCount = len(table.findAll('col'))

    bouts = []
    for roundId in range(1, colCount):
        maxSeed = pow(2, roundId)
        for highSeed in range(1, int(maxSeed / 2) + 1):
            bout = Bout()
            bout.fileName = fileName
            bout.roundId = maxSeed
            bout.aSeed = highSeed
            bout.bSeed = maxSeed - highSeed + 1
            bout.date = comp.date
            bout.category = comp.category
            bout.gender = comp.gender
            bout.weapon = comp.weapon
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
                name = str(cell.find('span', {'class': 'tableauCompName'}).text).strip()
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
                winnerName = str(cell.find('span', {'class': 'tableauCompName'}).text).strip()

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

    for bout in bouts:
        bout.aName = extractFencingTimeName(bout.aName)
        bout.bName = extractFencingTimeName(bout.bName)
    bouts = [bout for bout in bouts if bout.bScore != None]
    return bouts

def extractFencingTimeName(name):
    firstName = ''
    lastName = ''
    for part in name.split(' '):
        if part.isupper():
            lastName = lastName + ' ' + part
        else:
            firstName = firstName + ' ' + part
    firstName = firstName.strip().title()
    lastName = lastName.strip().title()
    
    return firstName + ' ' + lastName

def readBellepoule(filePath):
    fileName = os.path.basename(filePath)
    fileName = os.path.splitext(fileName)[0]

    file = open(filePath)
    htmlText = file.read()
    comp = getCompInfo(fileName)

    soup = BeautifulSoup(htmlText, 'html.parser')

    table = soup.find('table', {'class': 'TableTable'})
    headerRow = table.find('tr', {'class': 'TableName'})
    colCount = len(headerRow.findAll('th'))    
    rows = table.find_all('tr')
    bouts = []
    bouts = findBellepouleBoutHistory(table, 1, colCount - 1, 2, len(rows))

    for bout in bouts:
        bout.fileName = fileName
        bout.date = comp.date
        bout.weapon = comp.weapon
        bout.category = comp.category
        bout.gender = comp.gender
    return bouts

def findBellepouleBoutHistory(table, topSeed, colIndex, startRowIndex, endRowIndex):
    if colIndex <= 0:
        return []

    headerRow = table.find('tr', {'class': 'TableName'})
    colCount = len(headerRow.findAll('th'))
    maxSeed = pow(2, colCount - colIndex)
    otherSeed = maxSeed + 1 - topSeed

    bout = Bout()
    bout.roundId = maxSeed
    if topSeed%2 == 1:
        bout.aSeed = topSeed
        bout.bSeed = otherSeed
    else:
        bout.aSeed = otherSeed
        bout.bSeed = topSeed 

    bouts = []
    # Find bout result
    rows = table.find_all('tr')
    for row in rows[startRowIndex:endRowIndex]:
        cells = row.find_all('td')
        cell = cells[colIndex]
        cellClass = cell.get('class')[0]
        if cellClass == 'TableCellFirstCol' or cellClass == 'TableCell' or cellClass == 'TableCellLastCol':
            score = cell.find('span', {'class': 'TableScore'})
            if score is not None:
                # Get bout score
                scores = str(score.text).split('-')
                firstName = cell.find('span', {'class': 'first_name'}).text
                name = cell.find('span', {'class': 'name'}).text
                fullName = str(firstName) + str(name)
                fullName = fullName.strip()
                if scores[0][0] == 'V':
                    if scores[0] == 'V':
                        bout.aScore = 15
                    else:
                        bout.aScore = int(scores[0][1:])
                    bout.aName = fullName
                    bout.bScore = int(scores[1])
                elif scores[1][0] == 'V':                    
                    if scores[1] == 'V':
                        bout.bScore = 15
                    else:
                        bout.bScore = int(scores[1][1:])
                    bout.bName = fullName
                    bout.aScore = int(scores[0])
            else:
                return bouts

    # Get opponent    
    for row in rows[startRowIndex:endRowIndex]:
        cells = row.find_all('td')
        cell = cells[colIndex - 1]
        cellClass = cell.get('class')[0]
        if cellClass == 'TableCellFirstCol' or cellClass == 'TableCell' or cellClass == 'TableCellLastCol':
            firstName = cell.find('span', {'class': 'first_name'}).text
            name = cell.find('span', {'class': 'name'}).text
            otherFullName = str(firstName) + str(name)
            otherFullName = otherFullName.strip()
            if otherFullName != fullName:
                if bout.aName is None:
                    bout.aName = otherFullName
                else:
                    bout.bName = otherFullName

    if bout.aScore == 0 and bout.bScore == 0:
        return bouts

    bouts.append(bout)
    midRowIndex = startRowIndex + round((endRowIndex - startRowIndex) / 2)

    if topSeed%2 == 1:
        newBouts = findBellepouleBoutHistory(table, topSeed, colIndex - 1, startRowIndex, midRowIndex)
        for newBout in newBouts:
            bouts.append(newBout)
        newBouts = findBellepouleBoutHistory(table, otherSeed, colIndex - 1, midRowIndex, endRowIndex)
        for newBout in newBouts:
            bouts.append(newBout)
    else:
        newBouts = findBellepouleBoutHistory(table, otherSeed, colIndex - 1, startRowIndex, midRowIndex)
        for newBout in newBouts:
            bouts.append(newBout)
        newBouts = findBellepouleBoutHistory(table, topSeed, colIndex - 1, midRowIndex, endRowIndex)
        for newBout in newBouts:
            bouts.append(newBout)

    return bouts

def readEngardeOneFile(filePath):
    fileName = os.path.basename(filePath)
    fileName = os.path.splitext(fileName)[0]

    file = open(filePath)
    htmlText = file.read()
    comp = getCompInfo(fileName)

    soup = BeautifulSoup(htmlText, 'html.parser')
    table = soup.find('table', {'class': 'tableau'})
    if table == None:
        return []
    rows = table.find_all('tr')
    bouts = []
    rows = rows[1:]

    rowCount = len(rows)
    colCount = int(round(log2(rowCount))) + 2
    data = np.empty(rowCount * colCount, dtype=object).reshape(rowCount, colCount)

    for rowIndex, row in enumerate(rows):
        columns = row.find_all('td')
        while len(columns) > 0 and columns[-1].text.strip() == '':
            columns = columns[0:-1]
        for colIndex, col in enumerate(columns):
            cellValue = str(col.text.strip())
            if cellValue != '':
                data[rowIndex][colIndex] = cellValue
    
    data = np.delete(data, 2, 1)
    colCount = colCount - 1
    data = np.delete(data, 0, 1)
    colCount = colCount - 1

    bouts = findEngardeBoutHistory(data, 1, colCount - 1, 0, rowCount - 1)

    for bout in bouts:
        bout.fileName = fileName
        bout.date = comp.date
        bout.weapon = comp.weapon
        bout.category = comp.category
        bout.gender = comp.gender

    return bouts

def findEngardeBoutHistory(table, topSeed, colIndex, startRowIndex, endRowIndex):
    bouts = []
    
    for i in range(startRowIndex, endRowIndex):
        fencer = table[i][colIndex]
        if fencer != None:
            nameSplit = fencer.split(' ')
            fencer = nameSplit[1] + ' ' + nameSplit[0][0] + nameSplit[0][1:].lower()
            score = table[i+1][colIndex]

            if score == None:
                break

            # determine seeds
            colCount = table.shape[1]
            roundId = pow(2, colCount - colIndex)
            otherSeed = roundId + 1 - topSeed

            splitScore = score.split('/')            
            if len(splitScore) == 2:
            
                # Found a bout
                bout = Bout()
                bout.roundId = roundId
                bout.aName = fencer
                bout.aScore = splitScore[0]
                bout.bScore = splitScore[1]
                
                if topSeed%2 == 1:
                    bout.aSeed = topSeed
                    bout.bSeed = otherSeed
                else:
                    bout.aSeed = otherSeed
                    bout.bSeed = topSeed

                # Find bName
                for j in range(startRowIndex, i, 1):
                    opponentName = table[j][colIndex-1]
                    if opponentName != None:
                        nameSplit = opponentName.split(' ')
                        if len(nameSplit) > 1:
                            opponentName = nameSplit[1] + ' ' + nameSplit[0][0] + nameSplit[0][1:].lower()
                            if opponentName != bout.aName and len(str(opponentName).split('/')) == 1:
                                bout.bName = opponentName
                                break

                if bout.bName == None:
                    for j in range(i, endRowIndex, 1):
                        opponentName = table[j][colIndex-1]
                        if opponentName != None:
                            nameSplit = opponentName.split(' ')
                            if len(nameSplit) > 1:
                                opponentName = nameSplit[1] + ' ' + nameSplit[0][0] + nameSplit[0][1:].lower()
                                if opponentName != bout.aName:
                                    bout.bName = opponentName
                                    break

                bouts.append(bout)
            
            midRowIndex = startRowIndex + round((endRowIndex - startRowIndex) / 2)
            if topSeed%2 == 1:
                newBouts = findEngardeBoutHistory(table, topSeed, colIndex - 1, startRowIndex, midRowIndex)
                for newBout in newBouts:
                    bouts.append(newBout)
                newBouts = findEngardeBoutHistory(table, otherSeed, colIndex - 1, midRowIndex, endRowIndex)
                for newBout in newBouts:
                    bouts.append(newBout)
            else:
                newBouts = findEngardeBoutHistory(table, otherSeed, colIndex - 1, startRowIndex, midRowIndex)
                for newBout in newBouts:
                    bouts.append(newBout)
                newBouts = findEngardeBoutHistory(table, topSeed, colIndex - 1, midRowIndex, endRowIndex)
                for newBout in newBouts:
                    bouts.append(newBout)

            break

    return bouts

# Custom format defined by Lance Holden
def readLanceHolden(filePath):
    fileName = os.path.basename(filePath)
    fileName = os.path.splitext(fileName)[0]

    file = open(filePath)
    htmlText = file.read()
    comp = getCompInfo(fileName)

    soup = BeautifulSoup(htmlText, 'html.parser')
    tables = soup.find_all('table')
    table = soup.find('table')
    for t in tables:
        if not t.has_attr('class'):
            table = t
            break
    
    rows = table.find_all('tr')
    noColumns = len(rows[0].find_all('td'))
    bouts = findLanceHoldenBoutHistory(table, 1, noColumns - 1, 0, len(rows))
    for bout in bouts:
        bout.fileName = fileName
        bout.date = comp.date
        bout.weapon = comp.weapon
        bout.category = comp.category
        bout.gender = comp.gender
    return bouts

class LHResult:
    winnerName: str
    winnerScore: int
    loserScore: int

def findLanceHoldenBoutHistory(table, topSeed, colIndex, startRowIndex, endRowIndex):
    if colIndex <= 1:
        return []
    rows = table.find_all('tr')
    bouts = []
    for rowIndex in range(startRowIndex, endRowIndex):
        cells = rows[rowIndex].find_all('td')
        cell = cells[colIndex]
        cellText = cell.text.strip()
        if len(cellText) != 0:
            if '(' not in cellText:
                return bouts
            else:
                # Find winner name and score
                winner = lanceHoldenExtractValues(cellText)
                if winner is None:
                    return bouts

    # determine seeds
    colCount = len(rows[0].find_all('td'))
    roundId = pow(2, colCount - colIndex)
    otherSeed = roundId + 1 - topSeed

    # Found a bout
    bout = Bout()
    bout.roundId = roundId
    
    if topSeed%2 == 1:
        bout.aSeed = topSeed
        bout.bSeed = otherSeed
    else:
        bout.aSeed = otherSeed
        bout.bSeed = topSeed

    # Find loser name
    for rowIndex in range(startRowIndex, endRowIndex):
        cells = rows[rowIndex].find_all('td')
        cell = cells[colIndex - 1]
        cellText = str(cell.text.strip())
        if len(cellText) != 0:
            if '(' not in cellText:
                name = cellText
            else:
                cellDetails = lanceHoldenExtractValues(cellText)
                name = cellDetails.winnerName

            if bout.aName == None:
                bout.aName = name
            else:
                bout.bName = name

    if bout.aName == winner.winnerName:
        bout.aScore = winner.winnerScore
        bout.bScore = winner.loserScore
    else:
        bout.bScore = winner.winnerScore
        bout.aScore = winner.loserScore

    bouts.append(bout)

    # Find previous bouts
    midRowIndex = startRowIndex + round((endRowIndex - startRowIndex) / 2)
    if topSeed%2 == 1:
        newBouts = findLanceHoldenBoutHistory(table, topSeed, colIndex - 1, startRowIndex, midRowIndex)
        for newBout in newBouts:
            bouts.append(newBout)
        newBouts = findLanceHoldenBoutHistory(table, otherSeed, colIndex - 1, midRowIndex, endRowIndex)
        for newBout in newBouts:
            bouts.append(newBout)
    else:
        newBouts = findLanceHoldenBoutHistory(table, otherSeed, colIndex - 1, startRowIndex, midRowIndex)
        for newBout in newBouts:
            bouts.append(newBout)
        newBouts = findLanceHoldenBoutHistory(table, topSeed, colIndex - 1, midRowIndex, endRowIndex)
        for newBout in newBouts:
            bouts.append(newBout)
    return bouts

def lanceHoldenExtractValues(text: str):
    for i in range(0, len(text) - 1):
        charIndex = len(text) - 1 - i
        if (text[charIndex] == '('):
            scoreText = text[charIndex + 1:-1]
            result = LHResult()
            result.winnerName = text[0:charIndex].strip()
            result.winnerScore = scoreText.split('-')[0]
            result.loserScore = scoreText.split('-')[1]
            return result


bouts = []
# 2020+ Fencing Time
# 2018 Bellepoule
# 2017-2018 Engarde 1 File
# 2014-2017 Engarde multi files
# 2005-2013 LH
directories = [    
    'C:\\Code\\FencingSAResults2\\2013',
    'C:\\Code\\FencingSAResults2\\2014',
    'C:\\Code\\FencingSAResults2\\2015',
    'C:\\Code\\FencingSAResults2\\2016',
    'C:\\Code\\FencingSAResults2\\2017',
    'C:\\Code\\FencingSAResults2\\2018',
    'C:\\Code\\FencingSAResults2\\2019',
    'C:\\Code\\FencingSAResults2\\2020',
    'C:\\Code\\FencingSAResults2\\2021',
    'C:\\Code\\FencingSAResults2\\2022'
    ]

for directoryPath in directories:
    files = os.listdir(directoryPath)
    hashes = []

    for file in files:
        if not file.endswith(".htm") and not file.endswith('.html'):
            continue

        try:
            path = directoryPath + '\\' + file
            hash = hashlib.md5(open(path,'rb').read()).hexdigest()
            if hash in hashes:
                continue

            hashes.append(hash)
            bouts = bouts + readFile(path)
        except BaseException as err:
            print('Error ' + file)
            print(err)
            raise
        
with open(".\\nameLinks.json") as json_file:
    nameLinks = json.load(json_file)

for bout in bouts:
    if bout.aName in nameLinks:
        bout.aName = nameLinks[bout.aName]
    if bout.bName in nameLinks:
        bout.bName = nameLinks[bout.bName]

json_string = json.dumps([ob.__dict__ for ob in bouts])
with open(".\\bouts.json", "w") as file:
    file.write(json_string)
