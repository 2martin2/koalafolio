# -*- coding: utf-8 -*-
"""
Created on 29.11.2020

@author: Martin
"""

from pandas import DataFrame
import koalafolio.gui.helper.QLogger as logger

localLogger = logger.globalLogger

# staic class for static data
class ChaindataStatic:
    BLOCKDAEMON_BASE_URL = "https://svc.blockdaemon.com/"
    SUPPORTED_CHAINS = [
        "cardano",
        "ethereum",
        "solana",
        "polkadot",
        "polygon",
        "near",
        "avalanche"
    ]
    apiBaseURLs = {"cardano": BLOCKDAEMON_BASE_URL + "reporting/staking/v1/cardano/mainnet/delegator/history/",
                   "ethereum": BLOCKDAEMON_BASE_URL + "reporting/staking/v1/ethereum/mainnet/validator/history/",
                   "solana": BLOCKDAEMON_BASE_URL + "reporting/staking/v1/solana/mainnet/delegator/history/",
                   "polkadot": BLOCKDAEMON_BASE_URL + "reporting/staking/v1/polkadot/mainnet/nominator/history/",
                   "polygon": BLOCKDAEMON_BASE_URL + "reporting/staking/v1/polygon/mainnet/delegator/history/",
                   "near": BLOCKDAEMON_BASE_URL + "reporting/staking/v1/near/mainnet/delegator/history/",
                   "avalanche": BLOCKDAEMON_BASE_URL + "reporting/staking/v1/avalanche/mainnet/delegator/history/"}

    # time format factor, s = 1, ms = 1000, ...
    apiTimeFactors = {"cardano": 1, "ethereum": 1000, "solana": 1000, "polkadot": 1000, "polygon": 1, "near": 1,
                      "avalanche": 1}

    # timeUnit
    apiTimeUnits = {"cardano": "epoch", "ethereum": "week", "solana": "epoch", "polkadot": "era", "polygon": "epoch",
                    "near": "weekly", "avalanche": ""}

    @staticmethod
    def getBlockdaemonRewardsForAddress(apiname: str, apikey: str, address: str, start: int,
                                        end: int) -> DataFrame:
        startTimestamp = int(start) * ChaindataStatic.apiTimeFactors[apiname]
        endTimestamp = int(end) * ChaindataStatic.apiTimeFactors[apiname]
        if ChaindataStatic.apiTimeUnits[apiname]:
            payload = {
                "fromTime": startTimestamp,
                "toTime": endTimestamp,
                "timeUnit": ChaindataStatic.apiTimeUnits[apiname]
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

        from requests import post as requests_post
        response = requests_post(ChaindataStatic.apiBaseURLs[apiname] + str(address), json=payload, headers=headers)
        try:
            content = response.json()
        except Exception as ex:
            localLogger.error("no data returned from Blockdaemon (" + str(apiname) + "): " + str(ex))
            return DataFrame()
        if "rewards" in content:
            rewards = content['rewards']
        else:
            rewards = content

        return DataFrame.from_dict(rewards)


