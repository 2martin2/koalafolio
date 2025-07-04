# -*- coding: utf-8 -*-

import re

# %% header patterns
# general
ID_REGEX_PATTERN = r'^((transaction)|(trade)|(order)|())( *|_)((id)|(uuid)|(number)|(nummer)|(referenz))|#$'  # id
DATE_REGEX_PATTERN = r'^((Filled time)|(date.*)|datum|(time(|stamp))|(closed)|(updated)|(tradeCreatedAt))$'  # date
TYPE_REGEX_PATTERN = r'^(((transaction)|(trade)|(order)|())( *|_)((typ(|e))|(side))|(sell/buy))$'  # type
FEE_REGEX_PATTERN = r'^((fee(|s))|(commission)(|paid))$'  # fee
FEECOIN_REGEX_PATTERN = r'^(((fee)|(commission))(| *)((coin)|(currency)))|(coin\.3)$'  # feecoin
STATUS_REGEX_PATTERN = r'^(status)$'
EXCHANGE_REGEX_PATTERN = r'^exchange$'

# model 0
PAIR_REGEX_PATTERN_0 = r'^(((trading)|)(| *)(pair)|(symbol)|(currency(|s))|(market)|(coins)|(instrument))$'  # coinpair
PRICE_AVERAGE_REGEX_PATTERN_0 = r'^((filled)|)(| *)((price))(|(| *)per(| *)coin)$'
AMOUNT_MAIN_REGEX_PATTERN_0 = r'^((sub)|)((total)|(value)|(volume)|(funds))$'
AMOUNT_SUB_REGEX_PATTERN_0 = r'^(executed|)(| *)((am+ount)|(size)|(quantity)|(filled))$'
# model 1
PAIR_REGEX_PATTERN_1 = r'^exchange$'
PRICE_AVERAGE_REGEX_PATTERN_1 = r'^limit$'
AMOUNT_MAIN_REGEX_PATTERN_1 = r'^(price)$'
AMOUNT_SUB_REGEX_PATTERN_1 = AMOUNT_SUB_REGEX_PATTERN_0
# model 2
PAIR_REGEX_PATTERN_2 = PAIR_REGEX_PATTERN_0
AMOUNT_MAIN_REGEX_PATTERN_2 = r'^(etheramount)$'
AMOUNT_SUB_REGEX_PATTERN_2 = r'^tokenamount$'
# model 3
COIN_REGEX_PATTERN_3 = r'^(currency)$'  # Coin
AMOUNT_REGEX_PATTERN_3 = r'^(amount)|(size)$'
# model 4
BITCOIN_PAIR_REGEX_PATTERN_4 = r'^Währung(en|)$'  # coinpair
BITCOINDE_EINHEIT_KURS = r'^Einheit \(Kurs\)$'
AMOUNT_MAIN_WO_FEE_REGEX_PATTERN_4 = r'^(Menge|EUR) vor Gebühr$'
EINHEIT_AMOUNT_MAIN_WO_FEE_REGEX_PATTERN_4 = r'^Einheit \(Menge vor Gebühr\)$'
AMOUNT_SUB_WO_FEE_REGEX_PATTERN_4 = r'^(?!(EUR|Menge)).* vor Gebühr$'
AMOUNT_MAIN_W_FEE_REGEX_PATTERN_4 = r'^(Menge|EUR) nach Bitcoin\.de-Gebühr$'
EINHEIT_AMOUNT_MAIN_W_FEE_REGEX_PATTERN_4 = r'^Einheit \(Menge nach .*Gebühr\)$'
AMOUNT_MAIN_W_FEE_FIDOR_REGEX_PATTERN_4 = r'^EUR nach Bitcoin\.de- und Fidor-Gebühr$'
AMOUNT_SUB_W_FEE_REGEX_PATTERN_4 = r'^(?!(EUR|Menge)).* nach .*Gebühr$'
AMOUNT_ZUABGANG_REGEX_PATTERN_4 = r'^Zu.*Abgang$'
# model 5
PAIR_REGEX_PATTERN_5 = PAIR_REGEX_PATTERN_0
PRICE_AVERAGE_REGEX_PATTERN_5 = PRICE_AVERAGE_REGEX_PATTERN_0
AMOUNT_MAIN_REGEX_PATTERN_5 = AMOUNT_MAIN_REGEX_PATTERN_0
AMOUNT_SUB_REGEX_PATTERN_5 = AMOUNT_SUB_REGEX_PATTERN_0

