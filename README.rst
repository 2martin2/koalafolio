pycryptoportfolio
****************
portfolio for cryptocoins with profit export for tax

Installation
---------
   
 - clone repo
 - install python3
 - install pipenv
 - use pipenv to install dependencies
 - run gui_root.py
   
   
trade import
---------
 import trades from exchanges using their export files
  supported exchanges (so far):
   - binance (xls)
   - bitcoinde (csv)
   - bitfinex (csv)
   - bitstamp (csv)
   - bittrex (csv)
   - coinbase (buys, sells and merchant payouts)
   - hitbtc (csv)
   - idex (csv)
   - kraken (csv)
   - kuCoin (csv)
   - okex (csv)
   - poloniex (csv)
   - exodus (v1/txs/*.json)
   - others could work as well but not tested

portfolio
---------
  load all historical prices from CryptoCompare_ for profit calculation

  display balance, ... of all bought cryptocoins


export
------
  export profit made in a specific timeframe using FIFO-method (excel)
   - (for now export is only in german)

Credits
*******
Thanks to CryptoCompare_

.. _Cryptocompare: https://min-api.cryptocompare.com/

Gui based on Qt_

.. _Qt: https://www.qt.io/
