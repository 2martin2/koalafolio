# -*- coding: utf-8 -*-
"""
Created on 29.11.2020

@author: Martin
"""

import pandas
import datetime
import ccxt
import time
from typing import List, Optional, Dict, Any, Set
import koalafolio.gui.QLogger as logger

localLogger = logger.globalLogger

exchangenames = [
    "binance",
    "bitmex",
    "coinbase",
    "coinbasepro",
    "gemini",
    "poloniex",
    "kraken"
]

# timestamp,  location,   pair,   trade_type, amount, rate,   fee,    fee_currency,   link
def tradesToDataframe(trades):
    trades = []
    for trade in trades:
        trade = {}
        trade['timestamp'] = datetime.datetime.fromtimestamp(trade.timestamp)
        trade['location'] = str(trade.location)
        trade['pair'] = str(trade.pair)
        trade['trade_type'] = str(trade.trade_type)
        trade['amount'] = float(trade.amount)
        trade['rate'] = float(trade.rate)
        trade['fee'] = float(trade.fee)
        trade['fee_currency'] = str(trade.fee_currency.symbol)
        trade['link'] = str(trade.link)
        trades.append(trade)
    return pandas.DataFrame(trades)

def getTradeHistoryCcxt(apiname, key, secret, start, end):
    # Handle different secret encoding requirements for different exchanges
    api_secret = secret
    if isinstance(secret, str) and apiname.lower() != 'binance':
        api_secret = secret.encode()
    
    api = ccxtExchange(apiname, api_key=key, api_secret=api_secret)
    iskeyValid, checkKeyMsg = api.validate_api_credentials()
    if iskeyValid:
        trades = api.query_trade_history(start_ts=start, end_ts=end)
        tradesDF = tradesToDataframe(trades)
        return tradesDF
    localLogger.warning("api key is invalid for " + str(api.__class__.__name__) + ": " + checkKeyMsg)
    return pandas.DataFrame()

# todo: implement ccxt api for all current exchanges:
# binance, bitmex, coinbase, coinbasepro, gemini, poloniex, kraken

class Trade:
    """Simple class to represent a trade in the format expected by tradesToDataframe"""
    def __init__(self, timestamp, location, pair, trade_type, amount, rate, fee, fee_currency, link=""):
        self.timestamp = timestamp
        self.location = location
        self.pair = pair
        self.trade_type = trade_type
        self.amount = amount
        self.rate = rate
        self.fee = fee
        self.fee_currency = type('obj', (object,), {'symbol': fee_currency})
        self.link = link

