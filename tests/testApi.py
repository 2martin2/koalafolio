# -*- coding: utf-8 -*-

import cryptocompare.cryptocompare as cryptcomp
import requests, datetime


#set http_proxy=http://rb-proxy-de.bosch.com:8080
#set https_proxy=https://rb-proxy-de.bosch.com:8080
#set ftp_proxy=https://rb-proxy-de.bosch.com:8080

proxies = {
  'http': 'http://rb-proxy-de.bosch.com:8080',
  'https': 'https://rb-proxy-de.bosch.com:8080',
}
proxies = None


# price = cryptcomp.get_price(['BTC', 'ETH', 'EOS'], ['USD','EUR','BTC'], proxies=proxies)
# coinlist = cryptcomp.get_coin_list(proxies=proxies)
dates = [datetime.datetime(2017,6,6,10,30,0), datetime.datetime(2017,6,6,19,30,0), datetime.datetime(2017,6,7,10,30,0)]
histprices = []
for date in dates:
  histprices.append(cryptcomp.get_historical_price('ETH', ['USD','EUR','BTC'], date, proxies=proxies))
histprices2 = []
for date in dates:
  histprices2.append(cryptcomp.get_historical_price('ETH', ['USD','EUR','BTC'], date, calculationType='MidHighLow', proxies=proxies))
histprices3 = []
for date in dates:
  histprices3.append(cryptcomp.get_historical_price('ETH', ['USD','EUR','BTC'], date, calculationType='VolFVolT', proxies=proxies))

dayprice = cryptcomp.get_historical_price_day('ETH', 'EUR')