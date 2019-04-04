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
# "date","type","buy amount","buy cur","sell amount","sell cur",("exchange"),("fee amount"),("fee currency")
TEMPLATE1_DATE_REGEX = re.compile(r'^DATE$')
TEMPLATE1_TYPE_REGEX = re.compile(r'^TYPE$')
TEMPLATE1_BUY_AMOUNT_REGEX = re.compile(r'^BUY_AMOUNT$')
TEMPLATE1_BUY_CUR_REGEX = re.compile(r'^BUY_CUR$')
TEMPLATE1_SELL_AMOUNT_REGEX = re.compile(r'^SELL_AMOUNT$')
TEMPLATE1_SELL_CUR_REGEX = re.compile(r'^SELL_CUR$')
TEMPLATE1_EXCHANGE_REGEX = re.compile(r'^EXCHANGE$')
TEMPLATE1_FEE_AMOUNT_REGEX = re.compile(r'^FEE_AMOUNT$')
TEMPLATE1_FEE_CURRENCY_REGEX = re.compile(r'^FEE_CURRENCY$')

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


# general
ID_REGEX = re.compile(ID_REGEX_PATTERN, re.IGNORECASE)
DATE_REGEX = re.compile(DATE_REGEX_PATTERN, re.IGNORECASE)
TYPE_REGEX = re.compile(TYPE_REGEX_PATTERN, re.IGNORECASE)
FEE_REGEX = re.compile(FEE_REGEX_PATTERN, re.IGNORECASE)
FEECOIN_REGEX = re.compile(FEECOIN_REGEX_PATTERN, re.IGNORECASE)
STATUS_REGEX = re.compile(STATUS_REGEX_PATTERN, re.IGNORECASE)

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
TIME_PATTERN = []
TIME_PATTERN.append(r'^\d{4}-\d\d-\d\d \d\d:\d\d:\d\d$')  # 2018-08-26 04:22:33
TIME_PATTERN.append(r'^(\d{4}-\d\d-\d\d )(\d:\d\d:\d\d)$')  # 2018-08-26 4:22:33
TIME_PATTERN.append(r'^\d{4}-\d\d-\d\d \d\d:\d\d:\d\d [-|\+]\d{4}$')  # 2017-05-22 06:30:17 -0700
TIME_PATTERN.append(r'^(\d{1,2})(/)(\d{1,2})(/\d{4} )(\d{1,2})(:\d\d:\d\d) (\w\w)$')  # 8/8/2018 4:50:42 PM
TIME_PATTERN.append(r'^\w{3} \w{3} \d{2} \d\d:\d\d:\d\d \d{4}$')  # Wed Jun 27 17:16:39 2018
TIME_PATTERN.append(r'^(\w{3} \w{3} \d{2} \d\d:\d\d:\d\d)( \w{3})( \d{4})$')  # Wed Jun 27 17:16:39 CST 2018
TIME_PATTERN.append(r'^(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d)(\.\d+)$')  # 2017-05-22 06:30:17 .200
TIME_PATTERN.append(r'^(\w{3} \w{3} \d{2})( \d{4})( \d\d:\d\d:\d\d)( \w{3})([-|\+]\d{4})( .*)$')  # Fri May 19 2017 12:11:49 GMT+0200 (Mitteleuropäische Sommerzeit)
TIME_PATTERN.append(r'^(\d{4}-\d\d-\d\d).(\d\d:\d\d:\d\d).*Z$')  # 2017-07-28T20:23:16.000Z
TIME_PATTERN.append(r'^(\d\d-\d\d-\d\d).(\d\d:\d\d:\d\d)$')  # 27-09-17 17:01:01

PANDAS_TIME_PATTERN = r'^\d{4}-\d\d-\d\d \d\d:\d\d:\d\d[-|\+]\d\d:\d\d$'

# some patterns need to be changed before conversion
TIME_SPECIAL_PATTERN_INDEX = []
TIME_SPECIAL_PATTERN_INDEX.append(1)
TIME_SPECIAL_PATTERN_INDEX.append(3)
TIME_SPECIAL_PATTERN_INDEX.append(5)
TIME_SPECIAL_PATTERN_INDEX.append(6)
TIME_SPECIAL_PATTERN_INDEX.append(7)
TIME_SPECIAL_PATTERN_INDEX.append(8)

TIME_FORMAT = []
TIME_FORMAT.append('%Y-%m-%d %H:%M:%S')
TIME_FORMAT.append('%Y-%m-%d %H:%M:%S')
TIME_FORMAT.append('%Y-%m-%d %H:%M:%S %z')
TIME_FORMAT.append('%m/%d/%Y %H:%M:%S')
TIME_FORMAT.append('%c')
TIME_FORMAT.append('%c')
TIME_FORMAT.append('%Y-%m-%d %H:%M:%S')
TIME_FORMAT.append('%c %z')
TIME_FORMAT.append('%Y-%m-%d %H:%M:%S %z')
TIME_FORMAT.append('%d-%m-%y %H:%M:%S')

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
