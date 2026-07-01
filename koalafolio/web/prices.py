# -*- coding: utf-8 -*-

"""
Multi-exchange price aggregation layer

This module provides a high-level price fetching interface that queries
multiple exchanges, detects outliers, and computes averaged prices.

The strategy:
1. Query all supported exchanges for current and historical prices
2. Collect all valid price data per coin
3. Detect outliers using interquartile range (IQR) method
4. Log warnings when outliers are found
5. Return averaged prices from non-outlier data
6. Gracefully handle coins missing on some or all exchanges
"""

import statistics
from typing import List, Dict, Optional, Tuple
from koalafolio.web import ccxt_public
import koalafolio.PcpCore.core as core
import koalafolio.PcpCore.settings as settings
import koalafolio.PcpCore.logger as logger

localLogger = logger.globalLogger


class MultiExchangePriceProvider:
	"""Aggregates prices from multiple exchanges with outlier detection."""

	def __init__(self, exchange_names: List[str] = None):

		self.providers: Dict[str, ccxt_public.CCXTPublic] = {}
		self._init_providers()

	def _init_providers(self):
		"""Initialize CCXT providers for each exchange."""
		# use exchanges from settings if available
		if settings.mySettings.ccxtExchanges():
			self.exchange_names = settings.mySettings.ccxtExchanges()
		else:
			localLogger.warning("No exchanges configured for CCXT price aggregation. Using default exchanges.")
			self.exchange_names = ["mexc", "gate"]
		for exchange_name in self.exchange_names:
			try:
				if exchange_name in self.providers:
					continue
				self.providers[exchange_name] = ccxt_public.CCXTPublic(exchange_name)
				localLogger.info(f"initialized price provider for {exchange_name}")
			except Exception as e:
				localLogger.warning(f"failed to initialize price provider for {exchange_name}: {e}")
		for exchange_name in list(self.providers.keys()):
			if exchange_name not in self.exchange_names:
				del self.providers[exchange_name]
				localLogger.info(f"removed price provider for {exchange_name} (not in configured exchanges)")

	def _detect_outliers(self, values: List[float]) -> Tuple[List[float], List[float]]:
		"""Detect outliers using interquartile range (IQR) method.
		
		Returns (valid_values, outlier_values).
		"""
		if len(values) <= 1:
			return values, []

		sorted_vals = sorted(values)
		n = len(sorted_vals)

		# Calculate quartiles
		q1_idx = n // 4
		q3_idx = (3 * n) // 4

		q1 = sorted_vals[q1_idx]
		q3 = sorted_vals[q3_idx]
		iqr = q3 - q1

		# Calculate outlier bounds
		lower_bound = q1 - 1.5 * iqr
		upper_bound = q3 + 1.5 * iqr

		valid = [v for v in values if lower_bound <= v <= upper_bound]
		outliers = [v for v in values if v < lower_bound or v > upper_bound]

		return valid, outliers

	def get_coin_prices(self, coins: List[str]) -> Dict[str, Dict[str, float]]:
		"""Get averaged coin prices from all exchanges.
		
		Returns structure: {coin: {currency: {PRICE: float, CHANGEPCT24HOUR: float}}}
		"""

		self._init_providers()  # Ensure providers are initialized

		result: Dict[str, Dict[str, float]] = {}
		display_currencies = settings.mySettings.displayCurrencies()

		for coin in coins:
			coin = coin.upper()

			# Fetch all available provider prices for this coin one time per exchange
			provider_prices: Dict[str, Dict[str, Dict[str, float]]] = {}
			for exchange_name, provider in self.providers.items():
				try:
					prices = provider.get_coin_prices([coin])
					if coin in prices:
						provider_prices[exchange_name] = prices[coin]
				except Exception as e:
					localLogger.debug(f"error fetching prices for {coin} from {exchange_name}: {e}")

			for currency in display_currencies:
				currency = currency.upper()

				# Collect prices from all exchanges for the requested currency
				exchange_prices: Dict[str, Optional[Tuple[float, Optional[float]]]] = {}
				for exchange_name, prices in provider_prices.items():
					if currency in prices:
						price_data = prices[currency]
						if isinstance(price_data, dict) and 'PRICE' in price_data:
							price = price_data['PRICE']
							change = price_data.get('CHANGEPCT24HOUR')
							exchange_prices[exchange_name] = (float(price), change)

				if not exchange_prices:
					# No prices found on any exchange
					continue

				# Extract price values for averaging
				price_values = [p[0] for p in exchange_prices.values()]

				# Detect outliers
				valid_prices, outliers = self._detect_outliers(price_values)

				if outliers:
					outlier_exchanges = [ex for ex, (p, _) in exchange_prices.items() if p in outliers]
					localLogger.warning(
						f"price outliers detected for {coin}/{currency}: "
						f"outlier values {outliers} from exchanges {outlier_exchanges} will be excluded"
					)

				if not valid_prices:
					# All prices were outliers or no valid prices
					localLogger.warning(f"no valid prices for {coin}/{currency} after outlier removal")
					continue

				# Calculate average price
				avg_price = statistics.mean(valid_prices)

				# Use change from first valid exchange
				change = None
				for exchange_name, (price, ch) in exchange_prices.items():
					if price in valid_prices:
						change = ch
						break

				result[coin] = {}
				result[coin][currency] = {'PRICE': float(avg_price), 'CHANGEPCT24HOUR': float(change)}

		return result

	def get_historical_price(self, trade: core.Trade) -> Dict[str, float]:
		"""Get averaged historical price for a trade.
		
		Returns structure: {currency: price}
		"""

		self._init_providers()  # Ensure providers are initialized

		result: Dict[str, float] = {}
		display_currencies = settings.mySettings.displayCurrencies()

		# Fetch all available historical prices for this trade once per exchange
		provider_hist_prices: Dict[str, Dict[str, float]] = {}
		for exchange_name, provider in self.providers.items():
			try:
				hist_prices = provider.get_historical_price(trade)
				if hist_prices:
					provider_hist_prices[exchange_name] = hist_prices
			except Exception as e:
				localLogger.debug(
					f"error fetching historical prices for {trade.coin} from {exchange_name}: {e}"
				)

		for currency in display_currencies:
			currency = currency.upper()

			# Collect historical prices from all exchanges for the requested currency
			exchange_prices: Dict[str, Optional[float]] = {}
			for exchange_name, hist_prices in provider_hist_prices.items():
				if currency in hist_prices:
					exchange_prices[exchange_name] = float(hist_prices[currency])

			if not exchange_prices:
				# No prices found on any exchange
				continue

			# Extract price values
			price_values = list(exchange_prices.values())

			# Detect outliers
			valid_prices, outliers = self._detect_outliers(price_values)

			if outliers:
				outlier_exchanges = [ex for ex, p in exchange_prices.items() if p in outliers]
				localLogger.warning(
					f"historical price outliers for {trade.coin}/{currency} at {trade.date}: "
					f"outlier values {outliers} from exchanges {outlier_exchanges} will be excluded"
				)

			if not valid_prices:
				# All prices were outliers
				localLogger.warning(
					f"no valid historical prices for {trade.coin}/{currency} at {trade.date} after outlier removal"
				)
				continue

			# Calculate average price
			avg_price = statistics.mean(valid_prices)
			result[currency] = avg_price

		return result


# Module-level singleton using default exchanges
_DEFAULT = MultiExchangePriceProvider()


def getCoinPrices(coins: List[str]) -> Dict[str, Dict[str, float]]:
	"""Get aggregated coin prices from multiple exchanges."""
	return _DEFAULT.get_coin_prices(coins)


def getHistoricalPrice(trade: core.Trade) -> Dict[str, float]:
	"""Get aggregated historical price for a trade."""
	return _DEFAULT.get_historical_price(trade)