# %% model template1:
# "date","type","buy amount","buy cur","sell amount","sell cur",("exchange"),("fee amount"),("fee currency"),("wallet")
TEMPLATE1_DATE_REGEX = re.compile(r'^DATE$')
TEMPLATE1_TYPE_REGEX = re.compile(r'^TYPE$')
TEMPLATE1_BUY_AMOUNT_REGEX = re.compile(r'^BUY_AMOUNT$')
TEMPLATE1_BUY_CUR_REGEX = re.compile(r'^BUY_CUR$')
TEMPLATE1_SELL_AMOUNT_REGEX = re.compile(r'^SELL_AMOUNT$')
TEMPLATE1_SELL_CUR_REGEX = re.compile(r'^SELL_CUR$')
TEMPLATE1_EXCHANGE_REGEX = re.compile(r'^EXCHANGE$')
TEMPLATE1_FEE_AMOUNT_REGEX = re.compile(r'^FEE_AMOUNT$')
TEMPLATE1_FEE_CURRENCY_REGEX = re.compile(r'^FEE_CURRENCY$')
TEMPLATE1_BUY_WALLET_REGEX = re.compile(r'^BUY_WALLET$')
TEMPLATE1_SELL_WALLET_REGEX = re.compile(r'^SELL_WALLET$')

# %% model tradeList: no,id,date,type,coin,amount,value,valueLoaded,tradePartnerId,exchange,externId,wallet
TRADELIST_ID_REGEX = re.compile(r'^id$', re.IGNORECASE)
TRADELIST_DATE_REGEX = re.compile(r'^date$', re.IGNORECASE)
TRADELIST_TYPE_REGEX = re.compile(r'^type$', re.IGNORECASE)
TRADELIST_COIN_REGEX = re.compile(r'^coin$', re.IGNORECASE)
TRADELIST_AMOUNT_REGEX = re.compile(r'^amount$', re.IGNORECASE)
TRADELIST_VALUE_REGEX = re.compile(r'^value(.{1,5})$', re.IGNORECASE)
TRADELIST_VALUELOADED_REGEX = re.compile(r'^valueLoaded$', re.IGNORECASE)
TRADELIST_TRADEPARTNERID_REGEX = re.compile(r'^tradePartnerId$', re.IGNORECASE)
TRADELIST_EXCHANGE_REGEX = re.compile(r'^exchange$', re.IGNORECASE)
TRADELIST_EXTERNID_REGEX = re.compile(r'^externId$', re.IGNORECASE)
TRADELIST_WALLET_REGEX = re.compile(r'^wallet$', re.IGNORECASE)

# %% model rotki: ,timestamp,location,pair,trade_type,amount,rate,fee,fee_currency,link,notes
ROTKI_TIMESTAMP_REGEX = re.compile(r'^timestamp$', re.IGNORECASE)
ROTKI_LOCATION_REGEX = re.compile(r'^location$', re.IGNORECASE)
ROTKI_PAIR_REGEX = re.compile(r'^pair$', re.IGNORECASE)
ROTKI_TRADE_TYPE_REGEX = re.compile(r'^trade_type$', re.IGNORECASE)
ROTKI_AMOUNT_REGEX = re.compile(r'^amount$', re.IGNORECASE)
ROTKI_RATE_REGEX = re.compile(r'^rate$', re.IGNORECASE)
ROTKI_FEE_REGEX = re.compile(r'^fee$', re.IGNORECASE)
ROTKI_FEE_CURRENCY_REGEX = re.compile(r'^fee_currency$', re.IGNORECASE)
ROTKI_LINK_REGEX = re.compile(r'^link$', re.IGNORECASE)
ROTKI_NOTES_REGEX = re.compile(r'^notes$', re.IGNORECASE)

