# -*- coding: utf-8 -*-
"""
Created on Mon Feb 18 21:31:16 2019

@author: Martin
"""

import json
import os
import magic

folderPath = r'C:\Users\Martin\Desktop\exodus-exports\exodus-report-SAFE-2019-02-18_21-10-51\v1\txs'
filePath = os.path.join(folderPath, 'bitcoin.json')
print(filePath)

with open(filePath, "r") as read_file:
    data = json.load(read_file)


exchange = []
for tx in data:
    if 'toCoin' in tx:
        exchange.append(tx)

