# -*- coding: utf-8 -*-

import re

# %% header patterns
# general
ID_REGEX_PATTERN = r'^(((T|t)ransaction)|((T|t)rade)|((O|o)rder)|())( *|_)(((I|i)(D|d))|(Uu(I|i)(D|d))|((N|n)umber)|((N|n)ummer)|(Referenz))|#$'  # id
DATE_REGEX_PATTERN = r'^(((D|d)ate.*)|Datum|((T|t)ime(|stamp))|((C|c)losed)|((U|u)pdated))$'  # date
TYPE_REGEX_PATTERN = r'^((((T|t)ransaction)|((T|t)rade)|((O|o)rder)|())( *|_)(((T|t)yp(|e))|((S|s)ide))|((S|s)ell/(B|b)uy))$'  # type
FEE_REGEX_PATTERN = r'^(((F|f)ee(|s))|((C|c)ommission)(|(P|p)aid))$'  # fee
FEECOIN_REGEX_PATTERN = r'^((((F|f)ee)|((C|c)ommission))(| *)(((C|c)oin)|((C|c)urrency)))|((C|c)oin\.3)$'  # feecoin
STATUS_REGEX_PATTERN = r'^((S|s)tatus)$'

# model 0
PAIR_REGEX_PATTERN_0 = r'^((((T|t)rading)|)(| *)((P|p)air)|((C|c)urrency(|s))|((M|m)arket)|((C|c)oins)|((I|i)nstrument))$'  # coinpair
PRICE_AVERAGE_REGEX_PATTERN_0 = r'^(((F|f)illed)|)(| *)(((P|p)rice))(|(| *)(P|p)er(| *)(C|c)oin)$'
AMOUNT_MAIN_REGEX_PATTERN_0 = r'^(((S|s)ub)|)(((T|t)otal)|((V|v)alue)|((V|v)olume))$'
AMOUNT_SUB_REGEX_PATTERN_0 = r'^((E|e)xecuted|)(| *)(((A|a)m+ount)|((Q|q)uantity)|((F|f)illed))$'
# model 1
PAIR_REGEX_PATTERN_1 = r'^(E|e)xchange$'
PRICE_AVERAGE_REGEX_PATTERN_1 = r'^(L|l)imit$'
AMOUNT_MAIN_REGEX_PATTERN_1 = r'^((P|p)rice)$'
AMOUNT_SUB_REGEX_PATTERN_1 = AMOUNT_SUB_REGEX_PATTERN_0
# model 2
PAIR_REGEX_PATTERN_2 = PAIR_REGEX_PATTERN_0
AMOUNT_MAIN_REGEX_PATTERN_2 = r'^((E|e)ther(A|a)mount)$'
AMOUNT_SUB_REGEX_PATTERN_2 = r'^(T|t)oken(A|a)mount$'
# model 3
COIN_REGEX_PATTERN_3 = r'^((C|c)urrency)$'  # Coin
AMOUNT_REGEX_PATTERN_3 = r'^((A|a)mount)|((S|s)ize)$'
# model 4
PAIR_REGEX_PATTERN_4 = r'^Währungen$'  # coinpair
AMOUNT_MAIN_WO_FEE_REGEX_PATTERN_4 = r'^EUR vor Gebühr$'
AMOUNT_SUB_WO_FEE_REGEX_PATTERN_4 = r'^(?!EUR).* vor Gebühr$'
AMOUNT_MAIN_W_FEE_REGEX_PATTERN_4 = r'^EUR nach .*Fidor.*Gebühr$'
AMOUNT_SUB_W_FEE_REGEX_PATTERN_4 = r'^(?!EUR).* nach .*Gebühr$'
AMOUNT_ZUABGANG_REGEX_PATTERN_4 = r'^Zu.*Abgang$'
# model 5
PAIR_REGEX_PATTERN_5 = PAIR_REGEX_PATTERN_0
PRICE_AVERAGE_REGEX_PATTERN_5 = PRICE_AVERAGE_REGEX_PATTERN_0
AMOUNT_MAIN_REGEX_PATTERN_5 = AMOUNT_MAIN_REGEX_PATTERN_0
AMOUNT_SUB_REGEX_PATTERN_5 = AMOUNT_SUB_REGEX_PATTERN_0

