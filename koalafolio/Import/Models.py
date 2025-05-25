# -*- coding: utf-8 -*-
import pandas
from typing_extensions import Tuple

import koalafolio.Import.RegexPatterns as pat
import koalafolio.Import.Converter as converter
import koalafolio.PcpCore.core as core

class Importmodel:
    def __init__(self):
        self.modelName = ''
        self.modelHeaders = []
        self.headerRegexNeeded = []
        self.headerRegexAll = []
        self.contentRegexAll = []
        self.modelCallback = None

    def convert(self, matchedHeaderNames: list, dataFrame: pandas.DataFrame) -> Tuple[core.TradeList, core.TradeList, int]:
        if self.modelCallback is None:
            raise NotImplementedError("modelCallback not set")
        return self.modelCallback(matchedHeaderNames, dataFrame)

    def convertDataFrame(self, dataFrame: pandas.DataFrame) -> Tuple[core.TradeList, core.TradeList, int]:
        matchedHeaders, matchedHeaderNames = self.match(dataFrame.columns.tolist())
        return self.convert(matchedHeaderNames, dataFrame)

    def isMatch(self, headers):  # check if all needed Headers are included in CSV Headers
        for headerRegex in self.headerRegexNeeded:
            headerMatch = 0
            for header in headers:
                if headerRegex.match(header):
                    headerMatch = 1
                    break
            if headerMatch == 0:
                return False
        return True

    def match(self, headers):  # match every regexpattern of import model with CSV Headers
        headerMatchs = []
        headerMatchNames = []
        #        headerMatchNamesDict = {}
        #        i = -1
        for headerRegex in self.headerRegexAll:
            #            i += 1
            headerMatch = 0
            headerMatchName = ''
            for header in headers:
                matchTemp = headerRegex.match(header)
                if matchTemp:
                    headerMatch = 1
                    headerMatchName = matchTemp.group(0)
                    #                    headerMatchNamesDict[self.modelHeaders[i]] = headerMatchName
                    break
            headerMatchs.append(headerMatch)
            headerMatchNames.append(headerMatchName)
        return headerMatchs, headerMatchNames


IMPORT_MODEL_LIST = []
index = -1

# %% exodus [DATE,TYPE,OUTAMOUNT,OUTCURRENCY,FEEAMOUNT,FEECURRENCY,OUTTXID,OUTTXURL,INAMOUNT,INCURRENCY,INTXID,INTXURL,ORDERID]
index = index + 1
IMPORT_MODEL_LIST.append(Importmodel())
IMPORT_MODEL_LIST[index].modelName="exodus"
IMPORT_MODEL_LIST[index].modelHeaders = ['DATE', 'TYPE', 'OUTAMOUNT', 'OUTCURRENCY', 'FEEAMOUNT', 'FEECURRENCY',
                                         'OUTTXID', 'OUTTXURL',
                                         'INAMOUNT', 'INCURRENCY', 'INTXID', 'INTXURL', 'ORDERID']
IMPORT_MODEL_LIST[index].headerRegexNeeded = [pat.EXODUS_DATE_REGEX, pat.EXODUS_TYPE_REGEX,
                                              pat.EXODUS_OUTAMOUNT_REGEX, pat.EXODUS_OUTCURRENCY_REGEX,
                                              pat.EXODUS_FEEAMOUNT_REGEX, pat.EXODUS_FEECURRENCY_REGEX,
                                              pat.EXODUS_OUTTXID_REGEX, pat.EXODUS_OUTTXURL_REGEX,
                                              pat.EXODUS_INAMOUNT_REGEX, pat.EXODUS_INCURRENCY_REGEX,
                                              pat.EXODUS_INTXID_REGEX, pat.EXODUS_INTXURL_REGEX,
                                              pat.EXODUS_ORDERID_REGEX]
IMPORT_MODEL_LIST[index].headerRegexAll = IMPORT_MODEL_LIST[index].headerRegexNeeded
IMPORT_MODEL_LIST[index].modelCallback = converter.modelCallback_exodus