# %% model CCXT: timestamp, location, pair, trade_type, amount, rate, fee, fee_currency, link
CCXT_TIMESTAMP_REGEX = re.compile(r'^timestamp$', re.IGNORECASE)
CCXT_LOCATION_REGEX = re.compile(r'^location$', re.IGNORECASE)
CCXT_PAIR_REGEX = re.compile(r'^pair$', re.IGNORECASE)
CCXT_TRADE_TYPE_REGEX = re.compile(r'^trade_type$', re.IGNORECASE)
CCXT_AMOUNT_REGEX = re.compile(r'^amount$', re.IGNORECASE)
CCXT_RATE_REGEX = re.compile(r'^rate$', re.IGNORECASE)
CCXT_FEE_REGEX = re.compile(r'^fee$', re.IGNORECASE)
CCXT_FEE_CURRENCY_REGEX = re.compile(r'^fee_currency$', re.IGNORECASE)
CCXT_LINK_REGEX = re.compile(r'^link$', re.IGNORECASE)

# %% regex # XXX_$1_REGEX = re.compile\(r\'\^$1\$\'\)

# model exodus DATE,TYPE,OUTAMOUNT,OUTCURRENCY,FEEAMOUNT,FEECURRENCY,OUTTXID,OUTTXURL,INAMOUNT,INCURRENCY,INTXID,INTXURL,ORDERID
EXODUS_DATE_REGEX = re.compile(r'^DATE$', re.IGNORECASE)
EXODUS_TYPE_REGEX = re.compile(r'^TYPE$', re.IGNORECASE)
EXODUS_OUTAMOUNT_REGEX = re.compile(r'^OUTAMOUNT$', re.IGNORECASE)
EXODUS_OUTCURRENCY_REGEX = re.compile(r'^OUTCURRENCY$', re.IGNORECASE)
EXODUS_FEEAMOUNT_REGEX = re.compile(r'^FEEAMOUNT$', re.IGNORECASE)
EXODUS_FEECURRENCY_REGEX = re.compile(r'^FEECURRENCY$', re.IGNORECASE)
EXODUS_OUTTXID_REGEX = re.compile(r'^OUTTXID$', re.IGNORECASE)
EXODUS_OUTTXURL_REGEX = re.compile(r'^OUTTXURL$', re.IGNORECASE)
EXODUS_INAMOUNT_REGEX = re.compile(r'^INAMOUNT$', re.IGNORECASE)
EXODUS_INCURRENCY_REGEX = re.compile(r'^INCURRENCY$', re.IGNORECASE)
EXODUS_INTXID_REGEX = re.compile(r'^INTXID$', re.IGNORECASE)
EXODUS_INTXURL_REGEX = re.compile(r'^INTXURL$', re.IGNORECASE)
EXODUS_ORDERID_REGEX = re.compile(r'^ORDERID$', re.IGNORECASE)

# model Blockdaemon Cardano [currency,return,timeEnd,timeStart,startingBalance,timeAggregation,address,metadata]
BLOCKDAEMON_ADDRESS_REGEX = re.compile(r'^ADDRESS$', re.IGNORECASE)
BLOCKDAEMON_CURRENCY_REGEX = re.compile(r'^CURRENCY$', re.IGNORECASE)
BLOCKDAEMON_METADATA_REGEX = re.compile(r'^METADATA$', re.IGNORECASE)
BLOCKDAEMON_RETURN_REGEX = re.compile(r'^RETURN$', re.IGNORECASE)
BLOCKDAEMON_STARTINGBALANCE_REGEX = re.compile(r'^STARTINGBALANCE$', re.IGNORECASE)
BLOCKDAEMON_TIMEAGGREGATION_REGEX = re.compile(r'^TIMEAGGREGATION$', re.IGNORECASE)
BLOCKDAEMON_TIMEEND_REGEX = re.compile(r'^TIMEEND$', re.IGNORECASE)
BLOCKDAEMON_TIMESTART_REGEX = re.compile(r'^TIMESTART$', re.IGNORECASE)
BLOCKDAEMON_EPOCH_REGEX = re.compile(r'^EPOCH$', re.IGNORECASE)

