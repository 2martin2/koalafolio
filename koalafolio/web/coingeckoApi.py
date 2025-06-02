# -*- coding: utf-8 -*-


import pycoingecko
import json
import math
import koalafolio.PcpCore.core as core
import koalafolio.PcpCore.settings as settings
import koalafolio.PcpCore.logger as logger
from PyQt5.QtGui import QImage, QPixmap, QIcon
import requests
import datetime


class CoinGeckoAPIProxy(pycoingecko.CoinGeckoAPI):

    def __init__(self, api_base_url=pycoingecko.CoinGeckoAPI._CoinGeckoAPI__API_URL_BASE, proxies={}):
        super(CoinGeckoAPIProxy, self).__init__(api_base_url)
        self.proxies = proxies

    def __request(self, url):
        try:
            response = self.session.get(url, timeout=self.request_timeout, proxies=self.proxies)
            response.raise_for_status()
            content = json.loads(response.content.decode('utf-8'))
            return content
        except Exception:
            # check if json (with error message) is returned
            try:
                content = json.loads(response.content.decode('utf-8'))
                raise ValueError(content)
            # if no json
            except json.decoder.JSONDecodeError:
                pass
            # except UnboundLocalError as e:
            #    pass
            raise


cg = CoinGeckoAPIProxy()
try:
    coinsList = cg.get_coins_list()
except Exception as e:
    # todo: create lokal copy of coinsList as backup
    logger.globalLogger.error("coinsList from coingecko can not be loaded: " + str(e))
    coinsList = []

coinSymbolToIdDict = {} # id=bitcoin, symbol=btc
for coin in coinsList:
    coinSymbolToIdDict[coin['symbol'].upper()] = coin['id']
coinIdToSymbolDict = {}
for coin in coinsList:
    coinIdToSymbolDict[coin['id']] = coin['symbol'].upper()

def coinSymbolToId(coinSymbol):
    if coinSymbol in settings.mySettings.coinSwapDictCoinGeckoSymbolToId():
        return settings.mySettings.coinSwapDictCoinGeckoSymbolToId()[coinSymbol]
    if coinSymbol in settings.mySettings.coinSwapDictCoinGecko():
        coinSymbolSwap = settings.mySettings.coinSwapDictCoinGecko()[coinSymbol]
    else:
        coinSymbolSwap = coinSymbol
    try:
        return coinSymbolToIdDict[coinSymbolSwap]
    except KeyError:
        # ignore coin
        pass
        # logger.globalLogger.warning('error loading coinGecko data for ' + str(coinSymbolSwap))
    return None

def coinSymbolsToIds(coinSymbols):
    coinIds = []
    for coinSymbol in coinSymbols:
        coinId = coinSymbolToId(coinSymbol)
        if coinId is not None:
            coinIds.append(coinId)
    return coinIds


def coinIdToSymbol(coinId):
    coinSwapDictCoinGeckoSymbolToId = {v: k for k, v in settings.mySettings.coinSwapDictCoinGeckoSymbolToId().items()}
    if coinId in coinSwapDictCoinGeckoSymbolToId:
        return coinSwapDictCoinGeckoSymbolToId[coinId]
    invCoinSwapDictCoinGecko = {v: k for k, v in settings.mySettings.coinSwapDictCoinGecko().items()}
    if coinId in invCoinSwapDictCoinGecko:
        mappedCoinId = invCoinSwapDictCoinGecko[coinId]
    else:
        mappedCoinId = coinId
    try:
        return coinIdToSymbolDict[mappedCoinId]
    except KeyError:
        # ignore coin
        logger.globalLogger.warning('error loading coinGecko data for coinId' + str(coinId))
    return coinId


def coinIdsToSymbols(coinIds):
    coinSymbols = []
    for coinId in coinIds:
        coinSymbol = coinIdToSymbol(coinId)
        if coinSymbol is not None:
            coinSymbols.append(coinSymbol)
    return coinSymbols

def getHistoricalPrice(trade):
    if settings.mySettings.proxies():
        cg.proxies = settings.mySettings.proxies()
    else:
        cg.proxies = {}
    if trade.date:
        if coinSymbolToId(trade.coin) is not None:
            try:
                response = cg.get_coin_history_by_id(id=coinSymbolToId(trade.coin),
                                                     vsCurrencies=[key for key in settings.mySettings.displayCurrencies()],
                                                     date=trade.date.date().strftime('%d-%m-%Y'))

                return response['market_data']['current_price']
            except KeyError:
                logger.globalLogger.warning('error loading historical coinGecko price for ' + str(trade.coin))
            except ValueError as ex:
                logger.globalLogger.error('error loading historical coinGecko price for ' + str(trade.coin) + ': ' + str(ex))
    return {}