# Blockdaemon [currency,return,timeEnd,timeStart,startingBalance,timeAggregation,address,metadata]
index = index + 1
IMPORT_MODEL_LIST.append(Importmodel())
IMPORT_MODEL_LIST[index].modelName="Blockdaemon"
IMPORT_MODEL_LIST[index].modelHeaders = ['currency', 'return', 'timeEnd', 'timeStart', 'startingBalance',
                                         'timeAggregation', 'address', 'metadata']
IMPORT_MODEL_LIST[index].headerRegexNeeded = [pat.BLOCKDAEMON_CURRENCY_REGEX,
                                              pat.BLOCKDAEMON_RETURN_REGEX,
                                              pat.BLOCKDAEMON_TIMEEND_REGEX]
IMPORT_MODEL_LIST[index].headerRegexAll = IMPORT_MODEL_LIST[index].headerRegexNeeded + [
    pat.BLOCKDAEMON_TIMESTART_REGEX,
    pat.BLOCKDAEMON_STARTINGBALANCE_REGEX,
    pat.BLOCKDAEMON_TIMEAGGREGATION_REGEX,
    pat.BLOCKDAEMON_ADDRESS_REGEX,
    pat.BLOCKDAEMON_METADATA_REGEX
]
IMPORT_MODEL_LIST[index].modelCallback = converter.modelCallback_blockdaemon

# kucoin [orderCreatedAt,id,clientOid,symbol,side,type,stopPrice,price,size,dealSize,dealFunds,averagePrice,fee,feeCurrency,remark,tags,orderStatus]
index = index + 1
IMPORT_MODEL_LIST.append(Importmodel())
IMPORT_MODEL_LIST[index].modelName="kucoin"
IMPORT_MODEL_LIST[index].modelHeaders = ['orderCreatedAt', 'id', 'symbol', 'side', 'type', 'stopPrice', 'price', 'size',
                                         'dealSize', 'dealFunds', 'averagePrice', 'fee', 'feeCurrency', 'orderStatus']
IMPORT_MODEL_LIST[index].headerRegexNeeded = [pat.KUCOIN_ORDERCREATEDAT_REGEX, pat.KUCOIN_ID_REGEX,
                                              pat.KUCOIN_SYMBOL_REGEX, pat.KUCOIN_SIDE_REGEX, pat.KUCOIN_TYPE_REGEX,
                                              pat.KUCOIN_STOPPRICE_REGEX,
                                              pat.KUCOIN_PRICE_REGEX, pat.KUCOIN_SIZE_REGEX, pat.KUCOIN_DEALSIZE_REGEX,
                                              pat.KUCOIN_DEALFUNDS_REGEX,
                                              pat.KUCOIN_AVERAGEPRICE_REGEX, pat.KUCOIN_FEE_REGEX,
                                              pat.KUCOIN_FEECURRENCY_REGEX,
                                              pat.KUCOIN_ORDERSTATUS_REGEX]
IMPORT_MODEL_LIST[index].headerRegexAll = IMPORT_MODEL_LIST[index].headerRegexNeeded
IMPORT_MODEL_LIST[index].modelCallback = converter.modelCallback_kucoin

# %% kraken ["txid","ordertxid","pair","time","type","ordertype","price","cost","fee","vol","margin","misc","ledgers"]
index = index + 1
IMPORT_MODEL_LIST.append(Importmodel())
IMPORT_MODEL_LIST[index].modelName="kraken"
IMPORT_MODEL_LIST[index].modelHeaders = ['txid', 'ordertxid', 'pair', 'time', 'type', 'ordertype', 'price', 'cost',
                                         'fee', 'vol', 'margin', 'misc', 'ledgers']
IMPORT_MODEL_LIST[index].headerRegexNeeded = [pat.KRAKEN_TXID_REGEX, pat.KRAKEN_ORDERTXID_REGEX,
                                              pat.KRAKEN_PAIR_REGEX, pat.KRAKEN_TIME_REGEX, pat.KRAKEN_TYPE_REGEX,
                                              pat.KRAKEN_ORDERTYPE_REGEX,
                                              pat.KRAKEN_PRICE_REGEX, pat.KRAKEN_COST_REGEX, pat.KRAKEN_FEE_REGEX,
                                              pat.KRAKEN_VOL_REGEX,
                                              pat.KRAKEN_MARGIN_REGEX, pat.KRAKEN_MISC_REGEX, pat.KRAKEN_LEDGERS_REGEX]
