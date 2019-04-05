# -*- coding: utf-8 -*-

import pandas, hashlib, threading
import koalafolio.web.cryptocompareApi as ccapi
import koalafolio.PcpCore.settings as settings
import koalafolio.Import.Converter as converter
import koalafolio.PcpCore.logger as logger
import datetime
from dateutil.relativedelta import relativedelta

# constants
EXACT = 0
DAYWISE = 1


# tradeList: ['id', 'date', 'type', 'coin', 'amount', 'value_*' ]
def initTradeList(data=None):
    myCoinValue = CoinValue()
    myColumns = ['id', 'date', 'type', 'coin', 'amount'] + ['value' + key for key in myCoinValue.value]
    if data:
        return pandas.DataFrame(data, columns=myColumns)
    else:
        return pandas.DataFrame(columns=myColumns)


# tradeListComplete: ['id', 'date', 'type', 'coin', 'amount', 'value_*', valueLoaded ]
def initTradeListComplete(data=None):
    myCoinValue = CoinValue()
    myColumns = ['id', 'date', 'type', 'coin', 'amount'] + ['value' + key for key in myCoinValue.value] \
                + ['valueLoaded', 'tradePartnerId', 'exchange', 'externId', 'wallet']
    if data:
        return pandas.DataFrame(data, columns=myColumns)
    else:
        return pandas.DataFrame(columns=myColumns)


def initFeeList():
    myCoinValue = CoinValue()
    return pandas.DataFrame(columns=['id', 'date', 'coin', 'fee'] + ['value' + key for key in myCoinValue.value])


# coinListComplete: [ 'coin', 'balance', 'currentValue_*']
def initCoinList(data=None):
    myCoinValue = CoinValue()
    myColumns = ['coin', 'balance'] + ['currentValue' + key for key in myCoinValue.value]
    if data:
        return pandas.DataFrame(data, columns=myColumns)
    else:
        return pandas.DataFrame(columns=myColumns)


# coinListComplete: [ 'coin', 'balance', 'initialValue_*', 'currentValue_*']
def initCoinListComplete(data=None):
    myCoinValue = CoinValue()
    myColumns = ['coin', 'balance'] + ['initialValue' + key for key in myCoinValue.value] + ['currentValue' + key for
                                                                                             key in myCoinValue.value]
    if data:
        return pandas.DataFrame(data, columns=myColumns)
    else:
        return pandas.DataFrame(columns=myColumns)


# %% CoinValue
class CoinValue():
    def __init__(self):
        self.value = {}
        try:
            for currency in settings.mySettings.displayCurrencies():
                self.value[currency] = 0
        except Exception as ex:
            logger.globalLogger.error('error initializing display currencies: ' + str(ex))
            logger.globalLogger.info('using default display currencies')
            self.value = {'EUR': 0, 'USD': 0, 'BTC': 0}

    # iterate values
    def __iter__(self):
        return iter(self.value)

    # return length of values
    def __len__(self):
        return len(self.value)

    # get item using []
    def __getitem__(self, key):
        return self.value[key]

    def __setitem__(self, key, value):
        self.value[key] = value

    def __lt__(self, other):
        val = 1
        for key in self.value:
            if key in other.value and self.value[key] != 0 and other.value[key] != 0:
                val *= self.value[key]/other.value[key]
        return val < 1

    def __le__(self, other):
        val = 1
        for key in self.value:
            if key in other.value:
                val *= self.value[key] / other.value[key]
        return val <= 1

    def __eq__(self, other):
        val = 1
        for key in self.value:
            if key in other.value:
                val *= self.value[key] / other.value[key]
        return val == 1

    def __ne__(self, other):
        return not self.__eq__(other)

    def __ge__(self, other):
        return not self.__lt__(other)

    def __gt__(self, other):
        return not self.__le__(other)

    # add another CoinValue to the existing one
    def add(self, other):
        for key in self.value:
            self.value[key] += other.value[key]
        return self

    # add another CoinValue and return a new object
    def __add__(self, other):
        return self.copy().add(other)

    # substract another CoinValue from the existing one
    def sub(self, other):
        for key in self.value:
            self.value[key] -= other.value[key]
        return self

    # sub another CoinValue and return a new object
    def __sub__(self, other):
        return self.copy().sub(other)

    def fromDict(self, dictionary):
        for key in self.value:
            try:
                self.value[key] = dictionary[key]
            except KeyError:
                pass
        return self

    # set value of all CoinValues
    def setValue(self, value):
        for key in self.value:
            self.value[key] = value
        return self

    # devide CoinValue and return new object
    def div(self, divider):
        coinValue = CoinValue()
        if isinstance(divider, CoinValue):
            for key in self.value:
                if divider.value[key] != 0:
                    coinValue.value[key] = self.value[key] / divider.value[key]
                elif self.value[key] == 0:  # if both values are zero return 1
                    coinValue.value[key] = 1
        else:
            if not divider == 0:
                for key in self.value:
                    coinValue.value[key] = self.value[key] / divider
                return coinValue
        return coinValue

    # multiply CoinValue and return new object
    def mult(self, multiplicator):
        coinValue = CoinValue()
        for key in self.value:
            coinValue.value[key] = self.value[key] * multiplicator
        return coinValue

    def copy(self):
        coinValue = CoinValue()
        for key in self.value:
            coinValue.value[key] = self.value[key]
        return coinValue


