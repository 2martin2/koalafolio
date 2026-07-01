# -*- coding: utf-8 -*-

"""
CCXT-based public price API wrapper

Provides a small, robust wrapper around ccxt to fetch current coin prices
and historical (close) prices for trades. Designed to be a drop-in
replacement for the previous `coingeckoApi` / `cryptocompareApi` price
functions used by the application. Initial implementation focuses on
`binance` and falls back gracefully when symbols are missing.

Functions exposed:
- `getCoinPrices(coins: list) -> dict` — current prices for requested
  coins (best-effort for configured display currencies)
- `getHistoricalPrice(trade) -> dict` — price snapshot for a given
  `core.Trade` at `trade.date` (best-effort)

This module uses the `settings.mySettings.displayCurrencies()` list to
decide which quote currencies to provide. It respects exchange rate
limits and logs errors instead of raising them.
"""

import re
import time
from typing import List, Dict

import ccxt

import koalafolio.PcpCore.core as core
import koalafolio.PcpCore.settings as settings
import koalafolio.PcpCore.logger as logger

localLogger = logger.globalLogger


class CCXTPublic:
	"""Small CCXT wrapper to fetch tickers and OHLCV close prices."""

	def __init__(self, exchange_name: str = 'binance'):
		self.exchange_name = exchange_name
		try:
			exchange_cls = getattr(ccxt, self.exchange_name)
		except AttributeError:
			raise ValueError(f"ccxt does not provide exchange '{self.exchange_name}'")

		# disable rate limit handling and reasonable timeouts
		self.exchange = exchange_cls({'enableRateLimit': False, 'timeout': 30000})

		try:
			# load markets to build symbol map
			self.exchange.load_markets()
		except Exception as e:
			localLogger.warning(f"failed to load markets for {self.exchange_name}: {e}")

		# common quote candidates to try when looking for pairs
		self.common_quotes = ['USDT', 'USDC', 'BTC', 'ETH', 'BNB', 'EUR', 'USD']
		self._ticker_cache = {}
		self._ohlcv_cache = {}
		self._cache_ttl_seconds = 15

	def _get_cached_ticker(self, symbol: str):
		entry = self._ticker_cache.get(symbol)
		if not entry:
			return None
		ts, value = entry
		if time.time() - ts > self._cache_ttl_seconds:
			del self._ticker_cache[symbol]
			return None
		return value

	def _set_cached_ticker(self, symbol: str, value):
		self._ticker_cache[symbol] = (time.time(), value)

	def _get_cached_ohlcv(self, symbol: str, since_ms: int, timeframe: str):
		key = (symbol, timeframe, since_ms)
		entry = self._ohlcv_cache.get(key)
		if not entry:
			return None
		ts, value = entry
		if time.time() - ts > self._cache_ttl_seconds:
			del self._ohlcv_cache[key]
			return None
		return value

	def _set_cached_ohlcv(self, symbol: str, since_ms: int, timeframe: str, value):
		self._ohlcv_cache[(symbol, timeframe, since_ms)] = (time.time(), value)

	def _sleep_rate_limit(self):
		# try without rate limits. reenable if needed
		return
		# try:
		# 	delay = float(getattr(self.exchange, 'rateLimit', 0)) / 1000.0
		# 	logger.globalLogger.info(f"Sleeping for {delay} seconds to respect rate limit for {self.exchange_name}")
		# 	if delay > 0:
		# 		time.sleep(delay)
		# except Exception:
		# 	# best-effort, ignore
		# 	pass

	@staticmethod
	def _parse_numeric(value):
		"""Parse numeric values from CCXT tickers, including strings like '1.27%'."""
		if value is None:
			return None
		if isinstance(value, (int, float)):
			return float(value)
		if isinstance(value, str):
			text = value.strip()
			if not text:
				return None
			text = text.replace('%', '').replace('−', '-').replace(',', '.')
			text = re.sub(r'[^0-9.+\-eE]', '', text)
			if not text:
				return None
			try:
				return float(text)
			except ValueError:
				return None
		return None

	@staticmethod
	def _is_expected_symbol_error(error: Exception) -> bool:
		text = str(error).lower()
		return any(token in text for token in ['invalid symbol', 'not found', 'not supported', 'symbol'])

	def _symbol_exists(self, symbol: str) -> bool:
		try:
			return symbol in getattr(self.exchange, 'markets', {})
		except Exception:
			return False

	def _get_ticker_data(self, symbol: str):
		cached = self._get_cached_ticker(symbol)
		if cached is not None:
			return cached
		try:
			ticker = self.exchange.fetch_ticker(symbol)
			self._sleep_rate_limit()
			# prefer 'last' then 'close'
			price = ticker.get('last') or ticker.get('close') or ticker.get('info', {}).get('price')
			change = ticker.get('info', {}).get('priceChangePercent')
			if change is None:
				change = ticker.get('percentage')
			price_value = self._parse_numeric(price)
			change_value = self._parse_numeric(change)
			result = (price_value, change_value) if price_value is not None else (None, None)
			self._set_cached_ticker(symbol, result)
			return result
		except Exception as e:
			if self._is_expected_symbol_error(e):
				localLogger.debug(f"skipping ticker for {symbol}: {e}")
			else:
				localLogger.warning(f"error fetching ticker for {symbol}: {e}")
			result = (None, None)
			self._set_cached_ticker(symbol, result)
			return result

	def _get_ticker_price(self, symbol: str):
		price, _ = self._get_ticker_data(symbol)
		return price

	def _get_ohlcv_close(self, symbol: str, since_ms: int = None, timeframe: str = '1d'):
		cached = self._get_cached_ohlcv(symbol, since_ms, timeframe)
		if cached is not None:
			return cached
		try:
			# fetch one candle around the requested timestamp
			ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe=timeframe, since=since_ms, limit=1)
			self._sleep_rate_limit()
			if ohlcv and len(ohlcv) > 0:
				value = float(ohlcv[0][4])
				self._set_cached_ohlcv(symbol, since_ms, timeframe, value)
				return value
			self._set_cached_ohlcv(symbol, since_ms, timeframe, None)
			return None
		except Exception as e:
			localLogger.warning(f"error fetching ohlcv for {symbol}: {e}")
			self._set_cached_ohlcv(symbol, since_ms, timeframe, None)
			return None

	def _find_symbol(self, base: str, quote_candidates: List[str]) -> str:
		# try direct base/quote candidates
		for q in quote_candidates:
			sym = f"{base}/{q}"
			if self._symbol_exists(sym):
				return sym
		# try inverted (quote/base) and skip for now
		return None

	def _convert_price_to_display(self, price, quote: str, display: str, visited=None):
		"""Best-effort conversion from one quote currency to another."""
		if price is None:
			return None, None
		if quote == display:
			return price, None

		if visited is None:
			visited = set()
		visited = set(visited) | {quote}

		# 1) direct conversion: quote/display or display/quote
		for symbol in [f"{quote}/{display}", f"{display}/{quote}"]:
			if self._symbol_exists(symbol):
				pair_price, pair_change = self._get_ticker_data(symbol)
				if pair_price is not None:
					if symbol.startswith(f"{quote}/"):
						return price * pair_price, pair_change
					return price / pair_price, pair_change

		# 2) try an intermediate quote such as USDC (Binance commonly exposes EUR/USDC)
		for intermediate in ['USDC', 'USDT', 'USD']:
			if intermediate in {quote, display} or intermediate in visited:
				continue
			if self._symbol_exists(f"{quote}/{intermediate}"):
				intermediate_price, _ = self._get_ticker_data(f"{quote}/{intermediate}")
				if intermediate_price is not None:
					converted, _ = self._convert_price_to_display(
						price * intermediate_price,
						intermediate,
						display,
						visited | {intermediate},
					)
					if converted is not None:
						return converted, None
			if self._symbol_exists(f"{intermediate}/{quote}"):
				intermediate_price, _ = self._get_ticker_data(f"{intermediate}/{quote}")
				if intermediate_price is not None:
					converted, _ = self._convert_price_to_display(
						price / intermediate_price,
						intermediate,
						display,
						visited | {intermediate},
					)
					if converted is not None:
						return converted, None
		return None, None

	def get_coin_prices(self, coins: List[str]) -> Dict[str, Dict[str, float]]:
		"""Return a mapping coin -> {DISPLAY_CURRENCY: price}

		This is a best-effort implementation: it will try to find a direct
		trading pair for each requested display currency. When only a
		quote-based pair (e.g. coin/USDC) is available it will provide the
		price for the display currency if the display currency maps to the
		same quote (USD -> USDC) or if a conversion pair is available.
		"""
		prices: Dict[str, Dict[str, float]] = {}
		display_currencies = settings.mySettings.displayCurrencies()

		for coin in coins:
			coin = coin.upper()
			prices[coin] = {}
			# try to find a direct pair for each display currency
			for display in display_currencies:
				display = display.upper()
				# if querying price for the same coin
				if display == coin:
					prices[coin][display] = {'PRICE': 1.0, 'CHANGEPCT24HOUR': None}
					continue

				# prepare quote candidates: prefer display itself then common quotes
				quote_candidates = [display] + [q for q in self.common_quotes if q != display]
				# map USD -> USDC as first attempt
				if display == 'USD' and 'USDC' not in quote_candidates:
					quote_candidates.insert(0, 'USDC')

				symbol = self._find_symbol(coin, quote_candidates)
				if symbol:
					p, change = self._get_ticker_data(symbol)
					if p is not None:
						# if symbol quote matches display use directly
						quote = symbol.split('/')[1]
						if quote == display or (display == 'USD' and quote == 'USDC'):
							prices[coin][display] = {'PRICE': p, 'CHANGEPCT24HOUR': change}
							continue
					converted_price, converted_change = self._convert_price_to_display(p, quote, display)
					if converted_price is not None:
						prices[coin][display] = {'PRICE': converted_price, 'CHANGEPCT24HOUR': change if converted_change is None else converted_change}
						continue

				# if no direct symbol, try to compute via USDC path
				# fetch coin/USDC and display/USDC to compute price
				if self._symbol_exists(f"{coin}/USDC"):
					coin_usdc, coin_change = self._get_ticker_data(f"{coin}/USDC")
					# if display == USD treat USDC as USD
					if display == 'USD':
						if coin_usdc is not None:
							prices[coin][display] = {'PRICE': coin_usdc, 'CHANGEPCT24HOUR': coin_change}
							continue
					# try to get display/USDC or USDC/display
					if self._symbol_exists(f"{display}/USDC"):
						display_usdc, display_change = self._get_ticker_data(f"{display}/USDC")
						if coin_usdc is not None and display_usdc:
							prices[coin][display] = {'PRICE': coin_usdc / display_usdc, 'CHANGEPCT24HOUR': coin_change}
							continue
					if self._symbol_exists(f"USDC/{display}"):
						usdc_display, usdc_change = self._get_ticker_data(f"USDC/{display}")
						if coin_usdc is not None and usdc_display:
							prices[coin][display] = {'PRICE': coin_usdc * usdc_display, 'CHANGEPCT24HOUR': coin_change}
							continue

				# give up for this display currency — leave missing to be handled upstream
		return prices

	def get_historical_price(self, trade: core.Trade) -> Dict[str, float]:
		"""Return a dict with display currency keys and price (close) at trade.date.

		The function attempts to find an OHLCV candle for the best matching
		trading pair and returns the close price. If no data can be found an
		empty dict is returned.
		"""
		if not trade or not trade.date or not trade.coin:
			return {}

		ts_ms = int(trade.date.timestamp() * 1000)
		display_currencies = settings.mySettings.displayCurrencies()
		result: Dict[str, float] = {}

		base = trade.coin.upper()
		for display in display_currencies:
			display = display.upper()
			if display == base:
				result[display] = 1.0
				continue

			# try direct pair
			quote_candidates = [display] + [q for q in self.common_quotes if q != display]
			if display == 'USD':
				quote_candidates.insert(0, 'USDC')

			symbol = self._find_symbol(base, quote_candidates)
			if symbol:
				close = self._get_ohlcv_close(symbol, since_ms=ts_ms)
				if close is not None:
					# if quote != display attempt conversion similar to tickers
					quote = symbol.split('/')[1]
					if quote == display or (display == 'USD' and quote == 'USDC'):
						result[display] = close
						continue
					if quote != display:
						# try direct conversion and an intermediate via USDC
						converted = None
						if self._symbol_exists(f"{quote}/{display}"):
							converted = self._get_ohlcv_close(f"{quote}/{display}", since_ms=ts_ms)
							if converted:
								result[display] = close * converted
								continue
						if self._symbol_exists(f"{display}/{quote}"):
							converted = self._get_ohlcv_close(f"{display}/{quote}", since_ms=ts_ms)
							if converted:
								result[display] = close / converted
								continue
						for intermediate in ['USDC', 'USDT', 'USD']:
							if intermediate in {quote, display}:
								continue
							if self._symbol_exists(f"{quote}/{intermediate}"):
								base_intermediate = self._get_ohlcv_close(f"{quote}/{intermediate}", since_ms=ts_ms)
								if base_intermediate:
									if self._symbol_exists(f"{intermediate}/{display}"):
										display_intermediate = self._get_ohlcv_close(f"{intermediate}/{display}", since_ms=ts_ms)
										if display_intermediate:
											result[display] = close * base_intermediate * display_intermediate
											continue
									if self._symbol_exists(f"{display}/{intermediate}"):
										display_intermediate = self._get_ohlcv_close(f"{display}/{intermediate}", since_ms=ts_ms)
										if display_intermediate:
											result[display] = close * base_intermediate / display_intermediate
											continue
							if self._symbol_exists(f"{intermediate}/{quote}"):
								base_intermediate = self._get_ohlcv_close(f"{intermediate}/{quote}", since_ms=ts_ms)
								if base_intermediate:
									if self._symbol_exists(f"{intermediate}/{display}"):
										display_intermediate = self._get_ohlcv_close(f"{intermediate}/{display}", since_ms=ts_ms)
										if display_intermediate:
											result[display] = close / base_intermediate * display_intermediate
											continue
									if self._symbol_exists(f"{display}/{intermediate}"):
										display_intermediate = self._get_ohlcv_close(f"{display}/{intermediate}", since_ms=ts_ms)
										if display_intermediate:
											result[display] = close / base_intermediate / display_intermediate
											continue

			# fallback via USDC path using ohlcv/ticker
			if self._symbol_exists(f"{base}/USDC"):
				base_usdc_close = self._get_ohlcv_close(f"{base}/USDC", since_ms=ts_ms)
				if base_usdc_close is None:
					base_usdc_close = self._get_ticker_price(f"{base}/USDC")
				if base_usdc_close is not None:
					if display == 'USD':
						result[display] = base_usdc_close
						continue
					# try to get display/USDC
					if self._symbol_exists(f"{display}/USDC"):
						display_usdc = self._get_ohlcv_close(f"{display}/USDC", since_ms=ts_ms)
						if display_usdc is None:
							display_usdc = self._get_ticker_price(f"{display}/USDC")
						if display_usdc:
							result[display] = base_usdc_close / display_usdc
							continue
					if self._symbol_exists(f"USDC/{display}"):
						usdc_display = self._get_ohlcv_close(f"USDC/{display}", since_ms=ts_ms)
						if usdc_display is None:
							usdc_display = self._get_ticker_price(f"USDC/{display}")
						if usdc_display:
							result[display] = base_usdc_close * usdc_display
							continue

		return result