IMPORT_MODEL_LIST[index].headerRegexAll = IMPORT_MODEL_LIST[index].headerRegexNeeded
IMPORT_MODEL_LIST[index].modelCallback = converter.modelCallback_kraken

# %% krakenapi [txid,ordertxid,pair,dtime,type,ordertype,price,cost,fee,vol,margin,misc,postxid,time]
index = index + 1
IMPORT_MODEL_LIST.append(Importmodel())
IMPORT_MODEL_LIST[index].modelName="krakenapi"
IMPORT_MODEL_LIST[index].modelHeaders = ['txid', 'ordertxid', 'pair', 'dtime', 'type', 'ordertype', 'price', 'cost',
                                         'fee', 'vol', 'margin', 'misc', 'postxid', 'time']
IMPORT_MODEL_LIST[index].headerRegexNeeded = [pat.KRAKENAPI_TXID_REGEX, pat.KRAKENAPI_ORDERTXID_REGEX,
                                              pat.KRAKENAPI_PAIR_REGEX, pat.KRAKENAPI_DTIME_REGEX,
                                              pat.KRAKENAPI_TYPE_REGEX, pat.KRAKENAPI_ORDERTYPE_REGEX,
                                              pat.KRAKENAPI_PRICE_REGEX, pat.KRAKENAPI_COST_REGEX,
                                              pat.KRAKENAPI_FEE_REGEX, pat.KRAKENAPI_VOL_REGEX,
                                              pat.KRAKENAPI_MARGIN_REGEX, pat.KRAKENAPI_MISC_REGEX,
                                              pat.KRAKENAPI_POSTXID_REGEX, pat.KRAKENAPI_TIME_REGEX]
IMPORT_MODEL_LIST[index].headerRegexAll = IMPORT_MODEL_LIST[index].headerRegexNeeded
IMPORT_MODEL_LIST[index].modelCallback = converter.modelCallback_krakenapi

# %% krakenledger [txid, refid, time, type, subtype, aclass, asset, amount, fee, balance]
index = index + 1
IMPORT_MODEL_LIST.append(Importmodel())
IMPORT_MODEL_LIST[index].modelName="krakenledger"
IMPORT_MODEL_LIST[index].modelHeaders = ['txid', 'refid', 'time', 'type', 'subtype', 'aclass', 'asset', 'amount', 'fee',
                                         'balance']
IMPORT_MODEL_LIST[index].headerRegexNeeded = [pat.KRAKENLEDGER_TXID_REGEX, pat.KRAKENLEDGER_REFID_REGEX,
                                              pat.KRAKENLEDGER_TIME_REGEX, pat.KRAKENLEDGER_TYPE_REGEX,
                                              pat.KRAKENLEDGER_SUBTYPE_REGEX, pat.KRAKENLEDGER_ACLASS_REGEX,
                                              pat.KRAKENLEDGER_ASSET_REGEX, pat.KRAKENLEDGER_AMOUNT_REGEX,
                                              pat.KRAKENLEDGER_FEE_REGEX, pat.KRAKENLEDGER_BALANCE_REGEX]
IMPORT_MODEL_LIST[index].headerRegexAll = IMPORT_MODEL_LIST[index].headerRegexNeeded
IMPORT_MODEL_LIST[index].modelCallback = converter.modelCallback_krakenledger

