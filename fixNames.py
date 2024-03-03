import json


# Matches to investigate
#     "Marshall Griffin" : "Michael Griffin",
#     "Beatriz Dal Moro Ferreira" : "Isabela Dal Moro Ferreira",
#     "Madeline Neal" : "Rin Neal",
#     "Karl VATZVIK" : "Karl Vatzlavik",
#     "Rohan Fransic-foale" : "FOALE Francis",
#     "Beatriz DAL MORO FERREIRA" : "Isabela DAL MORO FERREIRA",
#     "Isabela Dal Moro Ferreira" : "Isabela Dal Moro Ferreira",

#     "Michael Chen" : "Mitchell Chen",
#     "Ben Lim" : "Ben Lam",
#     "VRIES De" : "Luke DE VRIES",


with open(".\\bouts.json", "r") as file:
    bouts = json.loads(file.read())

with open(".\\nameLinks.json") as json_file:
    nameLinks = json.load(json_file)

for bout in bouts:
    if bout['aName'] in nameLinks:
        bout['aName'] = nameLinks[bout['aName']]
    if bout['bName'] in nameLinks:
        bout['bName'] = nameLinks[bout['bName']]

json_string = json.dumps(bouts)
with open(".\\bouts.json", "w") as file:
    file.write(json_string)