# model kucoin [orderCreatedAt,id,clientOid,symbol,side,type,stopPrice,price,size,dealSize,dealFunds,averagePrice,fee,feeCurrency,remark,tags,orderStatus]
KUCOIN_ORDERCREATEDAT_REGEX = re.compile(r'^orderCreatedAt$', re.IGNORECASE)
KUCOIN_ID_REGEX = re.compile(r'^id$', re.IGNORECASE)
KUCOIN_CLIENTOID_REGEX = re.compile(r'^clientOid$', re.IGNORECASE)
KUCOIN_SYMBOL_REGEX = re.compile(r'^symbol$', re.IGNORECASE)
KUCOIN_SIDE_REGEX = re.compile(r'^side$', re.IGNORECASE)
KUCOIN_TYPE_REGEX = re.compile(r'^type$', re.IGNORECASE)
KUCOIN_STOPPRICE_REGEX = re.compile(r'^stopPrice$', re.IGNORECASE)
KUCOIN_PRICE_REGEX = re.compile(r'^price$', re.IGNORECASE)
KUCOIN_SIZE_REGEX = re.compile(r'^size$', re.IGNORECASE)
KUCOIN_DEALSIZE_REGEX = re.compile(r'^dealSize$', re.IGNORECASE)
KUCOIN_DEALFUNDS_REGEX = re.compile(r'^dealFunds$', re.IGNORECASE)
KUCOIN_AVERAGEPRICE_REGEX = re.compile(r'^averagePrice$', re.IGNORECASE)
KUCOIN_FEE_REGEX = re.compile(r'^fee$', re.IGNORECASE)
KUCOIN_FEECURRENCY_REGEX = re.compile(r'^feeCurrency$', re.IGNORECASE)
KUCOIN_REMARK_REGEX = re.compile(r'^remark$', re.IGNORECASE)
KUCOIN_TAGS_REGEX = re.compile(r'^tags$', re.IGNORECASE)
KUCOIN_ORDERSTATUS_REGEX = re.compile(r'^orderStatus$', re.IGNORECASE)

# model kraken ["txid","ordertxid","pair","time","type","ordertype","price","cost","fee","vol","margin","misc","ledgers"]
KRAKEN_TXID_REGEX = re.compile(r'^txid$', re.IGNORECASE)
KRAKEN_ORDERTXID_REGEX = re.compile(r'^ordertxid$', re.IGNORECASE)
KRAKEN_PAIR_REGEX = re.compile(r'^pair$', re.IGNORECASE)
KRAKEN_TIME_REGEX = re.compile(r'^time$', re.IGNORECASE)
KRAKEN_TYPE_REGEX = re.compile(r'^type$', re.IGNORECASE)
KRAKEN_ORDERTYPE_REGEX = re.compile(r'^ordertype$', re.IGNORECASE)
KRAKEN_PRICE_REGEX = re.compile(r'^price$', re.IGNORECASE)
KRAKEN_COST_REGEX = re.compile(r'^cost$', re.IGNORECASE)
KRAKEN_FEE_REGEX = re.compile(r'^fee$', re.IGNORECASE)
KRAKEN_VOL_REGEX = re.compile(r'^vol$', re.IGNORECASE)
KRAKEN_MARGIN_REGEX = re.compile(r'^margin$', re.IGNORECASE)
KRAKEN_MISC_REGEX = re.compile(r'^misc$', re.IGNORECASE)
KRAKEN_LEDGERS_REGEX = re.compile(r'^ledgers$', re.IGNORECASE)

