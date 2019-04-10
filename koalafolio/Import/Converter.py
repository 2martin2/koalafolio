# -*- coding: utf-8 -*-

import koalafolio.PcpCore.core as core
import koalafolio.PcpCore.settings as settings
import re, numbers, pandas
import koalafolio.Import.RegexPatterns as pat
import datetime, tzlocal, pytz
import dateutil

def exodusJsonToDataFrame(data):
    # txId, error, date, confirmations, meta, token, coinAmount, coinName, feeAmount, to, toCoin
    # toCoin: coin, coinAmount, fiatAmount,

    # DATE,TYPE,OUTAMOUNT,OUTCURRENCY,FEEAMOUNT,FEECURRENCY,OUTTXID,OUTTXURL,INAMOUNT,INCURRENCY,INTXID,INTXURL,ORDERID

    amountRegex = re.compile('^((-|\+|)(\d+)((\.\d+)|)((e(-|\+|)\d+)|)) (\w+)$')
    # convert dict
    newDictList = []
    for row in range(len(data)):
        dict = data[row]
        newDict = {}

        amountMatch = amountRegex.match(dict['coinAmount'])
        if amountMatch:
            amount = float(amountMatch.group(1))
            newDict['DATE'] = dict['date']
            if amount >= 0:  # input
                newDict['TYPE'] = 'deposit'
                newDict['INAMOUNT'] = amount
                newDict['INCURRENCY'] = amountMatch.group(9)
                newDict['INTXID'] = dict['txId']
            else:  # output
                newDict['TYPE'] = 'withdrawal'
                newDict['OUTAMOUNT'] = amount
                newDict['OUTCURRENCY'] = amountMatch.group(9)
                newDict['OUTTXID'] = dict['txId']

        if 'toCoin' in dict:  # trade
            amountMatch = amountRegex.match(dict['toCoin']['coinAmount'])
            if amountMatch:
                amount = float(amountMatch.group(1))
                newDict['TYPE'] = 'exchange'
                newDict['INAMOUNT'] = amount
                newDict['INCURRENCY'] = amountMatch.group(9)
                newDict['INTXID'] = dict['meta']['shapeshiftOrderId']
                newDict['ORDERID'] = dict['meta']['shapeshiftOrderId']

        # do not use fromCoin since these trades are already included in toCoin
        # if 'fromCoin' in dict:
        #     amountMatch = amountRegex.match(dict['fromCoin']['coinAmount'])
        #     if amountMatch:
        #         amount = float(amountMatch.group(1))
        #         newDict['TYPE'] = 'exchange'
        #         newDict['OUTAMOUNT'] = - amount
        #         newDict['OUTCURRENCY'] = amountMatch.group(9)
        #         newDict['OUTTXID'] = dict['meta']['shapeshiftOrderId']
        #         newDict['ORDERID'] = dict['meta']['shapeshiftOrderId']

        if 'feeAmount' in dict:  # fee
            amountMatch = amountRegex.match(dict['feeAmount'])
            if amountMatch:
                amount = float(amountMatch.group(1))
                newDict['FEEAMOUNT'] = amount
                newDict['FEECURRENCY'] = amountMatch.group(9)
                # newDict['feeAmount'] = dict['feeAmount']

        keys = ['DATE','TYPE','OUTAMOUNT','OUTCURRENCY','FEEAMOUNT','FEECURRENCY','OUTTXID',
                'OUTTXURL','INAMOUNT','INCURRENCY','INTXID','INTXURL','ORDERID']
        for key in keys:
            if key not in newDict:
                newDict[key] = 'nan'
        newDictList.append(newDict)

    return pandas.DataFrame(newDictList)

# %% exodus [DATE,TYPE,OUTAMOUNT,OUTCURRENCY,FEEAMOUNT,FEECURRENCY,OUTTXID,OUTTXURL,INAMOUNT,INCURRENCY,INTXID,INTXURL,ORDERID]
#             0     1       2         3         4           5         6        7        8       9         10      11     12
def modelCallback_exodus(headernames, dataFrame):
    tradeList = core.TradeList()
    feeList = core.TradeList()
    skippedRows = 0
    exchangeRegex = re.compile(r'^(exchange)$')
    for row in range(dataFrame.shape[0]):
        exchangeMatch = exchangeRegex.match(dataFrame[headernames[1]][row])  # check type
        isFee = str(dataFrame[headernames[4]][row]) != 'nan'
        if not exchangeMatch and not isFee:  # no trade and no fee
            skippedRows += 1
            continue  # skip row
        if exchangeMatch:  # if exchange
            tempTrade_out = core.Trade()  # out
            tempTrade_in = core.Trade()  # in
            # get id
            tempTrade_out.externId = str(dataFrame[headernames[6]][row])
            tempTrade_in.externId = str(dataFrame[headernames[10]][row])
            # get date
            tempTrade_out.date = convertDate(dataFrame[headernames[0]][row])
            tempTrade_in.date = convertDate(dataFrame[headernames[0]][row])
            # get type
            tempTrade_out.tradeType = 'trade'
            tempTrade_in.tradeType = 'trade'
            # get coin
            tempTrade_out.coin = str(dataFrame[headernames[3]][row])
            tempTrade_in.coin = str(dataFrame[headernames[9]][row])
            # swap Coin Name
            swapCoinName(tempTrade_out)
            swapCoinName(tempTrade_in)
            # get amount
            tempTrade_out.amount = dataFrame[headernames[2]][row]
            tempTrade_in.amount = dataFrame[headernames[8]][row]
            # set exchange and wallet
            exchange = 'shapeshift'
            tempTrade_out.exchange = tempTrade_in.exchange = 'shapeshift'
            tempTrade_out.wallet = tempTrade_in.wallet = 'exodus'
            # set id
            if not tempTrade_out.tradeID:
                tempTrade_out.generateID()
            if not tempTrade_in.tradeID:
                tempTrade_in.generateID()
            # add trades to tradeList
            if not tradeList.addTradePair(tempTrade_out, tempTrade_in):
                skippedRows += 1
        else:
            exchange = ''

        # fees
        if isFee:  # if fee
            fee = createFee(date=convertDate(dataFrame[headernames[0]][row]),
                            amountStr=dataFrame[headernames[4]][row],
                            maincoin=dataFrame[headernames[5]][row],
                            exchange=exchange,
                            wallet='exodus')
            fee.generateID()
            feeList.addTrade(fee)

    return tradeList, feeList, skippedRows

