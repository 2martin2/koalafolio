#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Tests for the multi-exchange price aggregation layer

This test exercises the price aggregation logic which queries multiple
exchanges and computes averaged prices with outlier detection.

The tests are best-effort and will be skipped if dependencies are missing
or exchanges are unreachable (no network).
"""

import unittest
import datetime

from koalafolio.web import ccxt_public


class TestCCXTPrices(unittest.TestCase):
    def setUp(self):

        try:
            import koalafolio.web.prices as prices_api
            self.prices_api = prices_api
        except Exception as e:
            self.prices_api = None
            self.skipTest(f"prices module not available: {e}")

        # sample coins to query
        self.coins = ['BTC', 'ETH', 'ADA', 'BNB', 'XMR', 'LINK', 'KCS', 'HOT', 'IOTA', 'USDT']
        # ensure pandas is available (core module depends on pandas)
        try:
            import pandas as pd  # noqa: F401
        except Exception as e:
            self.skipTest(f"pandas not available: {e}")

        # import core/settings after dependency checks
        import koalafolio.PcpCore.core as core
        import koalafolio.PcpCore.settings as settings
        self.core = core
        self.settings = settings
        # ensure settings are initialized (displayCurrencies etc.)
        try:
            self.settings.mySettings.initSettings()
        except Exception:
            pass

    def test_getCoinPrices_structure(self):
        """getCoinPrices should return a dict-of-dicts for requested coins"""
        prices = self.prices_api.getCoinPrices(self.coins)
        self.assertIsInstance(prices, dict)
        # ensure keys for coins exist (uppercased)
        for coin in self.coins:
            self.assertIn(coin.upper(), prices)
            self.assertIsInstance(prices[coin.upper()], dict)
            if prices[coin.upper()]:
                sample_currency = next(iter(prices[coin.upper()].keys()))
                self.assertIsInstance(prices[coin.upper()][sample_currency], dict)
                self.assertIn('PRICE', prices[coin.upper()][sample_currency])
                self.assertIn('CHANGEPCT24HOUR', prices[coin.upper()][sample_currency])

    def test_getHistoricalPrice_basic(self):
        """getHistoricalPrice should accept a Trade and return a dict (may be empty)"""
        t = self.core.Trade()
        t.date = datetime.datetime.now(tz=datetime.timezone.utc) - datetime.timedelta(days=1)
        t.coin = 'BTC'
        t.amount = 1

        hist = self.prices_api.getHistoricalPrice(t)
        self.assertIsInstance(hist, dict)
        # if prices returned, keys should be known display currencies
        if hist:
            disp = self.settings.mySettings.displayCurrencies()
            for k in hist:
                self.assertIn(k, disp)
                self.assertIsInstance(hist[k], float)

    def test_convert_price_to_display_stops_recursive_cycles(self):
        """Currency conversions should not recurse forever through stable pairs."""
        provider = object.__new__(ccxt_public.CCXTPublic)
        provider._get_ticker_data = lambda symbol: (1.0, None)
        provider._symbol_exists = lambda symbol: symbol in {
            'USDT/USDC',
            'USDC/USDT',
        }

        result = provider._convert_price_to_display(1.0, 'USDT', 'USD')
        self.assertEqual(result, (None, None))

    def test_parse_numeric_handles_percent_strings(self):
        """Percent strings should be parsed into floats without raising."""
        provider = ccxt_public.CCXTPublic.__new__(ccxt_public.CCXTPublic)
        self.assertEqual(provider._parse_numeric('1.27%'), 1.27)
        self.assertEqual(provider._parse_numeric('−2,50%'), -2.5)
        self.assertIsNone(provider._parse_numeric('n/a'))


if __name__ == '__main__':
    unittest.main()
