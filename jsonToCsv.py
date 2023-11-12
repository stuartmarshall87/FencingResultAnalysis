import pandas as pd

df = pd.read_json('bouts.json')

csv = df.to_csv('bouts.csv', index=False )