# %% kraken model: ["txid","ordertxid","pair","time","type","ordertype","price","cost","fee","vol","margin","misc","ledgers"]
def modelCallback_kraken(headernames, dataFrame):
    # seperate coin pair
    # "txid"	"ordertxid"	"pair"		"time"	"type"	"ordertype"	"price"		"cost"		"fee"	"vol"		"margin"	"misc"	"ledgers"
    # "x"	"x"			"XETHZEUR"	"x"		"buy"	"limit"		170.25000	851.25000	1.36200	5.00000000	0.00000		""		"x"
    # "x"	"x"			"XXBTZEUR"	"x"		"buy"	"limit"		5220.00000	3839.00171	6.14240	0.73544094	0.00000		""		"x"
    # "x"	"x"			"ADAEUR"	"x"		"buy"	"limit"		0.0400000	1000.00171	1.14240	0.73544094	0.00000		""		"x"

    COIN_PAIR_REGEX = re.compile('^X([a-z|A-Z]*)Z([a-z|A-Z]*)$')
    COIN_PAIR_REGEX_2 = re.compile('^([a-z|A-Z]{3})([a-z|A-Z]{3})$')

    for row in range(dataFrame.shape[0]):

        coinPairMatch = COIN_PAIR_REGEX.match(dataFrame[headernames[2]][row])
        if coinPairMatch:
            subcoin = coinPairMatch.group(1)
            maincoin = coinPairMatch.group(2)
            dataFrame.at[row, headernames[2]] = subcoin + '/' + maincoin
        else:
            coinPairMatch = COIN_PAIR_REGEX_2.match(dataFrame[headernames[2]][row])
            if coinPairMatch:
                subcoin = coinPairMatch.group(1)
                maincoin = coinPairMatch.group(2)
                dataFrame.at[row, headernames[2]] = subcoin + '/' + maincoin
            else:
                raise ValueError('kraken market pair does not fit the expected pattern')

    headernames_m0 = []
    headernames_m0.append(headernames[3])  # date
    headernames_m0.append(headernames[4])  # type
    headernames_m0.append(headernames[2])  # pair
    headernames_m0.append(headernames[6])  # average price
    headernames_m0.append(headernames[9])  # amount
    headernames_m0.append(headernames[0])  # id
    headernames_m0.append(headernames[7])  # total
    headernames_m0.append(headernames[8])  # fee
    headernames_m0.append('')  # no feecoin
    headernames_m0.append('')  # state

    tradeList, feeList, skippedRows = modelCallback_0(headernames_m0, dataFrame)

    for trade in tradeList:
        trade.exchange = 'kraken'
    for fee in feeList:
        fee.exchange = 'kraken'

    return tradeList, feeList, skippedRows


# %% binance model: ['Date(UTC)', 'Market', 'Type', 'Price', 'Amount', 'Total', 'Fee', 'Fee Coin']
def modelCallback_binance(headernames, dataFrame):
    # seperate coin pair
    #    Date(UTC)	Market	Type	Price	Amount	Total	Fee	    Fee Coin
    #    xx	        XXXETH	BUY	    x.xxxx	xxxx	xx.xx	x.xx	BNB
    #    xx	        XXXUSDT	BUY	    x.xxxx	xxxx	xx.xx	x.xx	BNB

    COIN_PAIR_REGEX = re.compile('^([a-z|A-Z]*)([a-z|A-Z]{3})$')
    USDT_REGEX = re.compile('^([a-z|A-Z]*)(USDT)$')

    for row in range(dataFrame.shape[0]):

        usdtMatch = USDT_REGEX.match(dataFrame[headernames[1]][row])
        if usdtMatch:
            dataFrame[headernames[1]][row] = usdtMatch.group(1) + '/' + usdtMatch.group(2)
        else:
            coinPairMatch = COIN_PAIR_REGEX.match(dataFrame[headernames[1]][row])
            if coinPairMatch:
                dataFrame.at[row, headernames[1]] = coinPairMatch.group(1) + '/' + coinPairMatch.group(2)
            else:
                raise ValueError('binance market pair does not fit the expected pattern')

    headernames_m0 = []
    headernames_m0.append(headernames[0])  # date
    headernames_m0.append(headernames[2])  # type
    headernames_m0.append(headernames[1])  # pair
    headernames_m0.append(headernames[3])  # average price
    headernames_m0.append(headernames[4])  # amount
    headernames_m0.append('')  # no id
    headernames_m0.append(headernames[5])  # total
    headernames_m0.append(headernames[6])  # fee
    headernames_m0.append(headernames[7])  # feecoin
    headernames_m0.append('')  # state

    tradeList, feeList, skippedRows = modelCallback_0(headernames_m0, dataFrame)

    for trade in tradeList:
        trade.exchange = 'binance'
        # import timestamp as utc
        timestamp = trade.date
        timestamp = timestamp.replace(tzinfo=pytz.UTC)
        myTimezone = tzlocal.get_localzone()
        timestamp = timestamp.astimezone(myTimezone)
        trade.date = timestamp
        # update id
        trade.generateID()
    for fee in feeList:
        fee.exchange = 'binance'
        # import timestamp as utc
        timestamp = fee.date
        timestamp = timestamp.replace(tzinfo=pytz.UTC)
        myTimezone = tzlocal.get_localzone()
        timestamp = timestamp.astimezone(myTimezone)
        fee.date = timestamp
        # update id
        trade.generateID()

    return tradeList, feeList, skippedRows


