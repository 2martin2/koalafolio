# -*- coding: utf-8 -*-
"""
Created on 31.03.2021

@author: Martin
"""

import argparse
import os


def parse_arguments():
    # create parser
    parser = argparse.ArgumentParser(prog="koalafolio",
                                     description=" visit https://github.com/2martin2/koalafolio for more information")
    # add arguments to the parser
    parser.add_argument('-d', '--datadir', type=dir_path, required=False,
                        help="directory where user data should be stored. make sure it is a valid and writable dir")
    parser.add_argument('-u', '--username', type=str, required=False,
                        help="username can be used to switch between different portfolios. " +
                             "username will be added to Datafolder (Data_username), " +
                             "so every user has its own settings, trades, styles and so on")
    # parse the arguments
    return parser.parse_args()


def dir_path(path):
    if os.path.isdir(path):
        return path
    else:
        raise argparse.ArgumentTypeError(f"{path} is not a valid path")
