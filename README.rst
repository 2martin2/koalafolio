pycryptoportfolio
******************
portfolio for cryptocoins with profit export for tax

Installation with PipEnv
-------------------------
   
 - clone repo
 - install python > 3.7
 - install pipenv
 - use pipenv to install dependencies
 - run gui_root.py
 
Installation with Pip
----------------------
   
 - (opt) install python_ > 3.7 (check with python --version or python3 --version or python3.x --version)
 - (opt) install pip (check with pip --version or pip3 --version)
 - install koalafolio for python 3!: (pip install koalafolio or pip3 install koalafolio or python3.x -m pip install koalafolio)
 - run koalafolio from terminal (koalafolio)
 - (opt) update koalafolio (pip install koalafolio --upgrade)
   
.. _python: https://www.python.org/downloads/
   
trade import
-------------
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
   - exodus (v1/txs/.json)
   - others could work as well but not tested
   
 import trades from exchanges using their API:
  supported exchanges (so far):
   - kraken

portfolio
----------
  load all historical prices from CryptoCompare_ for profit calculation

  display balance, ... of all bought cryptocoins


export
-------
  export profit made in a specific timeframe using FIFO-method (excel)
   - (english and german, others can be added in translation.txt)

Credits
*********
Thanks to CryptoCompare_

.. _Cryptocompare: https://min-api.cryptocompare.com/

Gui based on Qt_

.. _Qt: https://www.qt.io/