# %% poloniex model: ['Date', 'Market', 'Category', 'Type', 'Price', 'Amount', 'Total', 'Fee', 'Order Number', 'Base Total Less Fee', 'Quote Total Less Fee']
def modelCallback_poloniex(headernames, dataFrame):
    #   Date, Market,  Category,  Type,  Price,       Amount,           Total,          Fee,    OrderNumber,   BaseTotalLessFee,  QuoteTotalLessFee
    #   xxx,  EOS/BTC, Exchange,  Buy,   0.00073222,  428.73542776,     0.31392865,     0.1%,   2170649379,    -0.31392865,       428.30669234
    #   xxx,  BCN/BTC, Exchange,  Sell,  0.00000072,  857643.36794962,  0.61750322,     0.25%,  9246260491,    0.61595947,        -857643.36794962

    feecoins = []
    for row in range(dataFrame.shape[0]):
        coinSub = re.match(r'^(.*)/.*$', dataFrame[headernames[1]][row]).group(1).upper()
        coinMain = re.match(r'^.*/(.*)$', dataFrame[headernames[1]][row]).group(1).upper()
        feeProz = abs(float(pat.NUMBER_REGEX.match(dataFrame[headernames[7]][row]).group(1)))
        # get sign
        if re.match(r'^.*?(SELL).*?$', dataFrame[headernames[3]][row], re.IGNORECASE):
            feecoin = coinMain
            feeamount = dataFrame[headernames[6]][row] * (feeProz / 100)
        elif re.match(r'^.*?(BUY).*?$', dataFrame[headernames[3]][row], re.IGNORECASE):
            feecoin = coinSub
            feeamount = dataFrame[headernames[5]][row] * (feeProz / 100)
        else:  # invalid type
            feecoin = ''
            feeamount = 0

        feecoins.append(feecoin)
        dataFrame.at[row, headernames[7]] = feeamount

    headernames.append('FeeCoin')
    dataFrame = dataFrame.assign(FeeCoin=pandas.Series(feecoins))

    headernames_m0 = []
    headernames_m0.append(headernames[0])  # date
    headernames_m0.append(headernames[3])  # type
    headernames_m0.append(headernames[1])  # pair
    headernames_m0.append(headernames[4])  # average price
    headernames_m0.append(headernames[10])  # amount
    headernames_m0.append(headernames[8])  # id
    headernames_m0.append(headernames[9])  # total
    headernames_m0.append(headernames[7])  # fee
    headernames_m0.append(headernames[11])  # no feecoin
    headernames_m0.append('')  # state

    tradeList, feeList, skippedRows = modelCallback_0(headernames_m0, dataFrame)

    for trade in tradeList:
        trade.exchange = 'poloniex'
    for fee in feeList:
        fee.exchange = 'poloniex'

    return tradeList, feeList, skippedRows


