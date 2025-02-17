#!/usr/bin/env python

import os
from glob import glob
import json
import pandas
import datetime

here = os.path.dirname(os.path.abspath(__file__))
folder = os.path.basename(here)
latest = '%s/latest' % here
year = datetime.datetime.today().year

output_data = os.path.join(here, 'data-latest.tsv')
output_year = os.path.join(here, 'data-%s.tsv' % year)

# Don't continue if we don't have latest folder
if not os.path.exists(latest):
    print('%s does not have parsed data.' % folder)
    sys.exit(0)

# Don't continue if we don't have results.json
results_json = os.path.join(latest, 'records.json')
if not os.path.exists(results_json):
    print('%s does not have results.json' % folder)
    sys.exit(1)

with open(results_json, 'r') as filey:
    results = json.loads(filey.read())

columns = ['charge_code', 
           'price', 
           'description', 
           'hospital_id', 
           'filename', 
           'charge_type']

df = pandas.DataFrame(columns=columns)

# First parse standard charges (doesn't have DRG header)
for result in results:
    filename = os.path.join(latest, result['filename'])
    if not os.path.exists(filename):
        print('%s is not found in latest folder.' % filename)
        continue

    if os.stat(filename).st_size == 0:
        print('%s is empty, skipping.' % filename)
        continue

    charge_type = 'standard'
    if "drg" in filename.lower():
        charge_type = "drg"

    print("Parsing %s" % filename)

    if filename.endswith('csv'):


        # encoding issues
        if "CC_Procedures_Methodist.csv" in filename or "CC_Procedures_TJUH" in filename or "CC_Supplies" in filename:
            with codecs.open(filename, "r", encoding='utf-8-sig', errors='ignore') as filey:
                 lines = filey.readlines()

            # 'Procedure Description,Unit Price\r\n'
            for l in range(1, len(lines)):
                line = lines[l].strip('\n').strip('\r').strip(',')
                description = ','.join(line.split(',')[:-1])
                price = line.split(',')[-1].replace(',','').strip()
                entry = [None,               # charge code
                         price,              # price
                         description,        # description
                         result["hospital_id"],        # hospital_id
                         result['filename'],
                         charge_type]            

        elif charge_type == "drg":
            content = pandas.read_csv(filename)
            content.columns=['MS-DRG','DESCRIPTION','TOTAL1','TOTAL2','Price']
            for row in content.iterrows():
                idx = df.shape[0] + 1
                entry = [row[1]['MS-DRG'],                                # charge code
                         row[1]['Price'].replace('$','').replace(',','').strip(), # price
                         row[1]['DESCRIPTION'],        # description
                         result["hospital_id"],        # hospital_id
                         result['filename'],
                         charge_type]            
                df.loc[idx,:] = entry
           
        # ['Generic Name', 'National Drug Code', 'Unit Price']
        elif "CC_Medications" in filename:
            content = pandas.read_csv(filename)
            for row in content.iterrows():
                idx = df.shape[0] + 1
                entry = [row[1]['National Drug Code'], # charge code
                         row[1]['Unit Price'],         # price
                         row[1]['Generic Name'],       # description
                         result["hospital_id"],        # hospital_id
                         result['filename'],
                         charge_type]            
                df.loc[idx,:] = entry

        # ['Procedure Description', 'Unit Price']
        else:        
            content = pandas.read_csv(filename)
            for row in content.iterrows():
                idx = df.shape[0] + 1
                entry = [None, # charge code
                         row[1]['Unit Price'],                  # price
                         row[1]['Procedure Description'],       # description
                         result["hospital_id"],                 # hospital_id
                         result['filename'],
                         charge_type]            
                df.loc[idx,:] = entry

# Remove empty rows
df = df.dropna(how='all')

# Save data!
print(df.shape)
df.to_csv(output_data, sep='\t', index=False)
df.to_csv(output_year, sep='\t', index=False)