# model kraken api [dtime,txid,cost,fee,margin,misc,ordertxid,ordertype,pair,postxid,price,time,type,vol]
KRAKENAPI_DTIME_REGEX = re.compile(r'^dtime$', re.IGNORECASE)
KRAKENAPI_TXID_REGEX = re.compile(r'^txid$', re.IGNORECASE)
KRAKENAPI_COST_REGEX = re.compile(r'^cost$', re.IGNORECASE)
KRAKENAPI_FEE_REGEX = re.compile(r'^fee$', re.IGNORECASE)
KRAKENAPI_MARGIN_REGEX = re.compile(r'^margin$', re.IGNORECASE)
KRAKENAPI_MISC_REGEX = re.compile(r'^misc$', re.IGNORECASE)
KRAKENAPI_ORDERTXID_REGEX = re.compile(r'^ordertxid$', re.IGNORECASE)
KRAKENAPI_ORDERTYPE_REGEX = re.compile(r'^ordertype$', re.IGNORECASE)
KRAKENAPI_PAIR_REGEX = re.compile(r'^pair$', re.IGNORECASE)
KRAKENAPI_POSTXID_REGEX = re.compile(r'^postxid$', re.IGNORECASE)
KRAKENAPI_PRICE_REGEX = re.compile(r'^price$', re.IGNORECASE)
KRAKENAPI_TIME_REGEX = re.compile(r'^time$', re.IGNORECASE)
KRAKENAPI_TYPE_REGEX = re.compile(r'^type$', re.IGNORECASE)
KRAKENAPI_VOL_REGEX = re.compile(r'^vol$', re.IGNORECASE)

# model kraken ledger [txid, refid, time, type, subtype, aclass, asset, amount, fee, balance]
KRAKENLEDGER_TXID_REGEX = re.compile(r'^TXID$', re.IGNORECASE)
KRAKENLEDGER_REFID_REGEX = re.compile(r'^REFID$', re.IGNORECASE)
KRAKENLEDGER_TIME_REGEX = re.compile(r'^TIME$', re.IGNORECASE)
KRAKENLEDGER_TYPE_REGEX = re.compile(r'^TYPE$', re.IGNORECASE)
KRAKENLEDGER_SUBTYPE_REGEX = re.compile(r'^SUBTYPE$', re.IGNORECASE)
KRAKENLEDGER_ACLASS_REGEX = re.compile(r'^ACLASS$', re.IGNORECASE)
KRAKENLEDGER_ASSET_REGEX = re.compile(r'^ASSET$', re.IGNORECASE)
KRAKENLEDGER_AMOUNT_REGEX = re.compile(r'^AMOUNT$', re.IGNORECASE)
KRAKENLEDGER_FEE_REGEX = re.compile(r'^FEE$', re.IGNORECASE)
KRAKENLEDGER_BALANCE_REGEX = re.compile(r'^BALANCE$', re.IGNORECASE)

# model binance ['Date(UTC)', 'Market', 'Type', 'Price', 'Amount', 'Total', 'Fee', 'Fee Coin']
BINANCE_DATE_REGEX = re.compile(r'^Date\(\w*\)$', re.IGNORECASE)
BINANCE_MARKET_REGEX = re.compile(r'^Market$', re.IGNORECASE)
BINANCE_TYPE_REGEX = re.compile(r'^Type$', re.IGNORECASE)
BINANCE_PRICE_REGEX = re.compile(r'^Price$', re.IGNORECASE)
BINANCE_AMOUNT_REGEX = re.compile(r'^Amount$', re.IGNORECASE)
BINANCE_TOTAL_REGEX = re.compile(r'^Total$', re.IGNORECASE)
BINANCE_FEE_REGEX = re.compile(r'^Fee$', re.IGNORECASE)
BINANCE_FEECOIN_REGEX = re.compile(r'^Fee Coin$', re.IGNORECASE)

