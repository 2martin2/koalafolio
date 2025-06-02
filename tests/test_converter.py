# -*- coding: utf-8 -*-
"""
Test script for converter functions in koalafolio/Import/Converter.py
Tests all modelCallback functions with example trade data
"""

import os
import pandas as pd
import json
import datetime
import unittest
from pathlib import Path
import koalafolio.Import.Models as models
import koalafolio.PcpCore.core as core
import koalafolio.PcpCore.settings as settings

# Add parent directory to path to import koalafolio modules
project_root = Path(__file__).parents[1]
test_root = Path(__file__).parents[2] / "koalafolio_testdata"
testdata_path = test_root / Path(__file__).stem


class ConverterTestResult :
    def __init__(self, model_name, file_name, success, trades_count=0, fees_count=0, skipped_rows=0, trade_list=None, fee_list=None, error=None):
        self.model_name = model_name
        self.file_name = file_name
        self.success = success
        self.trades_count = trades_count
        self.fees_count = fees_count
        self.skipped_rows = skipped_rows
        self.error = error
        self.timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.trade_list = trade_list
        self.fee_list = fee_list
    
    def to_dict(self):
        return {
            "model_name": self.model_name,
            "file_name": self.file_name,
            "success": self.success,
            "trades_count": self.trades_count,
            "fees_count": self.fees_count,
            "skipped_rows": self.skipped_rows,
            "error": str(self.error) if self.error else None,
            "timestamp": self.timestamp
            # skip trade_list and fee_list in dict creation
        }

