#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test script for exchange API functions in koalafolio/web/exchanges.py
Tests all getTradeHistory functions with API keys from a text file
"""

import os
import time
import datetime
import pandas as pd
import ast
from typing import Dict
import unittest
from pathlib import Path
from koalafolio.web.exchanges import ExchangesStatic

# Add parent directory to path to import koalafolio modules
project_root = Path(__file__).parents[1]
test_root = Path(__file__).parents[2] / "koalafolio_testdata"
testdata_path = test_root / Path(__file__).stem


class TestExchanges(unittest.TestCase):
    """Test class for exchange API functions"""

    def setUp(self):
        """Set up test environment"""
        self.test_start_time = datetime.datetime.now()
        self.test_data_dir = testdata_path
        # Check if test data directory exists
        if not os.path.exists(self.test_data_dir):
            raise unittest.SkipTest(f"Test data directory not found: {self.test_data_dir}")
        self.test_data_out_dir = testdata_path / f"out_{self.test_start_time.strftime('%Y%m%d_%H%M%S')}"
        # create out dir if it does not exist
        if not os.path.exists(self.test_data_out_dir):
            os.makedirs(self.test_data_out_dir)
        self.output_file = self.test_data_out_dir / \
                           f"test_exchanges_results_{self.test_start_time.strftime('%Y%m%d_%H%M%S')}.json"

        # Calculate timestamps for 5 year span
        now = self.test_start_time
        some_years_ago = now - datetime.timedelta(days=5*365)
        
        self.end_ts = int(time.mktime(now.timetuple()))
        self.start_ts = int(time.mktime(some_years_ago.timetuple()))

        self.load_api_keys(self.test_data_dir /"input.csv")

        # self.settings = settings.mySettings.setPath(test_root)

    def load_api_keys(self, file_path: str) -> Dict[str, Dict[str, str]]:
        """Load API keys from text file
        
        Args:
            file_path: Path to text file with API keys
            
        """
        # Dictionary to store API keys
        self.api_keys = {}
        try:
            with open(file_path, 'r') as f:
                content = f.read()
                self.api_keys = ast.literal_eval(content)
            
            print(f"TEST test_exchanges: Loaded {len(self.api_keys)} API keys from {file_path}")
        except Exception as e:
            print(f"TEST test_exchanges: Error loading API keys: {e}")
    
    def save_trades_to_csv(self, exchange_name: str, trades_df: pd.DataFrame):
        """Save trades to CSV file
        
        Args:
            exchange_name: Name of the exchange
            trades_df: DataFrame with trades
        """
        if not trades_df.empty:
            filename = f"{exchange_name}_ccxt_trades.txt"
            
            trades_df.to_csv(self.test_data_out_dir / filename, index=False)
            print(f"TEST test_exchanges: Saved {len(trades_df)} trades to {self.test_data_out_dir / filename}")
            
    def runTest(self):
        """Run all tests"""
        for apiname in self.api_keys:
            api_data = self.api_keys[apiname]
            key = api_data['apikey']
            secret = api_data['secret']
            print(f"TEST test_exchanges: Testing {apiname} API...")
            try:
                # log time needed for getTradeHistoryCall
                start_time = time.time()
                result = ExchangesStatic.getTradeHistoryCcxt(apiname, key, secret, self.start_ts, self.end_ts)
                end_time = time.time()
                print(f"TEST test_exchanges: {apiname} API test successful. Got {len(result)} trades.")
                self.save_trades_to_csv(apiname, result)
                print(f"TEST test_exchanges: {apiname} API test took {end_time - start_time:.2f} seconds")
                self.assertIsInstance(result, pd.DataFrame)
            except Exception as e:
                print(f"TEST test_exchanges: {apiname} API test failed: {e}")
                # mark test as failed
                self.assertTrue(False)




if __name__ == "__main__":
    # run test with test data
    unittest.main()
