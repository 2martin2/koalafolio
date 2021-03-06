# -*- coding: utf-8 -*-

# import koalafolio.web.cryptocompare as cryptcomp
import requests, datetime
from PIL import Image
from PIL.ImageQt import ImageQt
from io import BytesIO
from PyQt5 import QtGui as qtgui


proxies = None

# dates = [datetime.datetime(2017,6,6,10,30,0), datetime.datetime(2017,6,6,19,30,0), datetime.datetime(2017,6,7,10,30,0)]
# histprices = []
# for date in dates:
#   histprices.append(cryptcomp.get_historical_price('ETH', ['USD','EUR','BTC'], date, proxies=proxies))
# histprices2 = []
# for date in dates:
#   histprices2.append(cryptcomp.get_historical_price('ETH', ['USD','EUR','BTC'], date, calculationType='MidHighLow', proxies=proxies))
# histprices3 = []
# for date in dates:
#   histprices3.append(cryptcomp.get_historical_price('ETH', ['USD','EUR','BTC'], date, calculationType='VolFVolT', proxies=proxies))
#
# dayprice = cryptcomp.get_historical_price_day('ETH', 'EUR')


URL_CRYPTOCOMPARE = 'https://www.cryptocompare.com'
URL_COIN_LIST = 'https://www.cryptocompare.com/api/data/coinlist/'
URL_COIN_GENERAL = 'https://min-api.cryptocompare.com/data/coin/generalinfo'


def query_cryptocompare(url, errorCheck=True, *args, **kwargs):
  try:
    response = requests.get(url, *args, **kwargs).json()
  except Exception as e:
    print('Error getting coin information. %s' % str(e))
    return None
  if errorCheck and (response.get('Response') == 'Error'):
    print('[ERROR] %s' % response.get('Message'))
    return None
  return response

coinList = query_cryptocompare(URL_COIN_LIST)
coinInfo = query_cryptocompare(URL_COIN_GENERAL, params={'fsyms': ['BTC','EUR','ETH'], 'tsym': 'USD'})
for data in coinInfo['Data']:
  imageResponse = requests.get(URL_CRYPTOCOMPARE + data['CoinInfo']['ImageUrl'])
  coinIcon = Image.open(BytesIO(imageResponse.content))
  # im = coinIcon.convert("RGBA")
  # # data = im.tobytes("raw", "RGBA")
  # # data2 = imageResponse.content
  # # qim = qtgui.QImage(data, im.size[0], im.size[1], qtgui.QImage.Format_ARGB32)
  # qim = ImageQt(im)
  # qpix = qtgui.QPixmap.fromImage(qim)
  # qicon = qtgui.QIcon(qpix)
