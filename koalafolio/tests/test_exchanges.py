#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test script for exchange API functions in koalafolio/web/exchanges.py
Tests all getTradeHistory functions with API keys from a text file
"""

import os
import sys
import time
import datetime
import pandas as pd
import ast
from typing import Dict
import unittest


# Add parent directory to path to import koalafolio modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from koalafolio.web import exchanges


class TestExchanges(unittest.TestCase):
    """Test class for exchange API functions"""

    def setUp(self):
        """Set up test environment"""
        # Calculate timestamps for one year ago until today
        now = datetime.datetime.now()
        one_year_ago = now - datetime.timedelta(days=5*365)
        
        self.end_ts = int(time.mktime(now.timetuple()))
        self.start_ts = int(time.mktime(one_year_ago.timetuple()))
        
        # Create output directory for CSV files
        self.output_dir = os.path.dirname(os.path.abspath(__file__))

        file_path = "D:\git\koalafolio_testdata\exchanges.csv"
        self.load_api_keys(file_path)

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
            
            print(f"Loaded {len(self.api_keys)} API keys from {file_path}")
        except Exception as e:
            print(f"Error loading API keys: {e}")
    
    def save_trades_to_csv(self, exchange_name: str, trades_df: pd.DataFrame):
        """Save trades to CSV file
        
        Args:
            exchange_name: Name of the exchange
            trades_df: DataFrame with trades
        """
        if not trades_df.empty:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{exchange_name}_trades_{timestamp}.csv"
            filepath = os.path.join(self.output_dir, filename)
            
            trades_df.to_csv(filepath, index=False)
            print(f"Saved {len(trades_df)} trades to {filepath}")
            
    def runTest(self):
        """Run all tests"""
        for apiname in self.api_keys:
            api_data = self.api_keys[apiname]
            key = api_data['apikey']
            secret = api_data['secret']
            print(f"Testing {apiname} API...")
            try:
                result = exchanges.getTradeHistoryCcxt(apiname, key, secret, self.start_ts, self.end_ts)
                self.assertIsInstance(result, pd.DataFrame)
                print(f"{apiname} API test successful. Got {len(result)} trades.")
                self.save_trades_to_csv(apiname, result)
            except Exception as e:
                print(f"{apiname} API test failed: {e}")


def run_tests(file_path: str):
    """Run all tests with API keys from text file
    
    Args:
        file_path: Path to text file with Test API keys
    """
    # Create test suite
    suite = unittest.TestSuite()
    test = TestExchanges()
    
    # Load API keys
    test.load_api_keys(file_path)
    
    # Add test methods
    suite.addTest(test)
    
    # Run tests
    unittest.TextTestRunner().run(suite)


if __name__ == "__main__":
    # run test with test data
    run_tests()