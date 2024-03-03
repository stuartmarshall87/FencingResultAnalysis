import json
from thefuzz import fuzz
from thefuzz import process
from collections import Counter

with open(".\\bouts.json", "r") as file:
    bouts = json.loads(file.read())

names = []
for bout in bouts:
    names.append(bout['aName'])
    names.append(bout['bName'])

uniqueNames = [x for x in names]

uniqueNames = [element for element,count in Counter(names).most_common()]
uniqueNames = dict.fromkeys(uniqueNames)
uniqueNames = list(uniqueNames)
uniqueNames.reverse()

count = 0
fixes = []
for i in range(0, len(uniqueNames)):
    name = uniqueNames[i]
    bestResult = 0
    bestMatch = ''
    algorithm = 0
    for j in range(i, len(uniqueNames)):
        innerName = uniqueNames[j]
        if name == innerName:
            continue
        if name.lower() == innerName.lower():
            continue
        result = fuzz.ratio(name, innerName)
        if result > bestResult:
            bestMatch = innerName
            bestResult = result
            algorithm = 1
        result = fuzz.partial_ratio(name, innerName)
        if result > bestResult:
            bestMatch = innerName
            bestResult = result
            algorithm = 2
        result = fuzz.token_sort_ratio(name, innerName)
        if result > bestResult:
            bestMatch = innerName
            bestResult = result
            algorithm = 3
        result = fuzz.token_set_ratio(name, innerName)
        if result > bestResult:
            bestMatch = innerName
            bestResult = result
            algorithm = 4
        result = fuzz.partial_token_sort_ratio(name, innerName)
        if result > bestResult:
            bestMatch = innerName
            bestResult = result
            algorithm = 5

    if bestResult > 80:
        if name.lower() != bestMatch.lower():
            fixes.append('"' + name + '" : "' + bestMatch + '",')
            count = count + 1
fixes.sort()
for fix in fixes:
    print(fix)