class ccxtExchange:
    """CCXT Exchange wrapper for koalafolio"""
    
    SUPPORTED_EXCHANGES = exchangenames
    
    def __init__(self, exchange_name, api_key=None, api_secret=None):
        """
        Initialize the CCXT exchange wrapper
        
        Args:
            exchange_name (str): Name of the exchange (must be one of the supported exchanges)
            api_key (str): API key for the exchange
            api_secret (str): API secret for the exchange
        """
        if exchange_name.lower() not in self.SUPPORTED_EXCHANGES:
            raise ValueError(f"Exchange {exchange_name} not supported. Supported exchanges: {', '.join(self.SUPPORTED_EXCHANGES)}")
        
        self.exchange_name = exchange_name.lower()
        self.api_key = api_key
        self.api_secret = api_secret
        
        # Initialize the CCXT exchange
        exchange_class = getattr(ccxt, self.exchange_name)
        self.exchange = exchange_class({
            'apiKey': self.api_key,
            'secret': self.api_secret,
            'enableRateLimit': True,  # Respect exchange rate limits
        })
    
    def validate_api_credentials(self):
        """
        Validate the API credentials by attempting to fetch account balance
        
        Returns:
            tuple: (is_valid, message) where is_valid is a boolean and message is a string
        """
        try:
            self.exchange.fetch_balance()
            return True, "API credentials are valid"
        except Exception as e:
            return False, str(e)
    
    def _is_symbol_required_for_trades(self):
        """
        Check if the exchange requires a symbol for fetching trades
        
        Returns:
            bool: True if symbol is required, False otherwise
        """
        try:
            # Check if the exchange has the features property
            if hasattr(self.exchange, 'describe') and callable(self.exchange.describe):
                description = self.exchange.describe()
                
                # Navigate through the features structure
                if 'features' in description:
                    features = description['features']
                    
                    # Check spot trading features
                    if 'spot' in features and features['spot'] is not None:
                        spot_features = features['spot']
                        
                        # Check fetchMyTrades feature
                        if 'fetchMyTrades' in spot_features and spot_features['fetchMyTrades'] is not None:
                            fetch_trades_features = spot_features['fetchMyTrades']
                            
                            # Check if symbolRequired is specified
                            if 'symbolRequired' in fetch_trades_features:
                                return fetch_trades_features['symbolRequired']
            
            # If we can't determine from features, use a conservative approach
            # Check if the exchange has implemented fetchMyTrades without a symbol
            try:
                # Try to call fetchMyTrades with no symbol and a small limit
                # This is just a test call to see if it works
                self.exchange.fetch_my_trades(symbol=None, limit=1)
                return False  # If it works, symbol is not required
            except Exception as e:
                error_msg = str(e).lower()
                # Check for common error messages indicating symbol is required
                if 'symbol' in error_msg and ('required' in error_msg or 'must be' in error_msg):
                    return True
            
            # Default to requiring symbol for safety
            return True
            
        except Exception as e:
            localLogger.warning(f"Error checking if symbol is required: {str(e)}")
            return True  # Default to requiring symbol for safety
    
    def _get_user_assets(self) -> Set[str]:
        """
        Get the assets that the user has traded with
        
        Returns:
            set: Set of asset symbols
        """
        user_assets = set()
        
        # Try to get deposit history
        try:
            deposits = self.exchange.fetch_deposits()
            for deposit in deposits:
                if 'currency' in deposit:
                    user_assets.add(deposit['currency'])
        except Exception as e:
            localLogger.warning(f"Could not fetch deposit history: {str(e)}")
        
        # Try to get withdrawal history
        try:
            withdrawals = self.exchange.fetch_withdrawals()
            for withdrawal in withdrawals:
                if 'currency' in withdrawal:
                    user_assets.add(withdrawal['currency'])
        except Exception as e:
            localLogger.warning(f"Could not fetch withdrawal history: {str(e)}")
            
        # checking current balances
        try:
            balances = self.exchange.fetch_balance()
            if balances and 'total' in balances:
                for currency, amount in balances['total'].items():
                    if amount > 0:
                        user_assets.add(currency)
        except Exception as e:
            localLogger.warning(f"Could not fetch balance: {str(e)}")
        
        # add common assets
        user_assets.update({'BTC', 'ETH', 'BNB', 'USD', 'EUR', 'USDT', 'USDC'})
        
        return user_assets
    
    def _get_symbols_to_check(self, user_assets: Set[str]) -> List[str]:
        """
        Get the symbols to check for trades based on user assets
        
        Args:
            user_assets: Set of asset symbols the user has
            
        Returns:
            list: List of symbol strings to check
        """
        symbols_to_check = []
        
        try:
            # Only check symbols that contain the user's assets
            for symbol in self.exchange.markets:
                try:
                    market = self.exchange.market(symbol)
                    base, quote = market['base'], market['quote']
                    if base in user_assets and quote in user_assets:
                        symbols_to_check.append(symbol)
                except Exception:
                    continue
                    
        except Exception as e:
            localLogger.warning(f"Error determining symbols: {str(e)}")
            # Fallback to a minimal set of common pairs
            common_pairs = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'ETH/BTC']
            for pair in common_pairs:
                if pair in self.exchange.markets:
                    symbols_to_check.append(pair)
        
        return symbols_to_check
    
    def _fetch_trades_for_symbol(self, symbol: str, since: Optional[int] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Fetch trades for a specific symbol with rate limiting and retry logic
        
        Args:
            symbol: Trading pair symbol
            since: Timestamp in milliseconds to fetch trades from
            limit: Maximum number of trades to fetch per request
            
        Returns:
            list: List of trade dictionaries
        """
        all_trades = []
        
        try:
            # Initial request
            params = {}
            symbol_trades = self.exchange.fetch_my_trades(symbol=symbol, since=since, limit=limit, params=params)
            
            if symbol_trades:
                all_trades.extend(symbol_trades)
                
                # Some exchanges support pagination
                if len(symbol_trades) == limit:
                    # Continue fetching if we got exactly 'limit' trades (likely more available)
                    last_trade = symbol_trades[-1]
                    
                    # Different exchanges have different pagination mechanisms
                    if self.exchange_name == 'binance':
                        # Binance uses fromId for pagination
                        while len(symbol_trades) == limit:
                            # Add delay between requests to avoid rate limits
                            time.sleep(0.3)
                            
                            # Get the ID of the last trade
                            last_id = last_trade['id']
                            params = {'fromId': last_id}
                            
                            try:
                                symbol_trades = self.exchange.fetch_my_trades(symbol=symbol, limit=limit, params=params)
                                if symbol_trades:
                                    all_trades.extend(symbol_trades)
                                    last_trade = symbol_trades[-1]
                                else:
                                    break
                            except Exception as e:
                                localLogger.warning(f"Error during pagination for {symbol}: {str(e)}")
                                break
                    else:
                        # For other exchanges, use timestamp-based pagination
                        while len(symbol_trades) == limit:
                            # Add delay between requests to avoid rate limits
                            if self.exchange_name in ['coinbase', 'coinbasepro', 'gemini']:
                                time.sleep(0.5)
                            else:
                                time.sleep(0.2)
                            
                            # Get the timestamp of the last trade + 1ms
                            next_since = last_trade['timestamp'] + 1
                            
                            try:
                                symbol_trades = self.exchange.fetch_my_trades(symbol=symbol, since=next_since, limit=limit)
                                if symbol_trades:
                                    all_trades.extend(symbol_trades)
                                    last_trade = symbol_trades[-1]
                                else:
                                    break
                            except Exception as e:
                                localLogger.warning(f"Error during pagination for {symbol}: {str(e)}")
                                break
            
            # Add delay between requests to avoid rate limits
            if self.exchange_name == 'binance':
                time.sleep(0.3)  # 300ms delay between requests for Binance
            elif self.exchange_name in ['coinbase', 'coinbasepro', 'gemini']:
                time.sleep(0.5)  # 500ms delay for these exchanges
            else:
                time.sleep(0.2)  # 200ms default delay for other exchanges
                
            return all_trades
            
        except Exception as e:
            if 'rate limit' in str(e).lower():
                localLogger.warning(f"Rate limit hit for {symbol}, waiting 30 seconds before continuing")
                time.sleep(30)  # Wait 30 seconds if we hit rate limit
                try:
                    # Try again after waiting
                    return self._fetch_trades_for_symbol(symbol, since, limit)
                except Exception as retry_e:
                    localLogger.warning(f"Error fetching trades for {symbol} after retry: {str(retry_e)}")
            else:
                localLogger.warning(f"Error fetching trades for {symbol}: {str(e)}")
            
            return all_trades
    
    def _convert_raw_trade_to_trade_object(self, raw_trade: Dict[str, Any]) -> Optional[Trade]:
        """
        Convert a raw trade dictionary from CCXT to a Trade object
        
        Args:
            raw_trade: Dictionary containing trade data from CCXT
            
        Returns:
            Trade: Trade object or None if conversion fails
        """
        try:
            # Extract trade information
            timestamp = raw_trade['timestamp'] / 1000  # Convert from ms to seconds
            location = self.exchange_name
            pair = raw_trade['symbol']
            
            # Determine trade type (buy/sell)
            trade_type = raw_trade['side']
            
            # Extract amount and rate
            amount = raw_trade['amount']
            rate = raw_trade['price']
            
            # Extract fee information
            fee = 0
            fee_currency = ''
            
            if raw_trade['fee'] is not None:
                fee = raw_trade['fee'].get('cost', 0)
                fee_currency = raw_trade['fee'].get('currency', '')
            
            # Create link (trade ID or empty string)
            link = raw_trade.get('id', "")
            
            # Create Trade object
            return Trade(timestamp, location, pair, trade_type, amount, rate, fee, fee_currency, link)
            
        except Exception as e:
            localLogger.warning(f"Error processing trade: {str(e)}, trade data: {raw_trade}")
            return None
    
    def query_trade_history(self, start_ts=None, end_ts=None, limit_per_request=50):
        """
        Query trade history from the exchange with pagination
        
        Args:
            start_ts (int): Start timestamp in seconds since epoch
            end_ts (int): End timestamp in seconds since epoch
            limit_per_request (int): Maximum number of trades to fetch per request
            
        Returns:
            list: List of Trade objects
        """
        try:
            # Convert timestamps to milliseconds if provided
            since = int(start_ts * 1000) if start_ts else None
            
            # Fetch trades from the exchange
            raw_trades = []
            
            # Some exchanges require fetching trades by symbol
            if not self.exchange.has['fetchMyTrades']:
                localLogger.warning(f"Exchange {self.exchange_name} does not support fetching trades")
                return []
            
            # Get all markets first
            self.exchange.load_markets()
            
            # Check if symbol is required for fetching trades
            symbol_required = self._is_symbol_required_for_trades()
            localLogger.info(f"Symbol required for {self.exchange_name}: {symbol_required}")
            
            # For exchanges that don't require a symbol
            if not symbol_required:
                params = {}
                has_more = True
                current_since = since
                
                while has_more:
                    batch = self.exchange.fetch_my_trades(symbol=None, since=current_since, limit=limit_per_request, params=params)
                    if batch:
                        raw_trades.extend(batch)
                        
                        # If we got exactly the limit, there might be more
                        if len(batch) == limit_per_request:
                            # Update since for next request
                            current_since = batch[-1]['timestamp'] + 1
                        else:
                            has_more = False
                    else:
                        has_more = False
                        
                    # Add delay between requests
                    time.sleep(0.3)
                
                 # Kraken fetch_my_trades only returns trades since 2022, if start is before 2022 add warning for kraken
                if self.exchange_name == 'kraken' and start_ts and start_ts < 1640995200:  # Before 2022
                    localLogger.warning("Kraken Trade History older then 2022 not supported by Kraken API. Export history older then 2022 as .csv from Kraken Website")
  
                
            else:
                # For exchanges that require fetching trades by symbol
                # Get user assets to determine which symbols to check
                user_assets = self._get_user_assets()
                
                # Get symbols to check based on user assets
                localLogger.info(f"Only check symbols for user assets: {user_assets}")
                symbols_to_check = self._get_symbols_to_check(user_assets)
                
                # Fetch trades for each symbol with pagination
                localLogger.info(f"Number of symbols to check: {len(symbols_to_check)}")
                for symbol in symbols_to_check:
                    symbol_trades = self._fetch_trades_for_symbol(symbol, since, limit_per_request)
                    raw_trades.extend(symbol_trades)
            
            # Filter trades by end timestamp if provided
            if end_ts:
                raw_trades = [t for t in raw_trades if t['timestamp'] / 1000 <= end_ts]
            
            # Convert raw trades to Trade objects
            trades = []
            for raw_trade in raw_trades:
                trade = self._convert_raw_trade_to_trade_object(raw_trade)
                if trade:
                    trades.append(trade)
            
            localLogger.info(f"Found {len(trades)} trades for {self.exchange_name}")
            return trades
            
        except Exception as e:
            localLogger.error(f"Error querying trade history from {self.exchange_name}: {str(e)}")
            return []