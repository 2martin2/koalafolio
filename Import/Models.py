# -*- coding: utf-8 -*-

import Import.RegexPatterns as pat
import Import.Converter as converter


class Importmodel:
    def __init__(self):
        self.modelHeaders = []
        self.headerRegexNeeded = []
        self.headerRegexAll = []
        self.contentRegexAll = []
        self.modelCallback = None

    def convertDataFrame(self, dataFrame):
        matchedHeaders, matchedHeaderNames = self.match(dataFrame.columns.tolist())
        return self.modelCallback(matchedHeaderNames, dataFrame)

    def isMatch(self, headers):  # check if all needed Headers are included in CSV Headers
        #        headerMatchs = []
        for headerRegex in self.headerRegexNeeded:
            headerMatch = 0
            for header in headers:
                if headerRegex.match(header):
                    headerMatch = 1
                    break
            if headerMatch == 0:
                return False
        #            headerMatchs.append(headerMatch)
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
IMPORT_MODEL_LIST[index].modelHeaders = ['DATE', 'TYPE', 'OUTAMOUNT', 'OUTCURRENCY', 'FEEAMOUNT', 'FEECURRENCY', 'OUTTXID', 'OUTTXURL',
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

# %% kraken ["txid","ordertxid","pair","time","type","ordertype","price","cost","fee","vol","margin","misc","ledgers"]
index = index + 1
IMPORT_MODEL_LIST.append(Importmodel())
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

# %% binance ['Date(UTC)', 'Market', 'Type', 'Price', 'Amount', 'Total', 'Fee', 'Fee Coin']
index = index + 1
IMPORT_MODEL_LIST.append(Importmodel())
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

# %% model 0: Date, Type, Pair, Average Price, Amount, (ID), (Total), (Fee), (FeeCoin), (State)
index = index + 1
IMPORT_MODEL_LIST.append(Importmodel())
IMPORT_MODEL_LIST[index].modelHeaders = ['date', 'type', 'pair', 'price_average', 'amount', 'id', 'price_total', 'fee',
                                         'feeCoin', 'state']
IMPORT_MODEL_LIST[index].headerRegexNeeded = [pat.DATE_REGEX, pat.TYPE_REGEX, pat.PAIR_REGEX_0,
                                              pat.PRICE_AVERAGE_REGEX_0, pat.AMOUNT_SUB_REGEX_0]
IMPORT_MODEL_LIST[index].headerRegexAll = IMPORT_MODEL_LIST[index].headerRegexNeeded + [pat.ID_REGEX,
                                                                                        pat.AMOUNT_MAIN_REGEX_0,
                                                                                        pat.FEE_REGEX,
                                                                                        pat.FEECOIN_REGEX,
                                                                                        pat.STATUS_REGEX]
IMPORT_MODEL_LIST[index].modelCallback = converter.modelCallback_0

# %% model 1: Date, Type, Exchange, Average Price, Amount, (ID), (Total), (Fee), (FeeCoin)
index = index + 1
IMPORT_MODEL_LIST.append(Importmodel())
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
IMPORT_MODEL_LIST[index].modelHeaders = ['date', 'type', 'pair', 'amount_sub', 'amount_main', 'id', 'fee', 'feeCoin']
IMPORT_MODEL_LIST[index].headerRegexNeeded = [pat.DATE_REGEX, pat.TYPE_REGEX, pat.PAIR_REGEX_2, pat.AMOUNT_SUB_REGEX_2,
                                              pat.AMOUNT_MAIN_REGEX_2]
IMPORT_MODEL_LIST[index].headerRegexAll = IMPORT_MODEL_LIST[index].headerRegexNeeded + [pat.ID_REGEX, pat.FEE_REGEX,
                                                                                        pat.FEECOIN_REGEX]
IMPORT_MODEL_LIST[index].modelCallback = converter.modelCallback_2

# %% model 3: Date, type, Coin, Amount, (id), (fee)
index = index + 1
IMPORT_MODEL_LIST.append(Importmodel())
IMPORT_MODEL_LIST[index].modelHeaders = ['date', 'type', 'coin', 'amount', 'id', 'fee']
IMPORT_MODEL_LIST[index].headerRegexNeeded = [pat.DATE_REGEX, pat.TYPE_REGEX, pat.COIN_REGEX_3, pat.AMOUNT_REGEX_3]
IMPORT_MODEL_LIST[index].headerRegexAll = IMPORT_MODEL_LIST[index].headerRegexNeeded + [pat.ID_REGEX, pat.FEE_REGEX]
IMPORT_MODEL_LIST[index].modelCallback = converter.modelCallback_3

# %% model 4 (bitcoin.de): Date, Type, Pair, amount_main_wo, amount_sub_wo, amount_main_w_fees, amount_sub_w_fees, (ID), (ZuAbgang)
index = index + 1
IMPORT_MODEL_LIST.append(Importmodel())
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

# %% model tradeList: 'date', 'type', 'coin', 'amount', 'id', 'tradePartnerId', 'exchange', 'externId', 'wallet'
index = index + 1
IMPORT_MODEL_LIST.append(Importmodel())
IMPORT_MODEL_LIST[index].modelHeaders = ['date', 'type', 'coin', 'amount', 'id', 'tradePartnerId',
                                         'exchange', 'externId', 'wallet']
IMPORT_MODEL_LIST[index].headerRegexNeeded = [pat.TRADELIST_DATE_REGEX, pat.TRADELIST_TYPE_REGEX,
                                              pat.TRADELIST_COIN_REGEX, pat.TRADELIST_AMOUNT_REGEX]
IMPORT_MODEL_LIST[index].headerRegexAll = IMPORT_MODEL_LIST[index].headerRegexNeeded \
                                          + [pat.TRADELIST_ID_REGEX, pat.TRADELIST_TRADEPARTNERID_REGEX,
                                             pat.TRADELIST_VALUELOADED_REGEX, pat.TRADELIST_EXCHANGE_REGEX,
                                             pat.TRADELIST_EXTERNID_REGEX, pat.TRADELIST_WALLET_REGEX]
IMPORT_MODEL_LIST[index].modelCallback = converter.modelCallback_TradeList