# module-level singleton using binance by default
_DEFAULT = CCXTPublic('binance')


def getCoinPrices(coins: List[str]) -> Dict[str, Dict[str, float]]:
	return _DEFAULT.get_coin_prices(coins)


def getHistoricalPrice(trade: core.Trade) -> Dict[str, float]:
	return _DEFAULT.get_historical_price(trade)



if __name__ == "__main__":
	# get all common currencies from ccxt for debugging
	print(ccxt.Exchange.commonCurrencies)

	def write_list_to_file(data: list, filename: str):
		# write every entry of the list in seperate line
		with open(filename, 'w') as f:
			for item in data:
				f.write(f"{item}\n")

	# create subfolder for output files
	import os
	if not os.path.exists("ccxt_debug"):
		os.makedirs("ccxt_debug")

	# get all exchanges from ccxt for debugging
	write_list_to_file(ccxt.exchanges, "ccxt_debug/ccxt_exchanges.txt")
	print(f"ccxt: {len(ccxt.exchanges)} exchanges available")


	# loop trough all exchanges that might be used for price fetching and create a set of all available coinIds
	exchangesToCheck = ["coinbase", "binance", "gate", "mexc", "htx", "bingx"]
	coinIds = {}
	num_coinIds = {}
	for exchange_name in exchangesToCheck:
		print(f"loading coinIds for {exchange_name}...")
		coinIds[exchange_name] = set()
		num_coinIds[exchange_name] = 0
		markets = None
		try:
			exchange_cls = getattr(ccxt, exchange_name)
			exchange = exchange_cls({'enableRateLimit': True, 'timeout': 10000})
			markets = exchange.load_markets()
		except TimeoutError:
			print(f"Timeout occurred while loading coinIds for {exchange_name}")
		except Exception as e:
			print(f"Error occurred while loading coinIds for {exchange_name}")
		if markets is not None:
			for m in markets:
				coinIds[exchange_name].add(markets[m]['base'])
				coinIds[exchange_name].add(markets[m]['quote'])
			num_coinIds[exchange_name] = len(coinIds[exchange_name])
			print(f"{exchange_name}: {len(coinIds[exchange_name])} coinIds")
	
		
	# save coinId lists to files
	for exchange_name in exchangesToCheck:
		write_list_to_file(sorted(coinIds[exchange_name]), f"ccxt_debug/ccxt_coinIds_{exchange_name}.txt")



