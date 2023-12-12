# -*- coding: utf-8 -*-
"""
Created on 29.11.2020

@author: Martin
"""

import pandas
import requests
import koalafolio.PcpCore.settings as settings

blockdaemonBaseURL = "https://svc.blockdaemon.com/"
cardanoBaseURL = blockdaemonBaseURL + "reporting/staking/v1/cardano/mainnet/delegator/history/"

def getCardanoRewardsForAddress(apikey: str, address: str, start: int, end: int) -> pandas.DataFrame:
    payload = {
        "fromTime": int(start),
        "toTime": int(end),
        "timeUnit": "epoch"
    }

    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "X-API-Key": apikey
    }

    response = requests.post(cardanoBaseURL + str(address), json=payload, headers=headers)
    rewards = response.json()['rewards']

    return pandas.DataFrame.from_dict(rewards)