# model poloniex ['Date', 'Market', 'Category', 'Type', 'Price', 'Amount', 'Total', 'Fee', 'Order Number', 'Base Total Less Fee', 'Quote Total Less Fee']
POLONIEX_DATE_REGEX = re.compile(r'^Date$', re.IGNORECASE)
POLONIEX_MARKET_REGEX = re.compile(r'^Market$', re.IGNORECASE)
POLONIEX_CATEGORY_REGEX = re.compile(r'^Category$', re.IGNORECASE)
POLONIEX_TYPE_REGEX = re.compile(r'^Type$', re.IGNORECASE)
POLONIEX_PRICE_REGEX = re.compile(r'^Price$', re.IGNORECASE)
POLONIEX_AMOUNT_REGEX = re.compile(r'^Amount$', re.IGNORECASE)
POLONIEX_TOTAL_REGEX = re.compile(r'^Total$', re.IGNORECASE)
POLONIEX_FEE_REGEX = re.compile(r'^Fee$', re.IGNORECASE)
POLONIEX_ORDERNUMBER_REGEX = re.compile(r'^Order Number$', re.IGNORECASE)
POLONIEX_BASETOTALLESSFEE_REGEX = re.compile(r'^Base Total Less Fee$', re.IGNORECASE)
POLONIEX_QUOTETOTALLESSFEE_REGEX = re.compile(r'^Quote Total Less Fee$', re.IGNORECASE)

# model bittrex [Uuid, Exchange, TimeStamp, OrderType, Limit, Quantity, QuantityRemaining, Commission, Price, PricePerUnit, IsConditional, Condition, ConditionTarget, ImmediateOrCancel, Closed]
BITTREX_UUID_REGEX = re.compile(r'^Uuid$', re.IGNORECASE)
BITTREX_EXCHANGE_REGEX = re.compile(r'^Exchange$', re.IGNORECASE)
BITTREX_TIMESTAMP_REGEX = re.compile(r'^TimeStamp$', re.IGNORECASE)
BITTREX_ORDERTYPE_REGEX = re.compile(r'^OrderType$', re.IGNORECASE)
BITTREX_LIMIT_REGEX = re.compile(r'^Limit$', re.IGNORECASE)
BITTREX_QUANTITY_REGEX = re.compile(r'^Quantity$', re.IGNORECASE)
BITTREX_QUANTITYREMAINING_REGEX = re.compile(r'^QuantityRemaining$', re.IGNORECASE)
BITTREX_COMMISSION_REGEX = re.compile(r'^Commission$', re.IGNORECASE)
BITTREX_PRICE_REGEX = re.compile(r'^Price$', re.IGNORECASE)
BITTREX_PRICEPERUNIT_REGEX = re.compile(r'^PricePerUnit$', re.IGNORECASE)
BITTREX_ISCONDITIONAL_REGEX = re.compile(r'^IsConditional$', re.IGNORECASE)
BITTREX_CONDITION_REGEX = re.compile(r'^Condition$', re.IGNORECASE)
BITTREX_CONDITIONTARGET_REGEX = re.compile(r'^ConditionTarget$', re.IGNORECASE)
BITTREX_IMMEDIATEORCANCEL_REGEX = re.compile(r'^ImmediateOrCancel$', re.IGNORECASE)
BITTREX_CLOSED_REGEX = re.compile(r'^Closed$', re.IGNORECASE)

# general
ID_REGEX = re.compile(ID_REGEX_PATTERN, re.IGNORECASE)
DATE_REGEX = re.compile(DATE_REGEX_PATTERN, re.IGNORECASE)
TYPE_REGEX = re.compile(TYPE_REGEX_PATTERN, re.IGNORECASE)
FEE_REGEX = re.compile(FEE_REGEX_PATTERN, re.IGNORECASE)
FEECOIN_REGEX = re.compile(FEECOIN_REGEX_PATTERN, re.IGNORECASE)
STATUS_REGEX = re.compile(STATUS_REGEX_PATTERN, re.IGNORECASE)
EXCHANGE_REGEX = re.compile(EXCHANGE_REGEX_PATTERN, re.IGNORECASE)