# %% model 0: Date, Type, Pair, Average Price, Amount, (ID), (Total), (Fee), (FeeCoin), (State)
def modelCallback_0(headernames, dataFrame):
    tradeList = core.TradeList()
    feeList = core.TradeList()
    skippedRows = 0
    for row in range(dataFrame.shape[0]):
        if headernames[9]:  # if state included
            if re.match(r'^.*?(CANCELED).*?$', dataFrame[headernames[9]][row], re.IGNORECASE):  # check state
                skippedRows += 1
                continue  # skip row
        tempTrade_sub = core.Trade()  # sub
        tempTrade_main = core.Trade()  # main
        # get id
        if headernames[5]:
            tempTrade_sub.externId = str(dataFrame[headernames[5]][row])
            tempTrade_main.externId = str(dataFrame[headernames[5]][row])
        # get date
        tempTrade_sub.date = convertDate(dataFrame[headernames[0]][row])
        tempTrade_main.date = convertDate(dataFrame[headernames[0]][row])
        # get type
        tempTrade_sub.tradeType = 'trade'
        tempTrade_main.tradeType = 'trade'
        # get coin
        tempTrade_sub.coin = re.match(r'^(.*)(/|-).*$', dataFrame[headernames[2]][row]).group(1).upper()
        tempTrade_main.coin = re.match(r'^.*(/|-)(.*)$', dataFrame[headernames[2]][row]).group(2).upper()
        # swap Coin Name
        swapCoinName(tempTrade_sub)
        swapCoinName(tempTrade_main)
        # get amount
        if isinstance(dataFrame[headernames[4]][row], numbers.Number):  # if amount is number
            amount = abs(dataFrame[headernames[4]][row])
        else:  # now number so use regex to extract the number
            amount = abs(float(pat.NUMBER_REGEX.match(dataFrame[headernames[4]][row]).group(1)))
        if isinstance(dataFrame[headernames[3]][row], numbers.Number):  # if price is number
            price = abs(dataFrame[headernames[3]][row] * amount)
        else:  # no number so use regex
            price = abs(float(pat.NUMBER_REGEX.match(dataFrame[headernames[3]][row]).group(1)) * amount)
        # get sign
        if re.match(r'^.*?(SELL).*?$', dataFrame[headernames[1]][row], re.IGNORECASE):
            tempTrade_sub.amount = -amount
            tempTrade_main.amount = price
        elif re.match(r'^.*?(BUY).*?$', dataFrame[headernames[1]][row], re.IGNORECASE):
            tempTrade_sub.amount = amount
            tempTrade_main.amount = -price
        else:  # invalid type
            skippedRows += 1
            continue  # skip row
        # set value to zero
        #        tempTrade_sub = [0,0,0]
        #        tempTrade_main = [0,0,0]
        # set id
        if not tempTrade_sub.tradeID:
            tempTrade_sub.generateID()
        if not tempTrade_main.tradeID:
            tempTrade_main.generateID()
        # add trades to tradeList
        if not tradeList.addTradePair(tempTrade_sub, tempTrade_main):
            skippedRows += 1

        # fees
        try:
            if headernames[7]:  # if fee
                if headernames[8]:  # if fee coin
                    # use fee coin
                    feecoin = dataFrame[headernames[8]][row]
                else:  # no fee coin
                    # use main coin
                    feecoin = tempTrade_main.coin
                # set coin amount
                fee = createFee(date=tempTrade_main.date, amountStr=dataFrame[headernames[7]][row], maincoin=feecoin,
                                subcoin=tempTrade_sub.coin,
                                exchange=tempTrade_main.exchange, externId=tempTrade_main.externId)
                fee.generateID()
                feeList.addTrade(fee)
        except Exception as ex:  # do not skip line if error, just ignore fee
            print('error in Converter: ' + str(ex))

    return tradeList, feeList, skippedRows


# %% model 1: Date, Type, Exchange, Average Price, Amount, (ID), (Total), (Fee), (FeeCoin)
def modelCallback_1(headernames, dataFrame):
    headernames.append('')
    for row in range(dataFrame.shape[0]):
        coin_sub = re.match(r'^.*-(.*)$', dataFrame[headernames[2]][row]).group(1).upper()
        coin_main = re.match(r'^(.*)-.*$', dataFrame[headernames[2]][row]).group(1).upper()
        dataFrame.at[row, headernames[2]] = coin_sub + r'/' + coin_main

    return modelCallback_0(headernames, dataFrame)


# %% model 2: Date, Type, Pair, Amount sub, Amount main, (id), (fee), (feecoin)
def modelCallback_2(headernames, dataFrame):
    tradeList = core.TradeList()
    feeList = core.TradeList()
    skippedRows = 0
    for row in range(dataFrame.shape[0]):
        tempTrade_sub = core.Trade()  # sub
        tempTrade_main = core.Trade()  # main
        # get id
        if headernames[5]:
            tempTrade_sub.externId = str(dataFrame[headernames[5]][row])
            tempTrade_main.externId = str(dataFrame[headernames[5]][row])
        # get date
        tempTrade_sub.date = convertDate(dataFrame[headernames[0]][row])
        tempTrade_main.date = convertDate(dataFrame[headernames[0]][row])
        # get type
        tempTrade_sub.tradeType = 'trade'
        tempTrade_main.tradeType = 'trade'
        # get coin
        tempTrade_sub.coin = re.match(r'^(.*)/.*$', dataFrame[headernames[2]][row]).group(1).upper()
        tempTrade_main.coin = re.match(r'^.*/(.*)$', dataFrame[headernames[2]][row]).group(1).upper()
        # swap Coin Name
        swapCoinName(tempTrade_sub)
        swapCoinName(tempTrade_main)
        # get amount sub
        if isinstance(dataFrame[headernames[3]][row], numbers.Number):  # if amount is number
            amount = abs(dataFrame[headernames[3]][row])
        else:  # now number so use regex to extract the number
            amount = abs(float(pat.NUMBER_REGEX.match(dataFrame[headernames[3]][row]).group(1)))
        # get amount main
        if isinstance(dataFrame[headernames[4]][row], numbers.Number):  # if price is number
            price = abs(dataFrame[headernames[4]][row])
        else:  # no number so use regex
            price = abs(float(pat.NUMBER_REGEX.match(dataFrame[headernames[4]][row]).group(1)))
        # get sign
        if re.match(r'^.*?(SELL).*?$', dataFrame[headernames[1]][row], re.IGNORECASE):
            tempTrade_sub.amount = -amount
            tempTrade_main.amount = price
        elif re.match(r'^.*?(BUY).*?$', dataFrame[headernames[1]][row], re.IGNORECASE):
            tempTrade_sub.amount = amount
            tempTrade_main.amount = -price
        else:  # invalid type
            skippedRows += 1
            continue  # skip row
        # set id
        if not tempTrade_sub.tradeID:
            tempTrade_sub.generateID()
        if not tempTrade_main.tradeID:
            tempTrade_main.generateID()
        # add trades to tradeList
        if not tradeList.addTradePair(tempTrade_sub, tempTrade_main):
            skippedRows += 1

        # fees
        try:
            if headernames[6]:  # if fee
                if headernames[7]:  # if fee coin
                    # use fee coin
                    feecoin = dataFrame[headernames[7]][row]
                else:  # no fee coin
                    # use main coin
                    feecoin = tempTrade_main.coin
                # set coin amount
                fee = createFee(date=tempTrade_main.date, amountStr=dataFrame[headernames[6]][row], maincoin=feecoin,
                                subcoin=tempTrade_sub.coin,
                                exchange=tempTrade_main.exchange, externId=tempTrade_main.externId)
                fee.generateID()
                feeList.addTrade(fee)
        except Exception as ex:  # do not skip line if error, just ignore fee
            print('error in Converter: ' + str(ex))

    return tradeList, feeList, skippedRows