class TestConverter(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures before running tests."""
        cls.start_time = datetime.datetime.now()
        cls.test_data_dir = testdata_path
        # Check if test data directory exists
        if not os.path.exists(cls.test_data_dir):
            raise unittest.SkipTest(f"Test data directory not found: {cls.test_data_dir}")
        cls.test_data_out_dir = testdata_path / f"out_{cls.start_time.strftime('%Y%m%d_%H%M%S')}"
        # create out dir if it does not exist
        if not os.path.exists(cls.test_data_out_dir):
            os.makedirs(cls.test_data_out_dir)
        cls.test_spec_file = "testspec.txt"
        cls.output_file = cls.test_data_out_dir / \
                          f"test_converter_results_{cls.start_time.strftime('%Y%m%d_%H%M%S')}.json"
        cls.results = []
        cls.settings = settings.mySettings.setPath(test_root)

    def get_test_files(self):
        """Get list of files to test."""
        if os.path.exists(os.path.join(self.test_data_dir, self.test_spec_file)):
            with open(os.path.join(self.test_data_dir, self.test_spec_file), 'r') as f:
                # return all files from test_spec_file if not commented out
                return [line.strip() for line in f if line.strip() and not line.startswith('#')]
        # return all files in the test_data_dir
        return [f for f in os.listdir(self.test_data_dir) if os.path.isfile(os.path.join(self.test_data_dir, f)) and not f.startswith('.')]

    def runTest(self):
        """Test all converters with test data files."""
        for file_name in self.get_test_files():
            file_path = os.path.join(self.test_data_dir, file_name)
            if not os.path.exists(file_path):
                print(f"TEST test_converter: File not found: {file_path}")
                continue
            
            try:
                df = pd.read_csv(file_path)
                matchcnt = 0
                for model in models.IMPORT_MODEL_LIST:
                    try:
                        if model.isMatch(df.columns.tolist()):
                            try:
                                trade_list, fee_list, skipped_rows = model.convertDataFrame(df)

                                if len(trade_list) > 0 or len(fee_list) > 0:
                                    matchcnt += 1
                                    self.results.append(ConverterTestResult (
                                        model_name=model.modelName or model.modelCallback.__name__,
                                        file_name=file_name,
                                        success=True,
                                        trades_count=len(trade_list),
                                        fees_count=len(fee_list),
                                        skipped_rows=skipped_rows,
                                        trade_list=trade_list,
                                        fee_list=fee_list
                                    ))
                                    print(
                                        f"TEST test_converter: Success: {file_name} with {model.modelCallback.__name__}")
                                    print(
                                        f"TEST test_converter:   Trades: {len(trade_list)}, Fees: {len(fee_list)}, Skipped: {skipped_rows}")
                                else:
                                    self.results.append(ConverterTestResult (
                                        model_name=model.modelName or model.modelCallback.__name__,
                                        file_name=file_name,
                                        success=True,
                                        trades_count=0,
                                        fees_count=0,
                                        skipped_rows=skipped_rows,
                                        error="No trades or fees found"
                                    ))
                                    print(
                                        f"TEST test_converter: Info: {file_name} matched with {model.modelCallback.__name__} but no trades or fees found")
                                    print(
                                        f"TEST test_converter:   Trades: {len(trade_list)}, Fees: {len(fee_list)}, Skipped: {skipped_rows}")

                                # Add assertions to verify the conversion results
                                self.assertIsInstance(trade_list, core.TradeList)
                                self.assertIsInstance(fee_list, core.TradeList)
                                self.assertIsInstance(skipped_rows, int)
                                
                            except Exception as e:
                                self.results.append(ConverterTestResult (
                                    model_name=model.modelName or model.modelCallback.__name__,
                                    file_name=file_name,
                                    success=False,
                                    error=e
                                ))
                                print(f"TEST test_converter: Conversion error: {file_name} with {model.modelCallback.__name__}: {str(e)}")
                    except Exception as e:
                        self.results.append(ConverterTestResult (
                            model_name=model.modelName or model.modelCallback.__name__,
                            file_name=file_name,
                            success=False,
                            error=e
                        ))
                        print(f"TEST test_converter: Matching error: {file_name} with {model.modelCallback.__name__}: {str(e)}")
                if matchcnt == 0:
                    self.results.append(ConverterTestResult (
                        model_name="file_reading",
                        file_name=file_name,
                        success=False,
                        error="No matching model found"
                    ))
                    print(f"TEST test_converter: Matching error: {file_name} was not matched by any model")
                if matchcnt > 1:
                    fileresults = [result for result in self.results if result.file_name == file_name]
                    # check if any fileresult has different amount of trades, fees or skippedrows
                    if len(set([result.trades_count for result in fileresults])) > 1 or \
                            len(set([result.fees_count for result in fileresults])) > 1 or \
                            len(set([result.skipped_rows for result in fileresults])) > 1:
                        self.results.append(ConverterTestResult (
                            model_name="file_reading",
                            file_name=file_name,
                            success=False,
                            error="Multiple matching models found with different results"
                        ))
                        print(f"TEST test_converter: Matching error: {file_name} has multiple matching models with different results")
                    else:
                        self.results.append(ConverterTestResult (
                            model_name="file_reading",
                            file_name=file_name,
                            success=True,
                            error="Multiple matching models found with equal output"
                        ))
                        print(f"TEST test_converter: Warning: {file_name} has multiple matching with equal results")
            except Exception as e:
                self.results.append(ConverterTestResult (
                    model_name="file_reading",
                    file_name=file_name,
                    success=False,
                    error=e
                ))
                print(f"TEST test_converter: File reading error: {file_path}: {str(e)}")
        
        # Write results to file
        self.write_results()
        
        # Verify that we have some successful tests
        success_count = sum(1 for r in self.results if r.success)
        total_count = len(self.results)
        print(f"TEST test_converter: Summary: {success_count}/{total_count} tests passed")
        self.assertGreater(success_count, 0, "No successful conversions")

    def write_results(self):
        """Write test results to a JSON file."""
        results_dict = [result.to_dict() for result in self.results]
        
        grouped_results = {}
        for result in results_dict:
            file_name = result["file_name"]
            if file_name not in grouped_results:
                grouped_results[file_name] = []
            grouped_results[file_name].append(result)
        
        with open(self.output_file, 'w') as f:
            json.dump(grouped_results, f, indent=2)

        for result in self.results:
            if result.success:
                trade_list, fee_list = result.trade_list, result.fee_list
                if trade_list:
                    tradeFile = self.test_data_out_dir / f"{result.file_name.split('.')[0]}_{result.model_name}_trades.txt"
                    trade_list.toCsv(tradeFile)
                if fee_list:
                    feeFile = self.test_data_out_dir / f"{result.file_name.split('.')[0]}_{result.model_name}_fees.txt"
                    fee_list.toCsv(feeFile)

        
        print(f"TEST test_converter: Test results written to {self.output_file}")

if __name__ == "__main__":
    # run test with unittest
    unittest.main()