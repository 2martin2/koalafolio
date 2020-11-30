from rotkehlchen.assets.asset import Asset, EthereumToken

def getFiatCurrencies(start=0, end=None):
    A_USD = Asset('USD')
    A_EUR = Asset('EUR')
    A_GBP = Asset('GBP')
    A_JPY = Asset('JPY')
    A_CNY = Asset('CNY')
    A_CAD = Asset('CAD')
    A_KRW = Asset('KRW')
    A_RUB = Asset('RUB')
    A_CHF = Asset('CHF')
    A_TRY = Asset('TRY')
    A_ZAR = Asset('ZAR')
    A_AUD = Asset('AUD')
    A_NZD = Asset('NZD')
    A_BRL = Asset('BRL')
    FIAT_CURRENCIES = (
        A_USD,
        A_EUR,
        A_GBP,
        A_JPY,
        A_CNY,
        A_CAD,
        A_KRW,
        A_RUB,
        A_CHF,
        A_TRY,
        A_ZAR,
        A_AUD,
        A_NZD,
        A_BRL,
    )
    return FIAT_CURRENCIES[start:end]

