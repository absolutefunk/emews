"""
Runs all tests.

Created on October 17, 2018
@author: Brian Ricks
"""

import unittest

# test modules
import emews.base.tests.test_config
import emews.base.tests.test_system_init


def main():
    """
    Load and run all tests.

    The ordering here is not too important.
    """
    test_suites = []
    test_suites.append(unittest.TestLoader().loadTestsFromModule(emews.base.tests.test_system_init))
    test_suites.append(unittest.TestLoader().loadTestsFromModule(emews.base.tests.test_config))