# %% binance ['Date(UTC)', 'Market', 'Type', 'Price', 'Amount', 'Total', 'Fee', 'Fee Coin']
index = index + 1
IMPORT_MODEL_LIST.append(Importmodel())
IMPORT_MODEL_LIST[index].modelName="binance"
IMPORT_MODEL_LIST[index].modelHeaders = ['Date', 'Market', 'Type', 'Price', 'Amount', 'Total', 'Fee', 'Fee Coin']
IMPORT_MODEL_LIST[index].headerRegexNeeded = [pat.BINANCE_DATE_REGEX, pat.BINANCE_MARKET_REGEX,
                                              pat.BINANCE_TYPE_REGEX, pat.BINANCE_PRICE_REGEX, pat.BINANCE_AMOUNT_REGEX,
                                              pat.BINANCE_TOTAL_REGEX,
                                              pat.BINANCE_FEE_REGEX, pat.BINANCE_FEECOIN_REGEX]
IMPORT_MODEL_LIST[index].headerRegexAll = IMPORT_MODEL_LIST[index].headerRegexNeeded
IMPORT_MODEL_LIST[index].modelCallback = converter.modelCallback_binance

# %% poloniex model ['Date', 'Market', 'Category', 'Type', 'Price', 'Amount', 'Total', 'Fee', 'Order Number', 'Base Total Less Fee', 'Quote Total Less Fee']
index = index + 1
IMPORT_MODEL_LIST.append(Importmodel())
IMPORT_MODEL_LIST[index].modelName="poloniex"
IMPORT_MODEL_LIST[index].modelHeaders = ['Date', 'Market', 'Category', 'Type', 'Price', 'Amount', 'Total', 'Fee',
                                         'Order Number', 'Base Total Less Fee', 'Quote Total Less Fee']
IMPORT_MODEL_LIST[index].headerRegexNeeded = [pat.POLONIEX_DATE_REGEX, pat.POLONIEX_MARKET_REGEX,
                                              pat.POLONIEX_CATEGORY_REGEX,
                                              pat.POLONIEX_TYPE_REGEX, pat.POLONIEX_PRICE_REGEX,
                                              pat.POLONIEX_AMOUNT_REGEX, pat.POLONIEX_TOTAL_REGEX,
                                              pat.POLONIEX_FEE_REGEX, pat.POLONIEX_ORDERNUMBER_REGEX,
                                              pat.POLONIEX_BASETOTALLESSFEE_REGEX, pat.POLONIEX_QUOTETOTALLESSFEE_REGEX]
IMPORT_MODEL_LIST[index].headerRegexAll = IMPORT_MODEL_LIST[index].headerRegexNeeded
IMPORT_MODEL_LIST[index].modelCallback = converter.modelCallback_poloniex

# %% model bittrex [Uuid	Exchange	TimeStamp	OrderType	Limit	Quantity	QuantityRemaining	Commission	Price	PricePerUnit	IsConditional	Condition	ConditionTarget	ImmediateOrCancel	Closed]
index = index + 1
IMPORT_MODEL_LIST.append(Importmodel())
IMPORT_MODEL_LIST[index].modelName="bittrex"
IMPORT_MODEL_LIST[index].modelHeaders = ['Uuid', 'Exchange', 'TimeStamp', 'OrderType', 'Limit', 'Quantity',
                                         'QuantityRemaining', 'Commission', 'Price', 'PricePerUnit', 'IsConditional',
                                         'Condition', 'ConditionTarget', 'ImmediateOrCancel', 'Closed']
IMPORT_MODEL_LIST[index].headerRegexNeeded = [pat.BITTREX_UUID_REGEX, pat.BITTREX_EXCHANGE_REGEX,
                                              pat.BITTREX_TIMESTAMP_REGEX, pat.BITTREX_ORDERTYPE_REGEX,
                                              pat.BITTREX_LIMIT_REGEX, pat.BITTREX_QUANTITY_REGEX,
                                              pat.BITTREX_QUANTITYREMAINING_REGEX, pat.BITTREX_COMMISSION_REGEX,
                                              pat.BITTREX_PRICE_REGEX, pat.BITTREX_PRICEPERUNIT_REGEX,
                                              pat.BITTREX_ISCONDITIONAL_REGEX, pat.BITTREX_CONDITION_REGEX,
                                              pat.BITTREX_CONDITIONTARGET_REGEX, pat.BITTREX_IMMEDIATEORCANCEL_REGEX,
                                              pat.BITTREX_CLOSED_REGEX]