def getCoinPrices(coins):
    if settings.mySettings.proxies():
        cg.proxies = settings.mySettings.proxies()
    else:
        cg.proxies = {}
    # try to load price from coingecko
    coinIds = coinSymbolsToIds(coins)
    try:
        response = cg.get_price(ids=coinIds, vs_currencies=[key for key in core.CoinValue()], include_market_cap='true',
                                include_24hr_vol='true', include_24hr_change='true', include_last_updated_at='true')
        prices = {}
        for coinId in response:
            coinSymbol = coinIdToSymbol(coinId)
            prices[coinSymbol] = {}
            for key in core.CoinValue():
                prices[coinSymbol][key] = {}
                prices[coinSymbol][key]['PRICE'] = response[coinId][key.lower()]
                prices[coinSymbol][key]['CHANGEPCT24HOUR'] = response[coinId][key.lower() + '_24h_change']

        return prices
    except Exception as ex:
        logger.globalLogger.warning('error loading prices: ' + str(ex))
    return {}

def getPriceChartData(coin, startTime: datetime.datetime) -> list:
    if settings.mySettings.proxies():
        cg.proxies = settings.mySettings.proxies()
    else:
        cg.proxies = {}
    # try to load price from coingecko
    coinId = coinSymbolToId(coin)
    if coinId:
        try:
            response = cg.get_coin_market_chart_range_by_id(id=coinId, vs_currency=settings.mySettings.reportCurrency(),
                                                                   from_timestamp=startTime.timestamp(),
                                                                   to_timestamp=datetime.datetime.now().timestamp())
            return response['prices']
        except Exception as ex:
            logger.globalLogger.warning('error loading priceChartData: ' + str(ex) + '; id: ' + str(coinId))
    return []

def getImage(url, coin):
    try:
        imageResponse = requests.get(url, proxies=settings.mySettings.proxies(), timeout=100)
    except Exception as ex:
        logger.globalLogger.warning('error in coinGecko getIcon for ' + str(coin) + ': ' + str(ex))
        return None
    if imageResponse.status_code == 200:
        # request successful
        return imageResponse.content
    if imageResponse.status_code == 429:
        raise ConnectionRefusedError("response code: " + str(imageResponse.status_code) + ", reason: " + str(imageResponse.reason))
    raise ConnectionError(
        "response code: " + str(imageResponse.status_code) + ", reason: " + str(imageResponse.reason))

def getIcon(coin, *args, **kwargs):
    if settings.mySettings.proxies():
        cg.proxies = settings.mySettings.proxies()
    else:
        cg.proxies = {}
    coinId = coinSymbolToId(coin)
    if coinId is not None:
        coinInfo = cg.get_coin_by_id(id=coinId, localization='false', tickers='false', market_data='false',
                                      community_data='false', developer_data='false', sparkline='false')
        return imageToIcon(getImage(coinInfo['image']['small'], coinId))
    return None

def getIconsLoop(coins, *args, **kwargs):
    icons = {}
    for coin in coins:
        icon = getIcon(coin)
        if icon is not None:
            icons[coin] = icon
    return icons

def getIcons(coins, *args, **kwargs):
    iconUrls = getIconUrls(coins)
    icons = {}
    for coinSymbol in iconUrls:
        try:
            icons[coinSymbol] = imageToIcon(getImage(iconUrls[coinSymbol], coinSymbol))
        except Exception as ex:
            logger.globalLogger.warning('error loading coinGecko Icon for : ' + str(coinSymbol) + "exception: " + str(ex))
    return icons

def getIconUrls(coins, *args, **kwargs):
    if settings.mySettings.proxies():
        cg.proxies = settings.mySettings.proxies()
    else:
        cg.proxies = {}
    # try to load price from coingecko
    coinIds = coinSymbolsToIds(coins)
    pages = math.ceil(len(coins)/250)
    try:
        response = []
        for page in range(1, pages+1):
            response += (cg.get_coins_markets(ids=coinIds, vs_currency='btc', order='market_cap_desc',
                                        per_page=250, page=page))
        iconUrls = {}
        for coinInfo in response:

            coinSymbol = coinIdToSymbol(coinInfo['id'])
            iconUrls[coinSymbol] = coinInfo['image']
        return iconUrls
    except Exception as ex:
        logger.globalLogger.warning('error loading coinGecko Icons: ' + str(ex))
    return {}

def imageToIcon(imagedata):
    # Convert to QImage
    q_image = QImage()
    q_image.loadFromData(imagedata)
    # Convert to QPixmap
    qpix = QPixmap.fromImage(q_image)
    return QIcon(qpix)