# model 0
PAIR_REGEX_0 = re.compile(PAIR_REGEX_PATTERN_0, re.IGNORECASE)
PRICE_AVERAGE_REGEX_0 = re.compile(PRICE_AVERAGE_REGEX_PATTERN_0, re.IGNORECASE)
AMOUNT_MAIN_REGEX_0 = re.compile(AMOUNT_MAIN_REGEX_PATTERN_0, re.IGNORECASE)
AMOUNT_SUB_REGEX_0 = re.compile(AMOUNT_SUB_REGEX_PATTERN_0, re.IGNORECASE)
# model 1
PAIR_REGEX_1 = re.compile(PAIR_REGEX_PATTERN_1, re.IGNORECASE)
PRICE_AVERAGE_REGEX_1 = re.compile(PRICE_AVERAGE_REGEX_PATTERN_1, re.IGNORECASE)
AMOUNT_MAIN_REGEX_1 = re.compile(AMOUNT_MAIN_REGEX_PATTERN_1, re.IGNORECASE)
AMOUNT_SUB_REGEX_1 = re.compile(AMOUNT_SUB_REGEX_PATTERN_1, re.IGNORECASE)
# model 2
PAIR_REGEX_2 = re.compile(PAIR_REGEX_PATTERN_2, re.IGNORECASE)
AMOUNT_MAIN_REGEX_2 = re.compile(AMOUNT_MAIN_REGEX_PATTERN_2, re.IGNORECASE)
AMOUNT_SUB_REGEX_2 = re.compile(AMOUNT_SUB_REGEX_PATTERN_2, re.IGNORECASE)
# model 3
COIN_REGEX_3 = re.compile(COIN_REGEX_PATTERN_3, re.IGNORECASE)
AMOUNT_REGEX_3 = re.compile(AMOUNT_REGEX_PATTERN_3, re.IGNORECASE)
# model 4
BITCOIN_PAIR_REGEX_4 = re.compile(BITCOIN_PAIR_REGEX_PATTERN_4, re.IGNORECASE)
BITCOINDE_EINHEIT_KURS_REGEX = re.compile(BITCOINDE_EINHEIT_KURS)
AMOUNT_MAIN_WO_FEE_REGEX_4 = re.compile(AMOUNT_MAIN_WO_FEE_REGEX_PATTERN_4, re.IGNORECASE)
BITCOINDE_EINHEIT_AMOUNT_MAIN_WO_FEE_REGEX = re.compile(EINHEIT_AMOUNT_MAIN_WO_FEE_REGEX_PATTERN_4, re.IGNORECASE)
AMOUNT_SUB_WO_FEE_REGEX_4 = re.compile(AMOUNT_SUB_WO_FEE_REGEX_PATTERN_4, re.IGNORECASE)
AMOUNT_MAIN_W_FEE_REGEX_4 = re.compile(AMOUNT_MAIN_W_FEE_REGEX_PATTERN_4, re.IGNORECASE)
BITCOINDE_EINHEIT_AMOUNT_MAIN_W_FEE_REGEX = re.compile(EINHEIT_AMOUNT_MAIN_W_FEE_REGEX_PATTERN_4, re.IGNORECASE)
AMOUNT_MAIN_W_FEE_FIDOR_REGEX_4 = re.compile(AMOUNT_MAIN_W_FEE_FIDOR_REGEX_PATTERN_4, re.IGNORECASE)
AMOUNT_SUB_W_FEE_REGEX_4 = re.compile(AMOUNT_SUB_W_FEE_REGEX_PATTERN_4, re.IGNORECASE)
AMOUNT_ZUABGANG_REGEX_4 = re.compile(AMOUNT_ZUABGANG_REGEX_PATTERN_4, re.IGNORECASE)
# model 5
PAIR_REGEX_5 = re.compile(PAIR_REGEX_PATTERN_5, re.IGNORECASE)
PRICE_AVERAGE_REGEX_5 = re.compile(PRICE_AVERAGE_REGEX_PATTERN_5, re.IGNORECASE)
AMOUNT_MAIN_REGEX_5 = re.compile(AMOUNT_MAIN_REGEX_PATTERN_5, re.IGNORECASE)
AMOUNT_SUB_REGEX_5 = re.compile(AMOUNT_SUB_REGEX_PATTERN_5, re.IGNORECASE)