IMPORT_MODEL_LIST[index].headerRegexAll = IMPORT_MODEL_LIST[index].headerRegexNeeded
IMPORT_MODEL_LIST[index].modelCallback = converter.modelCallback_bittrex

# %% model 0: Date, Type, Pair, Average Price, Amount, (ID), (Total), (Fee), (FeeCoin), (State), (ExchangeName)
index = index + 1
IMPORT_MODEL_LIST.append(Importmodel())
IMPORT_MODEL_LIST[index].modelName="model 0"
IMPORT_MODEL_LIST[index].modelHeaders = ['date', 'type', 'pair', 'price_average', 'amount', 'id', 'price_total', 'fee',
                                         'feeCoin', 'state', 'exchangeName']
IMPORT_MODEL_LIST[index].headerRegexNeeded = [pat.DATE_REGEX, pat.TYPE_REGEX, pat.PAIR_REGEX_0,
                                              pat.PRICE_AVERAGE_REGEX_0, pat.AMOUNT_SUB_REGEX_0]
IMPORT_MODEL_LIST[index].headerRegexAll = IMPORT_MODEL_LIST[index].headerRegexNeeded + [pat.ID_REGEX,
                                                                                        pat.AMOUNT_MAIN_REGEX_0,
                                                                                        pat.FEE_REGEX,
                                                                                        pat.FEECOIN_REGEX,
                                                                                        pat.STATUS_REGEX,
                                                                                        pat.EXCHANGE_REGEX]
IMPORT_MODEL_LIST[index].modelCallback = converter.modelCallback_0

# %% model 1: Date, Type, Exchange, Average Price, Amount, (ID), (Total), (Fee), (FeeCoin)
index = index + 1
IMPORT_MODEL_LIST.append(Importmodel())
IMPORT_MODEL_LIST[index].modelName="model 1"
IMPORT_MODEL_LIST[index].modelHeaders = ['date', 'type', 'exchange', 'price_average', 'amount', 'id', 'price_total',
                                         'fee', 'feeCoin']
IMPORT_MODEL_LIST[index].headerRegexNeeded = [pat.DATE_REGEX, pat.TYPE_REGEX, pat.PAIR_REGEX_1,
                                              pat.PRICE_AVERAGE_REGEX_1, pat.AMOUNT_SUB_REGEX_1]
IMPORT_MODEL_LIST[index].headerRegexAll = IMPORT_MODEL_LIST[index].headerRegexNeeded + [pat.ID_REGEX,
                                                                                        pat.AMOUNT_MAIN_REGEX_1,
                                                                                        pat.FEE_REGEX,
                                                                                        pat.FEECOIN_REGEX]
IMPORT_MODEL_LIST[index].modelCallback = converter.modelCallback_1

# %% model 2: Date, Type, Pair, Amount sub, Amount main, (id), (fee), (feecoin)
index = index + 1
IMPORT_MODEL_LIST.append(Importmodel())
IMPORT_MODEL_LIST[index].modelName="model 2"
IMPORT_MODEL_LIST[index].modelHeaders = ['date', 'type', 'pair', 'amount_sub', 'amount_main', 'id', 'fee', 'feeCoin']
IMPORT_MODEL_LIST[index].headerRegexNeeded = [pat.DATE_REGEX, pat.TYPE_REGEX, pat.PAIR_REGEX_2, pat.AMOUNT_SUB_REGEX_2,
                                              pat.AMOUNT_MAIN_REGEX_2]
IMPORT_MODEL_LIST[index].headerRegexAll = IMPORT_MODEL_LIST[index].headerRegexNeeded + [pat.ID_REGEX, pat.FEE_REGEX,
                                                                                        pat.FEECOIN_REGEX]
IMPORT_MODEL_LIST[index].modelCallback = converter.modelCallback_2