# %% model 3: Date, type, Coin, Amount, (id), (fee)
def modelCallback_3(headernames, dataFrame):
    tradeList = core.TradeList()
    feeList = core.TradeList()
    skippedRows = 0
    for row in range(dataFrame.shape[0]):
        tempTrade_sub = core.Trade()
        # get id
        if headernames[4]:
            tempTrade_sub.externId = str(dataFrame[headernames[4]][row])
        # get date
        tempTrade_sub.date = convertDate(dataFrame[headernames[0]][row])
        # get type
        tempTrade_sub.tradeType = 'trade'
        # get coin
        tempTrade_sub.coin = (dataFrame[headernames[2]][row]).upper()
        # swap Coin Name
        swapCoinName(tempTrade_sub)
        # get amount sub
        if isinstance(dataFrame[headernames[3]][row], numbers.Number):  # if amount is number
            amount = dataFrame[headernames[3]][row]
        else:  # now number so use regex to extract the number
            amount = float(pat.NUMBER_REGEX.match(dataFrame[headernames[3]][row]).group(1))
        if amount:
            tempTrade_sub.amount = amount
        else:
            skippedRows += 1
            continue
        # add row to tradeList
        if not tempTrade_sub.tradeID:
            tempTrade_sub.generateID()
        if not tradeList.addTrade(tempTrade_sub):
            skippedRows += 1

        # fees
        try:
            if headernames[5]:  # if fee
                feecoin = tempTrade_sub.coin
                fee = createFee(date=tempTrade_sub.date, amountStr=dataFrame[headernames[5]][row], maincoin=feecoin,
                                exchange=tempTrade_sub.exchange, externId=tempTrade_sub.externId)
                fee.generateID()
                feeList.addTrade(fee)
        except Exception as ex:  # do not skip line if error, just ignore fee
            print('error in Converter: ' + str(ex))

    return tradeList, feeList, skippedRows