# %% Trade
class Trade:
    def __init__(self):
        self.tradeID = ''
        self.externId = ''
        self.date = None
        self.tradeType = ''
        self.coin = ''
        self.amount = None
        self.value = CoinValue()
        self.valueLoaded = False
        self.tradePartnerId = ''
        self.exchange = ''
        self.wallet = ''

    def generateID(self):
        tradeString = str(self.date) + str(self.tradeType) + str(self.externId) + str(self.coin) + str(self.amount)
        self.tradeID = hashlib.sha1(tradeString.encode()).hexdigest()
        return self.tradeID

    def __eq__(self, other):
        return self.tradeID == other.tradeID

    def __ne__(self, other):
        return (not self.__eq__(other))

    def __hash__(self):
        return hash(self.tradeID)

    def copy(self):
        trade = Trade()
        trade.tradeID = self.tradeID
        trade.externId = self.externId
        trade.tradePartnerId = self.tradePartnerId
        trade.date = self.date
        trade.tradeType = self.tradeType
        trade.coin = self.coin
        trade.amount = self.amount
        trade.value = self.value.copy()
        trade.valueLoaded = self.valueLoaded
        trade.exchange = self.exchange
        trade.wallet = self.wallet
        return trade

    def setAmount(self, amount):
        self.value = self.value.div(self.amount).mult(amount)
        self.amount = amount

    def mergeTrade(self, trade):
        self.value.add(trade.value)
        self.amount = self.amount + trade.amount

    def toList(self):
        return [self.tradeID, self.date, self.tradeType, self.coin, self.amount] + [self.value.value[key] for key in
                                                                                    self.value.value]

    def getHeaderComplete(self):
        myCoinValue = CoinValue()
        return ['id', 'date', 'type', 'coin', 'amount'] + ['value' + key for key in myCoinValue.value] + \
               ['valueLoaded', 'tradePartnerId', 'exchange', 'externId', 'wallet']

    def toListComplete(self):
        return self.toList() + [self.valueLoaded, self.tradePartnerId, self.exchange, self.externId, self.wallet]

    def toDataFrame(self):
        return initTradeList([self.toList()])

    def fromSeries(self, series):
        self.tradeID = series['id']
        self.externId = series['externId']
        self.tradePartnerId = series['tradePartnerId']
        if isinstance(series['date'], str):
            self.date = converter.convertDate(series['date'])
        else:
            self.date = series['date']
        self.tradeType = series['type']
        self.coin = series['coin']
        self.amount = series['amount']
        self.exchange = str(series['exchange']) if not str(series['exchange']) == 'nan' else ''
        self.wallet = str(series['wallet']) if not str(series['wallet']) == 'nan' else ''
        loadingValuesFailed = False
        for key in self.value.value:
            try:
                self.value.value[key] = series['value' + key]
            except Exception as ex:
                # logger.globalLogger.warning('error parsing historical price of trade: ' + str(ex))
                # logger.globalLogger.info('reset valueLoaded flag')
                laodingValuesFailed = True
        if loadingValuesFailed:
            self.valueLoaded = False
        else:
            self.valueLoaded = series['valueLoaded']
        return self

    def updateValue(self):
        return ccapi.updateTradeValue(self)

    def getPrice(self):
        return self.value.div(self.amount)

    def isFiat(self):
        for fiat in settings.mySettings.fiatList():
            if fiat == self.coin:
                return True
        return False

    def toString(self):
        return str(self.toList())


