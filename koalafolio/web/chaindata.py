# -*- coding: utf-8 -*-
"""
Created on 29.11.2020

@author: Martin
"""
from pandas import DataFrame
import koalafolio.gui.helper.QLogger as logger
from datetime import datetime
import requests, pytz

localLogger = logger.globalLogger

class ChainReward:
    def __init__(self, stake_address:str=None, epoch_no:int=None,
                 amount:float=None, chain:str=None, currency:str=None, datetime:datetime=None):
        self.stake_address = stake_address
        self.epoch_no = epoch_no
        self.amount = amount
        self.chain = chain
        self.currency = currency
        self.datetime = datetime

    def toDict(self) -> dict:
        return {
            "stake_address": self.stake_address,
            "epoch_no": self.epoch_no,
            "amount": self.amount,
            "chain": self.chain,
            "currency": self.currency,
            "datetime": self.datetime
        }

    def fromDict(self, dict):
        self.stake_address = dict["stake_address"]
        self.epoch_no = dict["epoch_no"]
        self.amount = dict["amount"]
        self.chain = dict["chain"]
        self.currency = dict["currency"]
        self.datetime = dict["datetime"]

    def __str__(self):
        return str(self.toDict())


# class ChainRewardApi:
#     BASE_URL = ""
#     SUPPORTED_CHAINS = []
#     apiBaseURLs = {}
#
#     @classmethod
#     def getRewardHistory(cls, stake_addresses: list, chain: str,
#                          start:int=None, end:int=None, apikey:str=None) -> list[ChainReward]:
#         raise NotImplementedError("not Implement in base class")

# KOIOS API for Cardano
class KoiosApi:
    KOIOS_BASE_URL = "https://api.koios.rest/api/v1/"
    SUPPORTED_CHAINS = [
        "cardano"
    ]
    CHAIN_CURRENCIES = {
        "cardano": "ADA"
    }
    rewardHistoryApi = KOIOS_BASE_URL + "account_reward_history"
    epochInfoApi = KOIOS_BASE_URL + "epoch_info"

    @classmethod
    def getApiName(cls) -> str:
        return "Koios"

    @classmethod
    def getRewardHistory(cls, stake_addresses: list, chain:str="cardano",
                         start:int=None, end:int=None, apikey:str=None) -> list[ChainReward]:
        rewards = []
        epochTimestamps = cls._getEpochTimestamps()
        payload = {
            "_stake_addresses": stake_addresses
        }
        headers = {
            "accept": "application/json",
            "content-type": "application/json"
        }
        response = requests.post(cls.rewardHistoryApi, json=payload, headers=headers)
        if response.status_code == 200:
            # returns list of dicts with keys
            # stake_address, earned_epoch, spendable_epoch, amount, type, pool_id_bech32
            for reward in response.json():
                try:
                    timestamp = epochTimestamps[reward["earned_epoch"]]
                except KeyError:
                    localLogger.error(f"no timestamp found for epoch {reward['earned_epoch']}")
                    continue
                rewards.append(ChainReward(stake_address=reward["stake_address"],
                                           epoch_no=(reward["earned_epoch"]),
                                           amount=int(reward["amount"])/1000000,
                                           chain=chain,
                                           currency=cls.CHAIN_CURRENCIES[chain],
                                           datetime=datetime.fromtimestamp(timestamp, tz=pytz.UTC)))
        else:
            localLogger.error("no data returned from Koios: " + str(response.status_code))

        # filter by timestamp
        if start is not None:
            rewards = [reward for reward in rewards if reward.datetime.timestamp() >= start]
            if end is not None:
                rewards = [reward for reward in rewards if reward.datetime.timestamp() <= end]

        return rewards

    @classmethod
    def _getEpochTimestamps(cls) -> dict:
        epochTimestamps = {}
        headers = {
            "accept": "application/json"
        }
        response = requests.get(cls.epochInfoApi, headers=headers)
        if response.status_code == 200:
            # response dict with keys
            # start_time, end_time, epoch_no,
            # active_stake, avg_blk_reward, blk_count,
            # fees, first_block_time, last_block_time, out_sum, total_rewards, tx_count
            for epoch in response.json():
                epochTimestamps[epoch["epoch_no"]] = int(epoch["end_time"])
            return epochTimestamps
        else:
            localLogger.error("no data returned from Koios: " + str(response.status_code))
            return None


# All Reward Apis
class ChaindataApis:
    SUPPORTED_CHAINS = [
        "cardano"
    ]
    chainRewardApis = {
        "cardano": KoiosApi
    }
    isApiKeyRequired = {
        "cardano": False
    }

    @classmethod
    def getRewardHistory(cls, apiname: str, addresses: list,
                         start: int, end: int,
                         apikey: str=None) -> DataFrame:
        if cls.isApiKeyRequired[apiname]:
            if apikey is None:
                localLogger.error(f"no apikey provided for api {apiname}")
                return DataFrame()
        rewards = cls.chainRewardApis[apiname].getRewardHistory(stake_addresses=addresses,
                                                                start=start, end=end,
                                                                apikey=apikey)

        return DataFrame.from_records([reward.toDict() for reward in rewards])