# %% model 4 (bitcoin.de): Date, Type, Pair, amount_main_wo, amount_sub_wo, amount_main_w_fees, amount_sub_w_fees,
# (ID), (ZuAbgang), (amount_main_w_fees_fidor), (einheit_amount_main_w_fee), (einheit_amount_main_wo_fee), (einheit kurs)
def modelCallback_4(headernames, dataFrame):
    tradeList = core.TradeList()
    feeList = core.TradeList()
    skippedRows = 0
    for row in range(dataFrame.shape[0]):
        if 'Gebühr' in dataFrame[headernames[1]][row]:
            # fees
            date = convertDate(dataFrame[headernames[0]][row])
            if headernames[7]:
                externId = str(dataFrame[headernames[7]][row])
            fees = dataFrame[headernames[8]][row]
            coin = str(dataFrame[headernames[2]][row])
            fee = createFee(date=date, amountStr=fees, maincoin=coin, exchange='bitcoinde', externId=externId)
            fee.generateID()
            feeList.addTrade(fee)
        else:
            tempTrade_sub = core.Trade()  # sub
            tempTrade_main = core.Trade()  # main
            # get id
            if headernames[7]:
                tempTrade_sub.externId = str(dataFrame[headernames[7]][row])
                tempTrade_main.externId = str(dataFrame[headernames[7]][row])
            # get date
            tempTrade_sub.date = convertDate(dataFrame[headernames[0]][row])
            tempTrade_main.date = convertDate(dataFrame[headernames[0]][row])
            # set type
            tempTrade_sub.tradeType = 'trade'
            tempTrade_main.tradeType = 'trade'
            # check content type
            isBuy = False
            if re.match(r'^.*?(Kauf).*?$', dataFrame[headernames[1]][row], re.IGNORECASE):
                isBuy = True
            elif re.match(r'^.*?(Verkauf).*?$', dataFrame[headernames[1]][row], re.IGNORECASE):
                isBuy = False
            else:  # invalid type
                skippedRows += 1
                continue
            # get coin
            if headernames[12]:
                coinPairIndex = 12
            else:
                coinPairIndex = 2
            tempTrade_sub.coin = re.match(r'^(.*) / .*$', dataFrame[headernames[coinPairIndex]][row]).group(1).upper()
            tempTrade_main.coin = re.match(r'^.* / (.*)$', dataFrame[headernames[coinPairIndex]][row]).group(1).upper()
            # swap Coin Name
            swapCoinName(tempTrade_sub)
            swapCoinName(tempTrade_main)
            # get amount wo fees
            if isinstance(dataFrame[headernames[4]][row], numbers.Number):  # if amount is number
                amount_wo_fees = abs(dataFrame[headernames[4]][row])
            else:  # now number so use regex to extract the number
                amount_wo_fees = abs(float(pat.NUMBER_REGEX.match(dataFrame[headernames[4]][row]).group(1)))
            # get price wo fees
            if isinstance(dataFrame[headernames[3]][row], numbers.Number):  # if price is number
                price_wo_fees = abs(dataFrame[headernames[3]][row])
            else:  # no number so use regex
                price_wo_fees = abs(float(pat.NUMBER_REGEX.match(dataFrame[headernames[3]][row]).group(1)))
            # get amount w fees
            if isinstance(dataFrame[headernames[6]][row], numbers.Number):  # if amount is number
                amount_w_fees = abs(dataFrame[headernames[6]][row])
            else:  # now number so use regex to extract the number
                amount_w_fees = abs(float(pat.NUMBER_REGEX.match(dataFrame[headernames[6]][row]).group(1)))
            # get price w fees
            if headernames[9]:  # if fidor fee included
                mainFeeIndex = 9
            else:
                mainFeeIndex = 5
            if isinstance(dataFrame[headernames[mainFeeIndex]][row], numbers.Number):  # if price is number
                price_w_fees = abs(dataFrame[headernames[mainFeeIndex]][row])
            else:  # no number so use regex
                price_w_fees = abs(float(pat.NUMBER_REGEX.match(dataFrame[headernames[mainFeeIndex]][row]).group(1)))
            # get sign
            if isBuy == True:
                tempTrade_sub.amount = amount_wo_fees
                tempTrade_main.amount = -price_w_fees
                fees_sub = amount_wo_fees - amount_w_fees
                fees_main = price_wo_fees - price_w_fees
            else:
                tempTrade_sub.amount = amount_w_fees
                tempTrade_main.amount = -price_wo_fees
                fees_sub = -(amount_wo_fees - amount_w_fees)
                fees_main = -(price_wo_fees - price_w_fees)
            # set exchange
            tempTrade_main.exchange = 'bitcoinde'
            tempTrade_sub.exchange = 'bitcoinde'
            # set id
            if not tempTrade_sub.tradeID:
                tempTrade_sub.generateID()
            if not tempTrade_main.tradeID:
                tempTrade_main.generateID()
            # add trades to tradeList
            if not tradeList.addTradePair(tempTrade_sub, tempTrade_main):
                skippedRows += 1

            # fees
            try:
                # get fee
                feeMain = createFee(date=tempTrade_main.date, amountStr=fees_main, maincoin=tempTrade_main.coin,
                                    exchange='bitcoinde', externId=tempTrade_main.externId)
                feeSub = createFee(date=tempTrade_sub.date, amountStr=fees_sub, maincoin=tempTrade_sub.coin,
                                   exchange='bitcoinde', externId=tempTrade_sub.externId)
                feeMain.generateID()
                feeSub.generateID()
                feeList.addTrade(feeMain)
                feeList.addTrade(feeSub)
            except Exception as ex:  # do not skip line if error, just ignore fee
                print('error in Converter: ' + str(ex))

    return tradeList, feeList, skippedRows


# %% model 5: Date, Pair, Average Price, Amount, (ID), (Total), (Fee), (FeeCoin), (State)
def modelCallback_5(headernames, dataFrame):
    tradeList = core.TradeList()
    feeList = core.TradeList()
    skippedRows = 0
    for row in range(dataFrame.shape[0]):
        if headernames[8]:  # if state included
            if re.match(r'^.*?(CANCELED).*?$', dataFrame[headernames[8]][row], re.IGNORECASE):  # check state
                skippedRows += 1
                continue  # skip row
        tempTrade_sub = core.Trade()  # sub
        tempTrade_main = core.Trade()  # main
        # get id
        if headernames[4]:
            tempTrade_sub.externId = str(dataFrame[headernames[4]][row])
            tempTrade_main.externId = str(dataFrame[headernames[4]][row])
        # get date
        tempTrade_sub.date = convertDate(dataFrame[headernames[0]][row])
        tempTrade_main.date = convertDate(dataFrame[headernames[0]][row])
        # get type
        tempTrade_sub.tradeType = 'trade'
        tempTrade_main.tradeType = 'trade'
        # get coin
        tempTrade_sub.coin = re.match(r'^(.*)/.*$', dataFrame[headernames[1]][row]).group(1).upper()
        tempTrade_main.coin = re.match(r'^.*/(.*)$', dataFrame[headernames[1]][row]).group(1).upper()
        # swap Coin Name
        swapCoinName(tempTrade_sub)
        swapCoinName(tempTrade_main)
        # get amount
        if isinstance(dataFrame[headernames[3]][row], numbers.Number):  # if amount is number
            amount = dataFrame[headernames[3]][row]
        else:  # now number so use regex to extract the number
            amount = float(pat.NUMBER_REGEX.match(dataFrame[headernames[3]][row]).group(1))
        if isinstance(dataFrame[headernames[2]][row], numbers.Number):  # if price is number
            price = dataFrame[headernames[2]][row] * amount * -1
        else:  # no number so use regex
            price = float(pat.NUMBER_REGEX.match(dataFrame[headernames[2]][row]).group(1)) * amount * -1
        tempTrade_sub.amount = amount
        tempTrade_main.amount = price
        # set id
        if not tempTrade_sub.tradeID:
            tempTrade_sub.generateID()
        if not tempTrade_main.tradeID:
            tempTrade_main.generateID()
        # add trades to tradeList
        if not tradeList.addTradePair(tempTrade_sub, tempTrade_main):
            skippedRows += 1

        # fees
        try:
            if headernames[6]:  # if fee
                if headernames[7]:  # if fee coin
                    # use fee coin
                    feecoin = dataFrame[headernames[7]][row]
                else:  # no fee coin
                    # use main coin
                    feecoin = tempTrade_main.coin
                # set coin amount
                fee = createFee(date=tempTrade_main.date, amountStr=dataFrame[headernames[6]][row], maincoin=feecoin,
                                subcoin=tempTrade_sub.coin,
                                exchange=tempTrade_main.exchange, externId=tempTrade_main.externId)
                fee.generateID()
                feeList.addTrade(fee)
        except Exception as ex:  # do not skip line if error, just ignore fee
            print('error in Converter: ' + str(ex))

    return tradeList, feeList, skippedRows