# %% model tradeList: no,id,date,type,coin,amount,value,valueLoaded,tradePartnerId,exchange,externId,wallet
TRADELIST_ID_REGEX = re.compile(r'^id$')
TRADELIST_DATE_REGEX = re.compile(r'^date$')
TRADELIST_TYPE_REGEX = re.compile(r'^type$')
TRADELIST_COIN_REGEX = re.compile(r'^coin$')
TRADELIST_AMOUNT_REGEX = re.compile(r'^amount$')
TRADELIST_VALUE_REGEX = re.compile(r'^value(.{1,5})$')
TRADELIST_VALUELOADED_REGEX = re.compile(r'^valueLoaded$')
TRADELIST_TRADEPARTNERID_REGEX = re.compile(r'^tradePartnerId$')
TRADELIST_EXCHANGE_REGEX = re.compile(r'^exchange$')
TRADELIST_EXTERNID_REGEX = re.compile(r'^externId$')
TRADELIST_WALLET_REGEX = re.compile(r'^wallet$')

# %% regex # XXX_$1_REGEX = re.compile\(r\'\^$1\$\'\)

# model exodus DATE,TYPE,OUTAMOUNT,OUTCURRENCY,FEEAMOUNT,FEECURRENCY,OUTTXID,OUTTXURL,INAMOUNT,INCURRENCY,INTXID,INTXURL,ORDERID
EXODUS_DATE_REGEX = re.compile(r'^DATE$')
EXODUS_TYPE_REGEX = re.compile(r'^TYPE$')
EXODUS_OUTAMOUNT_REGEX = re.compile(r'^OUTAMOUNT$')
EXODUS_OUTCURRENCY_REGEX = re.compile(r'^OUTCURRENCY$')
EXODUS_FEEAMOUNT_REGEX = re.compile(r'^FEEAMOUNT$')
EXODUS_FEECURRENCY_REGEX = re.compile(r'^FEECURRENCY$')
EXODUS_OUTTXID_REGEX = re.compile(r'^OUTTXID$')
EXODUS_OUTTXURL_REGEX = re.compile(r'^OUTTXURL$')
EXODUS_INAMOUNT_REGEX = re.compile(r'^INAMOUNT$')
EXODUS_INCURRENCY_REGEX = re.compile(r'^INCURRENCY$')
EXODUS_INTXID_REGEX = re.compile(r'^INTXID$')
EXODUS_INTXURL_REGEX = re.compile(r'^INTXURL$')
EXODUS_ORDERID_REGEX = re.compile(r'^ORDERID$')

# model kraken ["txid","ordertxid","pair","time","type","ordertype","price","cost","fee","vol","margin","misc","ledgers"]
KRAKEN_TXID_REGEX = re.compile(r'^txid$')
KRAKEN_ORDERTXID_REGEX = re.compile(r'^ordertxid$')
KRAKEN_PAIR_REGEX = re.compile(r'^pair$')
KRAKEN_TIME_REGEX = re.compile(r'^time$')
KRAKEN_TYPE_REGEX = re.compile(r'^type$')
KRAKEN_ORDERTYPE_REGEX = re.compile(r'^ordertype$')
KRAKEN_PRICE_REGEX = re.compile(r'^price$')
KRAKEN_COST_REGEX = re.compile(r'^cost$')
KRAKEN_FEE_REGEX = re.compile(r'^fee$')
KRAKEN_VOL_REGEX = re.compile(r'^vol$')
KRAKEN_MARGIN_REGEX = re.compile(r'^margin$')
KRAKEN_MISC_REGEX = re.compile(r'^misc$')
KRAKEN_LEDGERS_REGEX = re.compile(r'^ledgers$')

# model binance ['Date(UTC)', 'Market', 'Type', 'Price', 'Amount', 'Total', 'Fee', 'Fee Coin']
BINANCE_DATE_REGEX = re.compile(r'^Date\(\w*\)$')
BINANCE_MARKET_REGEX = re.compile(r'^Market$')
BINANCE_TYPE_REGEX = re.compile(r'^Type$')
BINANCE_PRICE_REGEX = re.compile(r'^Price$')
BINANCE_AMOUNT_REGEX = re.compile(r'^Amount$')
BINANCE_TOTAL_REGEX = re.compile(r'^Total$')
BINANCE_FEE_REGEX = re.compile(r'^Fee$')
BINANCE_FEECOIN_REGEX = re.compile(r'^Fee Coin$')

