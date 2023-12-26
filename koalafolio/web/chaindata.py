# -*- coding: utf-8 -*-
"""
Created on 29.11.2020

@author: Martin
"""

import pandas
import requests
import logger

localLogger = logger.globalLogger

blockdaemonBaseURL = "https://svc.blockdaemon.com/"
apinames = [
    "cardano",
    "ethereum",
    "solana",
    "polkadot",
    "polygon",
    "near",
    "avalanche"
]

# baseURLS
apiBaseURLs = {}
apiBaseURLs["cardano"] = blockdaemonBaseURL + "reporting/staking/v1/cardano/mainnet/delegator/history/"
apiBaseURLs["ethereum"] = blockdaemonBaseURL + "reporting/staking/v1/ethereum/mainnet/validator/history/"
apiBaseURLs["solana"] = blockdaemonBaseURL + "reporting/staking/v1/solana/mainnet/delegator/history/"
apiBaseURLs["polkadot"] = blockdaemonBaseURL + "reporting/staking/v1/polkadot/mainnet/nominator/history/"
apiBaseURLs["polygon"] = blockdaemonBaseURL + "reporting/staking/v1/polygon/mainnet/delegator/history/"
apiBaseURLs["near"] = blockdaemonBaseURL + "reporting/staking/v1/near/mainnet/delegator/history/"
apiBaseURLs["avalanche"] = blockdaemonBaseURL + "reporting/staking/v1/avalanche/mainnet/delegator/history/"

# time format factor, s = 1, ms = 1000, ...
apiTimeFactors = {}
apiTimeFactors["cardano"] = 1
apiTimeFactors["ethereum"] = 1000
apiTimeFactors["solana"] = 1000
apiTimeFactors["polkadot"] = 1000
apiTimeFactors["polygon"] = 1
apiTimeFactors["near"] = 1
apiTimeFactors["avalanche"] = 1

# timeUnit
apiTimeUnits = {}
apiTimeUnits["cardano"] = "epoch"
apiTimeUnits["ethereum"] = "week"
apiTimeUnits["solana"] = "epoch"
apiTimeUnits["polkadot"] = "era"
apiTimeUnits["polygon"] = "epoch"
apiTimeUnits["near"] = "weekly"
apiTimeUnits["avalanche"] = ""


# get data from blockdaemon api:
# apiname from apinames
# apikey for blockdaemon
# address in fromat of given apiname chain
# start timestamp in seconds
# end timestamp in seconds
def getBlockdaemonRewardsForAddress(apiname: str, apikey: str, address: str, start: int, end: int) -> pandas.DataFrame:
    startTimestamp = int(start) * apiTimeFactors[apiname]
    endTimestamp = int(end) * apiTimeFactors[apiname]
    if apiTimeUnits[apiname]:
        payload = {
            "fromTime": startTimestamp,
            "toTime": endTimestamp,
            "timeUnit": apiTimeUnits[apiname]
        }
    else:
        payload = {
            "fromTime": startTimestamp,
            "toTime": endTimestamp
        }

    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "X-API-Key": apikey
    }

    response = requests.post(apiBaseURLs[apiname] + str(address), json=payload, headers=headers)
    try:
        content = response.json()
    except Exception as ex:
        localLogger.error("no data returned from Blockdaemon (" + str(apiname) + "): " + str(ex))
        return pandas.DataFrame()
    if "rewards" in content:
        rewards = content['rewards']
    else:
        rewards = content

    return pandas.DataFrame.from_dict(rewards)