# %% model template1:
# "date","type","buy amount","buy cur","sell amount","sell cur",("exchange"),("fee amount"),("fee currency")
#   0       1       2           3         4             5            6              7               8
def modelCallback_Template1(headernames, dataFrame):
    tradeList = core.TradeList()
    feeList = core.TradeList()
    skippedRows = 0

    for row in range(dataFrame.shape[0]):
        try:
            date = convertDate(dataFrame[headernames[0]][row])
            tradeType = dataFrame[headernames[1]][row].lower()
            if headernames[6]:
                exchange = str(dataFrame[headernames[6]][row]).lower()
                if exchange == 'nan':
                    exchange = ''
            if dataFrame[headernames[1]][row].lower() == 'trade':
                tempTrade_sell = core.Trade()  # sell
                tempTrade_buy = core.Trade()  # buy
                # get date
                tempTrade_sell.date = date
                tempTrade_buy.date = date
                # get type
                tempTrade_sell.tradeType = 'trade'
                tempTrade_buy.tradeType = 'trade'
                # get coin
                tempTrade_sell.coin = (dataFrame[headernames[5]][row]).upper()
                tempTrade_buy.coin = (dataFrame[headernames[3]][row]).upper()
                # swap Coin Name
                swapCoinName(tempTrade_sell)
                swapCoinName(tempTrade_buy)
                # get amount
                tempTrade_sell.amount = - abs(dataFrame[headernames[4]][row])
                tempTrade_buy.amount = abs(dataFrame[headernames[2]][row])
                # set exchange
                tempTrade_sell.exchange = exchange
                tempTrade_buy.exchange = exchange
                # set id
                if not tempTrade_sell.tradeID:
                    tempTrade_sell.generateID()
                if not tempTrade_buy.tradeID:
                    tempTrade_buy.generateID()
                # add trades to tradeList
                if not tradeList.addTradePair(tempTrade_sell, tempTrade_buy):
                    skippedRows += 1
        except Exception as ex:
            print('error in Converter Template1: ' + str(ex))
            skippedRows += 1

        # fees
        try:
            if headernames[7] and str(dataFrame[headernames[7]][row]) != 'nan':  # if fee
                if headernames[8] and str(dataFrame[headernames[8]][row]) != 'nan':  # if fee coin
                    # use fee coin
                    feecoin = dataFrame[headernames[8]][row]
                else:  # no fee coin
                    # use buy coin
                    feecoin = tempTrade_buy.coin
                # set coin amount
                fee = createFee(date=date, amountStr=dataFrame[headernames[7]][row], maincoin=feecoin,
                                subcoin=tempTrade_sell.coin,
                                exchange=exchange)
                fee.generateID()
                feeList.addTrade(fee)
        except Exception as ex:  # do not skip line if error, just ignore fee
            print('error in Converter Template1: ' + str(ex))

    return tradeList, feeList, skippedRows

# %% model tradeList:
# 'date', 'type', 'coin', 'amount', 'id', 'tradePartnerId', 'valueLoaded', 'exchange', 'externId', 'wallet'
#   0       1       2       3         4          5               6          7           8              9
def modelCallback_TradeList(headernames, dataFrame):
    tradeList = core.TradeList()
    feeList = core.TradeList()
    skippedRows = 0

    for row in range(dataFrame.shape[0]):
        try:
            trade = core.Trade()

            # date
            trade.date = convertDate(dataFrame[headernames[0]][row])
            # type
            trade.tradeType = dataFrame[headernames[1]][row]
            trade.coin = dataFrame[headernames[2]][row]
            trade.amount = float(dataFrame[headernames[3]][row])


            trade.valueLoaded = False
            if headernames[6]:
                valueLoaded = dataFrame[headernames[6]][row]
                if valueLoaded:
                    headers = dataFrame.columns.tolist()
                    keysImport = []
                    valueHeaders = []
                    for header in headers:  # check all header for included historical values
                        valueMatch = pat.TRADELIST_VALUE_REGEX.match(header)
                        if valueMatch:
                            valueHeaders.append(valueMatch.group(0))
                            keysImport.append(valueMatch.group(1))

                    trade.valueLoaded = True
                    for key in core.CoinValue():  # check if all needed currencies are included
                        if key not in keysImport:
                            trade.valueLoaded = False

                    for valueInd in range(len(valueHeaders)):  # load all included historical values
                        trade.setValue(keysImport[valueInd], float(dataFrame[valueHeaders[valueInd]][row]))

            # exchange
            if headernames[7]:
                exchange = str(dataFrame[headernames[7]][row])
                if exchange != 'nan':
                    trade.exchange = exchange
            # extern id
            if headernames[8]:
                externId = str(dataFrame[headernames[8]][row])
                if externId != 'nan':
                    trade.externId = externId
            # wallet
            if headernames[9]:
                wallet = str(dataFrame[headernames[9]][row])
                if wallet != 'nan':
                    trade.wallet = wallet

            # id
            if headernames[4]:
                trade.tradeID = str(dataFrame[headernames[4]][row])
            else:
                trade.generateID()
            # partner id
            if headernames[5]:
                tradePartnerId = str(dataFrame[headernames[5]][row])
                if tradePartnerId != 'nan':
                    trade.tradePartnerId = tradePartnerId

            swapCoinName(trade)

            if trade.tradeType == 'fee':
                feeList.addTrade(trade)
            else:
                tradeList.addTrade(trade)
        except Exception as ex:
            print('error in Converter: ' + str(ex))
            skippedRows += 1

    return tradeList, feeList, skippedRows