# model poloniex ['Date', 'Market', 'Category', 'Type', 'Price', 'Amount', 'Total', 'Fee', 'Order Number', 'Base Total Less Fee', 'Quote Total Less Fee']
POLONIEX_DATE_REGEX = re.compile(r'^Date$')
POLONIEX_MARKET_REGEX = re.compile(r'^Market$')
POLONIEX_CATEGORY_REGEX = re.compile(r'^Category$')
POLONIEX_TYPE_REGEX = re.compile(r'^Type$')
POLONIEX_PRICE_REGEX = re.compile(r'^Price$')
POLONIEX_AMOUNT_REGEX = re.compile(r'^Amount$')
POLONIEX_TOTAL_REGEX = re.compile(r'^Total$')
POLONIEX_FEE_REGEX = re.compile(r'^Fee$')
POLONIEX_ORDERNUMBER_REGEX = re.compile(r'^Order Number$')
POLONIEX_BASETOTALLESSFEE_REGEX = re.compile(r'^Base Total Less Fee$')
POLONIEX_QUOTETOTALLESSFEE_REGEX = re.compile(r'^Quote Total Less Fee$')

# general
ID_REGEX = re.compile(ID_REGEX_PATTERN)
DATE_REGEX = re.compile(DATE_REGEX_PATTERN)
TYPE_REGEX = re.compile(TYPE_REGEX_PATTERN)
FEE_REGEX = re.compile(FEE_REGEX_PATTERN)
FEECOIN_REGEX = re.compile(FEECOIN_REGEX_PATTERN)
STATUS_REGEX = re.compile(STATUS_REGEX_PATTERN)

# model 0
PAIR_REGEX_0 = re.compile(PAIR_REGEX_PATTERN_0)
PRICE_AVERAGE_REGEX_0 = re.compile(PRICE_AVERAGE_REGEX_PATTERN_0)
AMOUNT_MAIN_REGEX_0 = re.compile(AMOUNT_MAIN_REGEX_PATTERN_0)
AMOUNT_SUB_REGEX_0 = re.compile(AMOUNT_SUB_REGEX_PATTERN_0)
# model 1
PAIR_REGEX_1 = re.compile(PAIR_REGEX_PATTERN_1)
PRICE_AVERAGE_REGEX_1 = re.compile(PRICE_AVERAGE_REGEX_PATTERN_1)
AMOUNT_MAIN_REGEX_1 = re.compile(AMOUNT_MAIN_REGEX_PATTERN_1)
AMOUNT_SUB_REGEX_1 = re.compile(AMOUNT_SUB_REGEX_PATTERN_1)
# model 2
PAIR_REGEX_2 = re.compile(PAIR_REGEX_PATTERN_2)
AMOUNT_MAIN_REGEX_2 = re.compile(AMOUNT_MAIN_REGEX_PATTERN_2)
AMOUNT_SUB_REGEX_2 = re.compile(AMOUNT_SUB_REGEX_PATTERN_2)
# model 3
COIN_REGEX_3 = re.compile(COIN_REGEX_PATTERN_3)
AMOUNT_REGEX_3 = re.compile(AMOUNT_REGEX_PATTERN_3)
# model 4
PAIR_REGEX_4 = re.compile(PAIR_REGEX_PATTERN_4)
AMOUNT_MAIN_WO_FEE_REGEX_4 = re.compile(AMOUNT_MAIN_WO_FEE_REGEX_PATTERN_4)
AMOUNT_SUB_WO_FEE_REGEX_4 = re.compile(AMOUNT_SUB_WO_FEE_REGEX_PATTERN_4)
AMOUNT_MAIN_W_FEE_REGEX_4 = re.compile(AMOUNT_MAIN_W_FEE_REGEX_PATTERN_4)
AMOUNT_SUB_W_FEE_REGEX_4 = re.compile(AMOUNT_SUB_W_FEE_REGEX_PATTERN_4)
AMOUNT_ZUABGANG_REGEX_4 = re.compile(AMOUNT_ZUABGANG_REGEX_PATTERN_4)
# model 5
PAIR_REGEX_5 = re.compile(PAIR_REGEX_PATTERN_5)
PRICE_AVERAGE_REGEX_5 = re.compile(PRICE_AVERAGE_REGEX_PATTERN_5)
AMOUNT_MAIN_REGEX_5 = re.compile(AMOUNT_MAIN_REGEX_PATTERN_5)
AMOUNT_SUB_REGEX_5 = re.compile(AMOUNT_SUB_REGEX_PATTERN_5)

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
# TIME_FORMAT.append('$b $d $Y $H:$M:$S %z')

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