# %% TradeList
class TradeList:
    def __init__(self):
        self.trades = []

    def __getitem__(self, index):
        return self.trades[index]

    def __setitem__(self, index, value):
        self.trades[index] = value

    # iterate trades
    def __iter__(self):
        return iter(self.trades)

        # return length of trades

    def __len__(self):
        return len(self.trades)

    def addTrade(self, trade):
        for mytrade in self.trades:
            if mytrade == trade:
                return False
        self.trades.append(trade)
        return True

    def addTradePair(self, trade1, trade2):
        # check if trades are already included
        trade1Index = None
        trade2Index = None
        for tradeIndex in range(len(self.trades)):
            if self.trades[tradeIndex] == trade1:
                trade1Index = tradeIndex
                if trade2Index:
                    break  # both tades found
            if self.trades[tradeIndex] == trade2:
                trade2Index = tradeIndex
                if trade1Index:
                    break  # both trades found
        # both trades found
        if trade1Index and trade2Index:
            # link found trades
            self.trades[trade1Index].tradePartnerId = self.trades[trade2Index].tradeID
            self.trades[trade2Index].tradePartnerId = self.trades[trade1Index].tradeID
            return False
        # only one trade found
        if trade1Index:
            self.trades[trade1Index].tradePartnerId = trade2.tradeID
            trade2.tradePartnerId = self.trades[trade1Index].tradeID
            self.trades.append(trade2)
        elif trade2Index:
            trade1.tradePartnerId = self.trades[trade2Index].tradeID
            self.trades[trade2Index].tradePartnerId = trade1.tradeID
            self.trades.append(trade1)
        else:  # no trade found
            trade1.tradePartnerId = trade2.tradeID
            trade2.tradePartnerId = trade1.tradeID
            self.trades.append(trade1)
            self.trades.append(trade2)
        return True

    def mergeTradeList(self, tradeList):
        addedTrades = TradeList()
        for trade in tradeList:
            if self.addTrade(trade):
                addedTrades.addTrade(trade)
        return addedTrades

    def reduceTradeList(self):
        self.trades = list(set(self.trades))

    def isEmpty(self):
        if self.trades:
            return False
        else:
            return True

    def toDataFrame(self):
        tradeList = []
        for trade in self.trades:
            tradeList.append(trade.toList())
        return initTradeList(tradeList)

    def toDataFrameComplete(self):
        trades = []
        for trade in self.trades:
            trades.append(trade.toListComplete())
        return initTradeListComplete(trades)

    def fromDataFrame(self, dataframe):
        for index, row in dataframe.iterrows():
            self.addTrade(Trade().fromSeries(row))
        return self

    def generateIDs(self):
        for trade in self.trades:
            if not trade.tradeID:
                trade.generateID()

    def reloadValues(self):
        for trade in self.trades:
            trade.updateValue()

    def setHistPrices(self, prices):
        for trade in self.trades:
            try:
                coinPrice = CoinValue()
                coinPrice.fromDict(prices[trade.tradeID])
                trade.value = coinPrice.mult(trade.amount)
                trade.valueLoaded = True
            except KeyError:
                pass

        for trade in self.trades:
            # get partner trade
            partner = self.getTradeById(trade.tradePartnerId)
            # check valid partner
            if partner:
                # check value of partner
                if partner.valueLoaded:
                    # use partner value if value update was not possible or if trade has a fiat partner
                    if (not trade.valueLoaded) or partner.isFiat():
                        trade.value = partner.value.mult(-1)
                        trade.valueLoaded = True
                    # if both values loaded and both trades are crypto use the same value
                    elif not trade.isFiat():
                        if trade.value < partner.value:  # use smaller value (tax will be paid later)
                            partner.value = trade.value.mult(-1)
                        else:
                            trade.value = partner.value.mult(-1)

    def updateValues(self):
        # load values of all trades
        for trade in self.trades:
            if not trade.valueLoaded:
                trade.updateValue()

        for trade in self.trades:
            # get partner trade
            partner = self.getTradeById(trade.tradePartnerId)
            # check valid partner
            if partner:
                # check value of partner
                if partner.valueLoaded:
                    # use partner value if value update was not possible or if trade has a fiat partner
                    if (not trade.valueLoaded) or partner.isFiat():
                        trade.value = partner.value.mult(-1)
                        trade.valueLoaded = True
                    # if both values loaded and both trades are crypto use the same value
                    elif not trade.isFiat():
                        if trade.value < partner.value:  # use smaller value (tax will be paid later)
                            partner.value = trade.value.mult(-1)
                        else:
                            trade.value = partner.value.mult(-1)


    def getTradeById(self, tradeId):
        for trade in self.trades:
            if trade.tradeID == tradeId:
                return trade
        return None

    def updateValuesAsync(self):
        t = threading.Thread(target=self.updateValues())
        t.start()
        return t

    def toCsv(self, path):
        # self.toDataFrameComplete().to_csv(path)
        with open(path, 'w') as file:
            file.write(','.join(Trade().getHeaderComplete()) + '\n')
            for trade in self:
                file.write(','.join(str(e) for e in trade.toListComplete()) + '\n')

    def fromCsv(self, path):
        self.fromDataFrame(pandas.read_csv(path))

    def clearPriceFlag(self):
        for trade in self.trades:
            trade.valueLoaded = False