# %% functions
def convertDate(dateString, useLocalTime=True):
    # check if pandas time pattern fits
    #    match = pat.Pandas_TIME_REGEX.match(dateString)
    timestamp = None
    try:  # try dateutil parser
        timestamp = dateutil.parser.parse(dateString)
    except ValueError:  # manuel parsing
        print('manuel parsing')
        if pat.Pandas_TIME_REGEX.match(dateString):
            timestamp = pandas.to_datetime(dateString, utc=True)
        for i in range(len(pat.TIME_REGEX)):
            tempMatch = pat.TIME_REGEX[i].match(dateString)
            if tempMatch:
                # correct wrong formats
                if i == pat.TIME_SPECIAL_PATTERN_INDEX[0]:
                    groups = tempMatch.group
                    dateString = groups(1) + '0' + groups(2)
                elif i == pat.TIME_SPECIAL_PATTERN_INDEX[1]:
                    groups = tempMatch.group
                    hour = groups(5)
                    if groups(7).upper() == 'PM':
                        hour = str(int(groups(5))+12)
                        if hour == '24':
                            hour = '00'
                    dateString = ""
                    if len(groups(1)) == 1:
                        dateString += '0' + groups(1) + groups(2)
                    else:
                        dateString += groups(1) + groups(2)
                    if len(groups(3)) == 1:
                        dateString += '0' + groups(3) + groups(4)
                    else:
                        dateString += groups(3) + groups(4)
                    if len(hour) == 1:
                        dateString += '0' + hour + groups(6)
                    else:
                        dateString += hour + groups(6)

                elif i == pat.TIME_SPECIAL_PATTERN_INDEX[2]:
                    groups = tempMatch.group
                    dateString = groups(1) + groups(3)
                elif i == pat.TIME_SPECIAL_PATTERN_INDEX[3]:
                    groups = tempMatch.group
                    dateString = groups(1)
                elif i == pat.TIME_SPECIAL_PATTERN_INDEX[4]:
                    groups = tempMatch.group
                    dateString = groups(1) + groups(3) + groups(2) + ' ' + groups(5)
                elif i == pat.TIME_SPECIAL_PATTERN_INDEX[5]:
                    groups = tempMatch.group
                    dateString = groups(1) + ' ' + groups(2) + ' +0000'
                # convert to datetime
                timestamp = datetime.datetime.strptime(dateString, pat.TIME_FORMAT[i])
                break
    if timestamp:
        # if no info about timezone included
        if not timestamp.tzinfo:
            # use local/UTC timezone (could cause matching error!)
            if useLocalTime:
                myTimezone = tzlocal.get_localzone()
                timestamp = myTimezone.localize(timestamp)
            #                myTimezone = datetime.timezone.now().astimezone().tzinfo
            #                timestamp = timestamp.replace(tzingo=myTimezone)
            else:  # use UTC
                timestamp = timestamp.replace(tzinfo=pytz.UTC)
                myTimezone = tzlocal.get_localzone()
                timestamp = timestamp.astimezone(myTimezone)
        else:
            # convert to system timezone
            myTimezone = tzlocal.get_localzone()
            timestamp = timestamp.astimezone(myTimezone)
    else:
        raise SyntaxError("date format not supported")
    return timestamp


# dateString = 'Wed Jun 27 17:16:39 CST 2018'
# date = convertDate(dateString)


def swapCoinName(trade):
    try:
        if trade.coin in settings.mySettings.coinSwapDict():
            trade.coin = settings.mySettings.coinSwapDict()[trade.coin]
    except Exception as ex:
        print('error in Converter: ' + str(ex))


def createTrades(tradeId='', externId=''):
    pass


def createFee(date, amountStr, maincoin, exchange, subcoin=None, wallet='', feeId='', externId=''):
    fee = core.Trade()
    fee.tradeID = feeId
    fee.externId = externId
    fee.tradeType = 'fee'
    fee.date = date
    fee.coin = maincoin
    if isinstance(amountStr, numbers.Number):  # if amount is number
        amount = - abs(amountStr)
    else:  # no number so use regex to extract the number
        feeMatch = pat.NUMBER_REGEX.match(amountStr)
        # check standard coins in fee value
        if subcoin:
            stdcoins = ['BTC', 'BNB', 'ETH', maincoin, subcoin]
        else:
            stdcoins = ['BTC', 'BNB', 'ETH', maincoin]
        for stdcoin in stdcoins:
            if stdcoin in feeMatch.group(4).upper():
                fee.coin = stdcoin  # use this coin as fee coin
        amount = - abs(float(pat.NUMBER_REGEX.match(amountStr).group(1)))
    fee.amount = amount
    fee.exchange = exchange
    fee.wallet = wallet
    swapCoinName(fee)
    return fee