# %% content patterns
NUMBER_REGEX_PATTERN = r'^((|-)\d*(\.|,|)\d*)(\D*)$'

# %% content regex
NUMBER_REGEX = re.compile(NUMBER_REGEX_PATTERN)

# %% datetime patterns
TIME_PATTERN = [
    r'^\d{4}-\d\d-\d\d \d\d:\d\d:\d\d$',  # 2018-08-26 04:22:33
    r'^(\d{4}-\d\d-\d\d )(\d:\d\d:\d\d)$',  # 2018-08-26 4:22:33
    r'^\d{4}-\d\d-\d\d \d\d:\d\d:\d\d [-\+]\d{4}$',  # 2017-05-22 06:30:17 -0700
    r'^(\d{1,2})(/)(\d{1,2})(/\d{4} )(\d{1,2})(:\d\d:\d\d) (\w\w)$',  # 8/8/2018 4:50:42 PM
    r'^\w{3} \w{3} \d{2} \d\d:\d\d:\d\d \d{4}$',  # Wed Jun 27 17:16:39 2018
    r'^(\w{3} \w{3} \d{2} \d\d:\d\d:\d\d)( \w{3})( \d{4})$',  # Wed Jun 27 17:16:39 CST 2018
    r'^(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d)(\.\d+)$',  # 2017-05-22 06:30:17 .200
    r'^(\w{3} \w{3} \d{2})( \d{4})( \d\d:\d\d:\d\d)( \w{3})([-\+]\d{4})( .*)$',  # Fri May 19 2017 12:11:49 GMT+0200 (Mitteleuropäische Sommerzeit)
    r'^(\d{4}-\d\d-\d\d).(\d\d:\d\d:\d\d).*Z$',  # 2017-07-28T20:23:16.000Z
    r'^(\d\d-\d\d-\d\d).(\d\d:\d\d:\d\d)$',  # 27-09-17 17:01:01
    ]

PANDAS_TIME_PATTERN = r'^\d{4}-\d\d-\d\d \d\d:\d\d:\d\d[-\+]\d\d:\d\d$'

# some patterns need to be changed before conversion
TIME_SPECIAL_PATTERN_INDEX = [1, 3, 5, 6, 7, 8]

TIME_FORMAT = ['%Y-%m-%d %H:%M:%S',
               '%Y-%m-%d %H:%M:%S',
               '%Y-%m-%d %H:%M:%S %z',
               '%m/%d/%Y %H:%M:%S',
               '%c',
               '%c',
               '%Y-%m-%d %H:%M:%S',
               '%c %z',
               '%Y-%m-%d %H:%M:%S %z',
               '%d-%m-%y %H:%M:%S']

# 2018-08-26 04:22:33
# 8/8/2018 4:50:42 PM
# 2017-05-22 06:30:17 -0700
# Wed Jun 27 17:16:39 CST 2018
# Fri May 19 2017 12:11:49 GMT+0200 (Mitteleuropäische Sommerzeit)

# %% datetime regex
TIME_REGEX = []
for pat in TIME_PATTERN:
    TIME_REGEX.append(re.compile(pat, re.IGNORECASE | re.MULTILINE))

Pandas_TIME_REGEX = re.compile(PANDAS_TIME_PATTERN, re.IGNORECASE | re.MULTILINE)