# %% TradeMatcher
class TradeMatcher:
    def __init__(self, coinBalance, trades=[]):
        self.coinBalance = coinBalance
        self.trades = trades
        self.sellsBuffer = []
        self.buysBuffer = []
        self.sellsMatched = []
        self.buysMatched = []
        self.profitMatched = []
        self.profitMatchedTime = []
        self.profitMatchedBuyTime = []
        self.buysLeft = []

    def setTrades(self, trades):
        self.trades = trades

    def prepareTrades(self, timemode=DAYWISE):
        # copy trades to buffer
        self.sellsBuffer = []
        self.buysBuffer = []
        for trade in self.trades:
            # if trade.tradeType == 'trade': # todo: define tradeTypes to be used for profit calculation
            if trade.valueLoaded:  # ignore trades without loaded value
                if trade.amount < 0:
                    # copy trade to sell list
                    self.sellsBuffer.append(trade.copy())
                    # use positive sign for matching
                    self.sellsBuffer[-1].setAmount(-self.sellsBuffer[-1].amount)
                else:  # trade.amount >= 0
                    # copy trade to buy list
                    self.buysBuffer.append(trade.copy())
        if self.sellsBuffer and self.buysBuffer:
            # sort trades by date
            self.sellsBuffer.sort(key=lambda x: x.date, reverse=False)
            self.buysBuffer.sort(key=lambda x: x.date, reverse=False)
            # check timemode
            if not timemode == EXACT:  # timemode == DAYWISE or other:
                # revert all datetimes to dates
                for sell in self.sellsBuffer:
                    sell.date = sell.date.date()
                for buy in self.buysBuffer:
                    buy.date = buy.date.date()
            # merge sells with same date
            sellsTemp = [self.sellsBuffer[0]]
            for sell in self.sellsBuffer[1:]:
                if sellsTemp[-1].date == sell.date:
                    sellsTemp[-1].mergeTrade(sell)
                else:
                    sellsTemp.append(sell)
            self.sellsBuffer = sellsTemp
            # merge buys with same date
            buysTemp = [self.buysBuffer[0]]
            for buy in self.buysBuffer[1:]:
                if buysTemp[-1].date == buy.date:
                    buysTemp[-1].mergeTrade(buy)
                else:
                    buysTemp.append(buy)
            self.buysBuffer = buysTemp

    def matchTrades(self, timemode=DAYWISE):
        self.prepareTrades(timemode)
        self.sellsMatched = []
        self.buysMatched = []
        self.profitMatched = []
        self.profitMatchedTime = []
        self.profitMatchedBuyTime = []
        self.buysLeft = []
        buyIndex = 0
        sellIndex = 0
        maxIter = 10 * len(self.sellsBuffer)
        while (sellIndex < len(self.sellsBuffer) and buyIndex < len(self.buysBuffer)):
            if self.sellsBuffer[sellIndex].date < self.buysBuffer[buyIndex].date:  # sell is bevore buy
                # no buy trade can be matched -> ignore sellTrade
                logger.globalLogger.warning('no earlier buyTrade available for sellTrade: ' + self.sellsBuffer[
                    sellIndex].toString() + '; sellTrade will be ignored for profit calculation')
                sellIndex += 1
                continue
            else:  # sell is after buy
                # sell date can be matched to buy trade
                if self.sellsBuffer[sellIndex].amount == self.buysBuffer[buyIndex].amount:  # sell and buy equal
                    # save both as matched trades
                    self.sellsMatched.append(self.sellsBuffer[sellIndex])
                    self.buysMatched.append(self.buysBuffer[buyIndex])
                    # next buy trade
                    buyIndex += 1
                    # next sell trade
                    sellIndex += 1
                elif self.sellsBuffer[sellIndex].amount < self.buysBuffer[buyIndex].amount:  # sell smaller than buy
                    # copy buy trade and set amount to sell amount
                    buyMatched = self.buysBuffer[buyIndex].copy()
                    buyMatched.setAmount(self.sellsBuffer[sellIndex].amount)
                    # reduce buy trade by sell amount
                    self.buysBuffer[buyIndex].setAmount(
                        self.buysBuffer[buyIndex].amount - self.sellsBuffer[sellIndex].amount)

                    # save sell and part of buy as matched
                    self.sellsMatched.append(self.sellsBuffer[sellIndex])
                    self.buysMatched.append(buyMatched)
                    # next sell
                    sellIndex += 1
                elif self.sellsBuffer[sellIndex].amount > self.buysBuffer[buyIndex].amount:  # sell bigger than buy
                    # copy sell trade and set amount to buy amount
                    sellMatched = self.sellsBuffer[sellIndex].copy()
                    sellMatched.setAmount(self.buysBuffer[buyIndex].amount)
                    # reduce buy trade by sell amount
                    self.sellsBuffer[sellIndex].setAmount(
                        self.sellsBuffer[sellIndex].amount - self.buysBuffer[buyIndex].amount)

                    # save part of sell and buy as matched
                    self.sellsMatched.append(sellMatched)
                    self.buysMatched.append(self.buysBuffer[buyIndex])
                    # next buy
                    buyIndex += 1

                # calculate profit of last matched trades
                self.profitMatched.append(self.calculateProfit(self.buysMatched[-1], self.sellsMatched[-1]))
                self.profitMatchedTime.append(self.sellsMatched[-1].date)
                self.profitMatchedBuyTime.append(self.buysMatched[-1].date)
            maxIter -= 1
            if maxIter <= 0:
                logger.globalLogger.warning('maximum of matching iterations reached for coin ' + str(self.trades[0].coin))
                logger.globalLogger.info('current sell index: ' + str(sellIndex) + ' from ' + str(len(self.sellsBuffer)))
                logger.globalLogger.info('current buy index: ' + str(buyIndex) + ' from ' + str(len(self.buysBuffer)))
                break

        self.buysLeft = self.buysBuffer[buyIndex:]

    def calculateProfit(self, buyTrade, sellTrade):
        return sellTrade.value.copy().sub(buyTrade.value)

    def getTotalProfit(self):
        return sum(self.profitMatched, CoinValue())

    # def getTimeInvest(self, date):


    def getTimeDeltaProfit(self, fromDate, toDate, taxFreeTimeDelta=-1):
        if taxFreeTimeDelta == -1:
            return sum([profit for profit, date in zip(self.profitMatched, self.profitMatchedTime)
                        if (date >= fromDate and date <=toDate)], CoinValue())
        else:
            return sum([profit for profit, date, buydate in zip(self.profitMatched, self.profitMatchedTime,
                                                                  self.profitMatchedBuyTime)
                        if (date >= fromDate and date <= toDate and (date - relativedelta(years=taxFreeTimeDelta) <= buydate))],
                       CoinValue())

    def getInitialPrice(self):
        initialValue = CoinValue()
        initialAmount = 0
        for buy in self.buysLeft:
            initialValue.add(buy.value)
            initialAmount += buy.amount
        return initialValue.div(initialAmount)

    def toDataFrame(self, currency):
        rows = []
        for i in range(len(self.profitMatched)):
            buy = self.buysMatched[i]
            sell = self.sellsMatched[i]
            profit = self.profitMatched[i]
            rows.append([buy.date, buy.amount, buy.getPrice()[currency], buy.value[currency], \
                         sell.date, sell.amount, sell.getPrice()[currency], sell.value[currency], \
                         profit[currency]])
        return pandas.DataFrame(rows, columns=['buyDate', 'buyAmount', 'buyPrice', 'buyValue', \
                                               'sellDate', 'sellAmount', 'sellPrice', 'sellValue', \
                                               'profit'])

    def getBuyAmount(self):
        amount = 0
        for trade in self.trades:
            if trade.amount > 0:
                amount += trade.amount
        return amount

    def getSellAmount(self):
        amount = 0
        for trade in self.trades:
            if trade.amount < 0:
                amount += trade.amount
        return amount

    def getBuyAmountLeft(self):
        amount = 0
        for trade in self.buysLeft:
            amount += trade.amount
        return amount

    def getFirstBuyLeftDate(self):
        if self.buysLeft:
            return self.buysLeft[0].date
        return None

    def getBuyAmountLeftToDate(self, date):
        amount = 0
        for trade in self.buysLeft:
            try:
                if trade.date < date:
                    amount += trade.amount
            except TypeError:
                if trade.date.date() < date:
                    amount += trade.amount
        return amount

    def getBuyAmountLeftTaxFree(self, taxfreeLimit):
        return self.getBuyAmountLeftToDate(datetime.datetime.now().date() - relativedelta(years=1))