# %% model 3: Date, type, Coin, Amount, (id), (fee)
index = index + 1
IMPORT_MODEL_LIST.append(Importmodel())
IMPORT_MODEL_LIST[index].modelName="model 3"
IMPORT_MODEL_LIST[index].modelHeaders = ['date', 'type', 'coin', 'amount', 'id', 'fee']
IMPORT_MODEL_LIST[index].headerRegexNeeded = [pat.DATE_REGEX, pat.TYPE_REGEX, pat.COIN_REGEX_3, pat.AMOUNT_REGEX_3]
IMPORT_MODEL_LIST[index].headerRegexAll = IMPORT_MODEL_LIST[index].headerRegexNeeded + [pat.ID_REGEX, pat.FEE_REGEX]
IMPORT_MODEL_LIST[index].modelCallback = converter.modelCallback_3

# %% model 4 (bitcoin.de): Date, Type, Pair, amount_main_wo, amount_sub_wo, amount_main_w_fees, amount_sub_w_fees, (ID), (ZuAbgang)
index = index + 1
IMPORT_MODEL_LIST.append(Importmodel())
IMPORT_MODEL_LIST[index].modelName="model 4"
IMPORT_MODEL_LIST[index].modelHeaders = ['date', 'type', 'pair', 'amount_main_wo_fee', 'amount_sub_wo_fee',
                                         'amount_main_w_fee', 'amount_main_w_fee_fidor', 'amount_sub_w_fee', 'id']
IMPORT_MODEL_LIST[index].headerRegexNeeded = [pat.DATE_REGEX, pat.TYPE_REGEX, pat.BITCOIN_PAIR_REGEX_4,
                                              pat.AMOUNT_MAIN_WO_FEE_REGEX_4, pat.AMOUNT_SUB_WO_FEE_REGEX_4,
                                              pat.AMOUNT_MAIN_W_FEE_REGEX_4, pat.AMOUNT_SUB_W_FEE_REGEX_4]
IMPORT_MODEL_LIST[index].headerRegexAll = \
    IMPORT_MODEL_LIST[index].headerRegexNeeded + [pat.ID_REGEX, pat.AMOUNT_ZUABGANG_REGEX_4,
                                                  pat.AMOUNT_MAIN_W_FEE_FIDOR_REGEX_4,
                                                  pat.BITCOINDE_EINHEIT_AMOUNT_MAIN_WO_FEE_REGEX,
                                                  pat.BITCOINDE_EINHEIT_AMOUNT_MAIN_W_FEE_REGEX,
                                                  pat.BITCOINDE_EINHEIT_KURS_REGEX]
IMPORT_MODEL_LIST[index].modelCallback = converter.modelCallback_4

# %% model 5: Date, Pair, Average Price, Amount, (ID), (Total), (Fee), (FeeCoin), (State)
index = index + 1
IMPORT_MODEL_LIST.append(Importmodel())
IMPORT_MODEL_LIST[index].modelName="model 5"
IMPORT_MODEL_LIST[index].modelHeaders = ['date', 'pair', 'price_average', 'amount', 'id', 'price_total', 'fee',
                                         'feeCoin', 'state']
IMPORT_MODEL_LIST[index].headerRegexNeeded = [pat.DATE_REGEX, pat.PAIR_REGEX_5, pat.PRICE_AVERAGE_REGEX_5,
                                              pat.AMOUNT_SUB_REGEX_5]
IMPORT_MODEL_LIST[index].headerRegexAll = IMPORT_MODEL_LIST[index].headerRegexNeeded + [pat.ID_REGEX,
                                                                                        pat.AMOUNT_MAIN_REGEX_5,
                                                                                        pat.FEE_REGEX,
                                                                                        pat.FEECOIN_REGEX,
                                                                                        pat.STATUS_REGEX]
IMPORT_MODEL_LIST[index].modelCallback = converter.modelCallback_5

# %% model template1: "date","type","buy amount","buy cur","sell amount","sell cur",("exchange"),("fee amount"),("fee currency"),("wallet")
index = index + 1
IMPORT_MODEL_LIST.append(Importmodel())
IMPORT_MODEL_LIST[index].modelName="model t1"
IMPORT_MODEL_LIST[index].modelName = 'Template1'
IMPORT_MODEL_LIST[index].modelHeaders = ['DATE', 'TYPE', 'BUY_AMOUNT', 'BUY_CUR', 'SELL_AMOUNT', 'SELL_CUR',
                                         'EXCHANGE', 'FEE_AMOUNT', 'FEE_CURRENCY', "BUY_WALLET", "SELL_WALLET"]