# %% Coin_Balance
class CoinBalance:
    def __init__(self):
        self.coinname = None
        self.balance = 0
        self.initialValue = CoinValue()
        self.currentValue = CoinValue()
        self.change24h = CoinValue()
        self.trades = []
        self.tradeMatcher = TradeMatcher(self)

    def __lt__(self, other):
        return self.balance < other.balance

    def __le__(self, other):
        return self.balance <= other.balance

    def __eq__(self, other):
        return self.balance == other.balance

    def __ne__(self, other):
        return not self.__eq__(other)

    def __gt__(self, other):
        return not self.__le__(other)

    def __ge__(self, other):
        return not self.__lt__(other)

    def __comp__(self, other):
        if self.__eq__(other):
            return 0
        elif self.__lt__(other):
            return -1
        else:
            return 1

    def addTrade(self, trade):
        if self.coinname == trade.coin:
            # check if trade already exists
            for myTrade in self.trades:
                if myTrade == trade:
                    return None
            # if trade doesnt exist then add it
            self.trades.append(trade)
            # update current value (use current price)
            newAmount = self.balance + trade.amount
            self.currentValue = self.currentValue.mult(newAmount).div(self.balance)
            # update balance
            self.balance = newAmount
            return self
        else:
            return None

    def removeTrade(self, trade):
        if self.coinname == trade.coin:
            # check if trade exists
            if trade in self.trades:
                self.trades.remove(trade)
            # update current value (use current price)
            newAmount = self.balance - trade.amount
            self.currentValue = self.currentValue.mult(newAmount).div(self.balance)
            # update balance
            self.balance = newAmount
            return self
        else:
            return None

    def updateBalance(self):
        newAmount = 0
        for trade in self.trades:
            newAmount += trade.amount
        # update current value (use current price)
        self.currentValue = self.currentValue.mult(newAmount).div(self.balance)
        # update balance
        self.balance = newAmount

    def isFiat(self):
        for fiat in settings.mySettings.fiatList():
            if fiat == self.coinname:
                return True
        return False

    def matchTrades(self):
        if self.isFiat():  # do not match fiat trades, just sum up all trades
            self.initialValue.setValue(0)
            for trade in self.trades:
                self.initialValue += trade.value
        else:  # all other trades have to be matched (sell can only be matched to an older buy)
            self.tradeMatcher.setTrades(self.trades)
            self.tradeMatcher.matchTrades()
            # check balance with buys left in tradeMatcher
            #        if self.balance != self.tradeMatcher.getBuyAmountLeft():
            # something is wrong. balance should be equal
            #            print('buys left in tradeMathcher do not fit to calculated balance for coin: ' + self.coinname)
            #            print(str(self.balance) + '; ' + str(self.tradeMatcher.getBuyAmountLeft()))
            #            pass
            # todo: create logging entry
            self.initialValue = self.tradeMatcher.getInitialPrice().mult(self.balance)

    def getInitialPrice(self):
        return self.initialValue.div(self.balance)

    def getCurrentPrice(self):
        return self.currentValue.div(self.balance)

    def getFees(self):
        fees = []
        for trade in self.trades:
            if trade.tradeType == "fee":
                fees.append(trade)
        return fees

    def getTotalFees(self):
        fees = CoinValue()
        for trade in self.trades:
            if trade.tradeType == "fee":
                fees.add(trade.value)
        return fees

    def toList(self):
        return [self.coinname, self.balance] + [self.currentValue.value[key] for key in self.currentValue.value]

    def toListComplete(self):
        return [self.coinname, self.balance] + [self.initialValue.value[key] for key in self.initialValue.value] + [
            self.currentValue.value[key] for key in self.currentValue.value]


# %% CoinList
class CoinList:
    def __init__(self):
        self.coins = []

    # iterate coins
    def __iter__(self):
        return iter(self.coins)

        # return length of coins

    def __len__(self):
        return len(self.coins)

    # get item by name        
    def __getitem__(self, key):
        return self.getCoinByName(key)

    def isMember(self, coinname):
        for coin in self.coins:
            if coin.coinname == coinname.upper():
                return True
        return False

    def addCoin(self, coinname):
        self.coins.append(CoinBalance())
        self.coins[-1].coinname = str(coinname)
        return self.coins[-1]

    def addTrade(self, trade):
        for coin in self.coins:
            if coin.coinname == trade.coin:
                coin.addTrade(trade)
                return coin
        self.addCoin(trade.coin)
        self.coins[-1].addTrade(trade)
        return self.coins[-1]

    def removeTrade(self, trade):
        for coin in self.coins:
            if coin.coinname == trade.coin:
                coin.removeTrade(trade)
                return coin

    def addTrades(self, trades):
        for trade in trades:
            self.addTrade(trade)
        self.matchTrades()
        return self

    def deleteTrades(self, trades):
        for trade in trades:
            self.removeTrade(trade)
        # remove all empty coins
        indexes = [index for index in range(len(self.coins)) if not self.coins[index].trades]
        indexes.sort(reverse=True)
        for index in indexes:
            self.coins.pop(index)
        self.matchTrades()
        return self

    def reloadTrades(self, trades):
        self.coins.clear()
        self.addTrades(trades)

    def tradeChanged(self, trade):
        try:
            coin = self.getCoinByName(trade.coin)
        except KeyError as ex:
            # unknowen coin; ignore trade
            print(str(ex) + ' for coin ' + str(trade.coin))
            return None
        coin.matchTrades()
        return coin

    def matchTrades(self):
        for coin in self.coins:
            coin.matchTrades()

    def toDataFrame(self):
        coinList = []
        for coin in self.coins:
            coinList.append(coin.toList())
        return initCoinList(coinList)

    def toDataFrameComplete(self):
        coinList = []
        for coin in self.coins:
            coinList.append(coin.toListComplete())
        return initCoinListComplete(coinList)

    def isEmpty(self):
        if self.coins:
            return False
        else:
            return True

    def getCoinByName(self, name):
        for coin in self:
            if coin.coinname == name:
                return coin
        raise KeyError

    # get List of coinnames
    def getCoinNames(self):
        return [coin.coinname for coin in self.coins]

    # set prices from dict
    def setPrices(self, prices):
        for coin in self.coins:
                for key in coin.currentValue:
                    try:
                        coin.currentValue[key] = prices[coin.coinname][key]['PRICE'] * coin.balance
                        coin.change24h[key] = prices[coin.coinname][key]['CHANGEPCT24HOUR']
                    except KeyError:
                        pass

    def histPricesChanged(self):
        pass

    def histPriceUpdateFinished(self):
        self.matchTrades()

    # update current value of all coins
    def updateCurrentValues(self):
        return ccapi.updateCurrentCoinValues(self)

    def update24hChange(self):
        return ccapi.get24hChange(self)

    # update current value of all coins async
    def updateCurrentValuesAsync(self):
        t = threading.Thread(target=self.updateCurrentValues)
        t.daemon = True
        t.start()
        return t