IMPORT_MODEL_LIST[index].headerRegexNeeded = [pat.TEMPLATE1_DATE_REGEX, pat.TEMPLATE1_TYPE_REGEX,
                                              pat.TEMPLATE1_BUY_AMOUNT_REGEX, pat.TEMPLATE1_BUY_CUR_REGEX,
                                              pat.TEMPLATE1_SELL_AMOUNT_REGEX, pat.TEMPLATE1_SELL_CUR_REGEX]
IMPORT_MODEL_LIST[index].headerRegexAll = IMPORT_MODEL_LIST[index].headerRegexNeeded \
                                          + [pat.TEMPLATE1_EXCHANGE_REGEX, pat.TEMPLATE1_FEE_AMOUNT_REGEX,
                                             pat.TEMPLATE1_FEE_CURRENCY_REGEX, pat.TEMPLATE1_BUY_WALLET_REGEX,
                                             pat.TEMPLATE1_SELL_WALLET_REGEX]
IMPORT_MODEL_LIST[index].modelCallback = converter.modelCallback_Template1

# %% model tradeList: 'date', 'type', 'coin', 'amount', 'id', 'tradePartnerId', 'valueLoaded', 'exchange', 'externId', 'wallet'
index = index + 1
IMPORT_MODEL_LIST.append(Importmodel())
IMPORT_MODEL_LIST[index].modelName="model tradeList"
IMPORT_MODEL_LIST[index].modelHeaders = ['date', 'type', 'coin', 'amount', 'id', 'tradePartnerId',
                                         'valueLaoded', 'exchange', 'externId', 'wallet']
IMPORT_MODEL_LIST[index].headerRegexNeeded = [pat.TRADELIST_DATE_REGEX, pat.TRADELIST_TYPE_REGEX,
                                              pat.TRADELIST_COIN_REGEX, pat.TRADELIST_AMOUNT_REGEX]
IMPORT_MODEL_LIST[index].headerRegexAll = IMPORT_MODEL_LIST[index].headerRegexNeeded \
                                          + [pat.TRADELIST_ID_REGEX, pat.TRADELIST_TRADEPARTNERID_REGEX,
                                             pat.TRADELIST_VALUELOADED_REGEX, pat.TRADELIST_EXCHANGE_REGEX,
                                             pat.TRADELIST_EXTERNID_REGEX, pat.TRADELIST_WALLET_REGEX]
IMPORT_MODEL_LIST[index].modelCallback = converter.modelCallback_TradeList

# %% model CCXT: timestamp, location, pair, trade_type, amount, rate, fee, fee_currency, link
index = index + 1
IMPORT_MODEL_LIST.append(Importmodel())
IMPORT_MODEL_LIST[index].modelName="CCXT"
IMPORT_MODEL_LIST[index].modelName = 'CCXT'
IMPORT_MODEL_LIST[index].modelHeaders = ['timestamp', 'location', 'pair', 'trade_type', 'amount', 'rate',
                                         'fee', 'fee_currency', 'link']
IMPORT_MODEL_LIST[index].headerRegexNeeded = [pat.CCXT_TIMESTAMP_REGEX, pat.CCXT_LOCATION_REGEX, pat.CCXT_PAIR_REGEX,
                                              pat.CCXT_TRADE_TYPE_REGEX, pat.CCXT_AMOUNT_REGEX, pat.CCXT_RATE_REGEX]
IMPORT_MODEL_LIST[index].headerRegexAll = IMPORT_MODEL_LIST[index].headerRegexNeeded + [pat.CCXT_FEE_REGEX,
                                                                                        pat.CCXT_FEE_CURRENCY_REGEX,
                                                                                        pat.CCXT_LINK_REGEX]
IMPORT_MODEL_LIST[index].modelCallback = converter.modelCallback_ccxt
